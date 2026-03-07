"""WoW AI Companion – MCP Server (FastAPI).

Provides REST + WebSocket endpoints for tip generation, combat event
ingestion, and real-time Second-Screen dashboard streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time as _time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

from llm import get_provider
from llm.base import LLMProvider
from analysis import FightAnalyzer

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("mcp")

# ── Singletons (created at startup) ─────────────────────────────────────
_provider: LLMProvider | None = None
_analyzer: FightAnalyzer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Initialize shared resources on startup."""
    global _provider, _analyzer
    _provider = get_provider()
    _analyzer = FightAnalyzer(_provider)
    log.info("MCP server ready – LLM provider: %s", _provider.name)
    yield


app = FastAPI(title="WoW AI Companion MCP", lifespan=lifespan)

# Allow Second-Screen WebUI (localhost:3000) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket Connection Manager ────────────────────────────────────────


class ConnectionManager:
    """Manages WebSocket connections grouped by channel."""

    def __init__(self) -> None:
        self._channels: dict[str, list[WebSocket]] = {}

    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        self._channels.setdefault(channel, []).append(ws)
        log.info("WS connect: channel=%s, total=%d", channel, len(self._channels[channel]))

    def disconnect(self, channel: str, ws: WebSocket) -> None:
        conns = self._channels.get(channel, [])
        if ws in conns:
            conns.remove(ws)
        log.info("WS disconnect: channel=%s, remaining=%d", channel, len(conns))

    async def broadcast(self, channel: str, data: dict) -> None:
        """Send JSON data to all clients on a channel."""
        dead: list[WebSocket] = []
        for ws in self._channels.get(channel, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(channel, ws)

    def client_count(self, channel: str) -> int:
        return len(self._channels.get(channel, []))


ws_manager = ConnectionManager()


# ── Prompt templates ────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a precise WoW coach. "
    "Return only bullet-point tips. Never suggest automation."
)

POST_PROMPT = """Return EXACTLY {n} bullet tips (<=160 chars each) \
in the player's locale (field 'locale').
Focus on exploration, missed turn-ins, quest items, rares, points of interest.
DATA:
```json
{data}
```"""


# ── Helpers ─────────────────────────────────────────────────────────────


def to_bullets(text: str, n: int) -> list[str]:
    """Parse LLM output into a list of tip strings."""
    tips: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] in "-•*":
            s = s.lstrip("-•* ").strip()
            if s:
                tips.append(s)
    if not tips:
        for line in text.splitlines():
            m = re.match(r"^\s*\d+\.\s*(.+)$", line.strip())
            if m:
                tips.append(m.group(1).strip())
    return tips[:n] if tips else []


# ── Pydantic models ────────────────────────────────────────────────────


class Session(BaseModel):
    ts: int | None = None
    player: str | None = None
    class_: str | None = Field(None, alias="class")
    specId: int | None = None
    zone: str | None = None
    fights: list[dict[str, Any]] | None = None
    locale: str | None = "deDE"
    # Midnight-safe fields (optional for backward compat)
    level: int | None = None
    ilvl: float | None = None
    activeQuests: list[dict[str, Any]] | None = None
    professions: list[dict[str, Any]] | None = None
    mapId: int | None = None


class GenReq(BaseModel):
    session: Session
    tips: int = 5


class GenResp(BaseModel):
    tips: list[str]


class CombatEventIn(BaseModel):
    ts: float
    raw: str


# ── In-memory event buffer ──────────────────────────────────────────────
LIVE_EVENTS: list[CombatEventIn] = []
MAX_EVENTS = 1000


# ── Routes ──────────────────────────────────────────────────────────────


@app.get("/")
def root():
    endpoints = sorted(
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path != "/"
    )
    return {
        "status": "ok",
        "service": "wow-ai-mcp",
        "llm_provider": _provider.name if _provider else "not initialized",
        "endpoints": endpoints,
    }


@app.get("/tools/ping")
def ping():
    return {"pong": True}


@app.get("/healthz")
async def health():
    llm_ok = await _provider.health() if _provider else False
    return {"ok": True, "llm_reachable": llm_ok}


@app.post("/tools/generate_tips", response_model=GenResp)
async def generate_tips(req: GenReq):
    assert _provider is not None, "LLM provider not initialized"

    loc = req.session.locale or "deDE"
    data = req.session.model_dump(by_alias=True, exclude_none=True)
    data["locale"] = loc
    prompt = POST_PROMPT.format(
        n=req.tips, data=json.dumps(data, ensure_ascii=False)
    )

    out = await _provider.generate(prompt, system=SYSTEM_PROMPT)
    tips = to_bullets(out, req.tips) or ["Keine Tipps erzeugt."]
    return GenResp(tips=tips)


class StructuredCombatEvent(BaseModel):
    """Structured combat event from enhanced watcher parser."""

    ts: float
    subevent: str
    sourceName: str = ""
    destName: str = ""
    spellId: int | None = None
    spellName: str | None = None
    amount: int | None = None
    extra: dict[str, Any] = {}


class FightSummaryIn(BaseModel):
    """Fight summary pushed by the watcher after encounter end."""

    encounterId: int | None = None
    encounterName: str | None = None
    start: float = 0.0
    end: float = 0.0
    durationSec: float = 0.0
    result: str = "unknown"
    totalDamage: int = 0
    totalHealing: int = 0
    players: dict[str, Any] = {}


class SessionUpdate(BaseModel):
    """Session data pushed by watcher when SavedVariables change."""

    session: dict[str, Any]


# ── In-memory state ─────────────────────────────────────────────────────
_current_session: dict[str, Any] = {}
_fight_history: list[dict[str, Any]] = []
MAX_FIGHT_HISTORY = 50


@app.post("/tools/ingest_combat_event")
async def ingest(ev: CombatEventIn):
    """Ingest raw combat log line (backward compat)."""
    LIVE_EVENTS.append(ev)
    if len(LIVE_EVENTS) > MAX_EVENTS:
        del LIVE_EVENTS[: len(LIVE_EVENTS) - MAX_EVENTS]
    return {"ok": True}


@app.post("/api/combat-event")
async def ingest_structured(ev: StructuredCombatEvent):
    """Ingest structured combat event and broadcast to WebSocket clients."""
    payload = {"type": "combat_event", "data": ev.model_dump()}
    await ws_manager.broadcast("combat", payload)
    await ws_manager.broadcast("dashboard", payload)
    return {"ok": True}


@app.post("/api/fight-summary")
async def push_fight_summary(summary: FightSummaryIn):
    """Receive a completed fight summary from the watcher."""
    data = summary.model_dump()
    _fight_history.append(data)
    if len(_fight_history) > MAX_FIGHT_HISTORY:
        del _fight_history[: len(_fight_history) - MAX_FIGHT_HISTORY]

    await ws_manager.broadcast("dashboard", {"type": "fight_end", "data": data})
    return {"ok": True}


@app.post("/api/session")
async def push_session(update: SessionUpdate):
    """Receive updated session data from watcher."""
    global _current_session
    _current_session = update.session
    await ws_manager.broadcast("dashboard", {"type": "session_update", "data": update.session})
    return {"ok": True}


@app.get("/api/session")
def get_session():
    """Return current session data."""
    return _current_session or {}


@app.get("/api/history")
def get_history(limit: int = 20):
    """Return recent fight summaries."""
    return _fight_history[-limit:]


@app.get("/tools/live_events")
def live_events(limit: int = 100):
    return [e.model_dump() for e in LIVE_EVENTS[-limit:]]


# ── Fight Analysis (Kampf-Coach) ────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request to analyze a specific fight."""

    fight: dict[str, Any]
    playerGuid: str | None = None
    playerClass: str = ""
    locale: str = "deDE"


@app.post("/api/analyze-fight")
async def analyze_fight(req: AnalyzeRequest):
    """Analyze a completed fight and return coaching feedback."""
    assert _analyzer is not None, "Fight analyzer not initialized"

    result = await _analyzer.analyze(
        fight=req.fight,
        player_guid=req.playerGuid,
        player_class=req.playerClass,
        locale=req.locale,
    )
    return result.to_dict()


@app.post("/api/analyze-latest")
async def analyze_latest():
    """Analyze the most recent fight in history."""
    assert _analyzer is not None, "Fight analyzer not initialized"

    if not _fight_history:
        return {"error": "No fights in history yet."}

    fight = _fight_history[-1]
    player_class = _current_session.get("class", "")
    locale = _current_session.get("locale", "deDE")

    result = await _analyzer.analyze(
        fight=fight,
        player_class=player_class,
        locale=locale,
    )

    # Broadcast analysis to dashboard
    analysis_data = result.to_dict()
    analysis_data["fight"] = fight
    await ws_manager.broadcast("dashboard", {"type": "fight_analysis", "data": analysis_data})

    return analysis_data


# ── WebSocket endpoints ─────────────────────────────────────────────────


@app.websocket("/ws/combat")
async def ws_combat(websocket: WebSocket):
    """Stream raw combat events to connected clients."""
    await ws_manager.connect("combat", websocket)
    try:
        while True:
            # Keep connection alive, receive pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "ts": _time.time()})
    except WebSocketDisconnect:
        ws_manager.disconnect("combat", websocket)


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """Full dashboard stream: combat events + fight summaries + session updates."""
    await ws_manager.connect("dashboard", websocket)
    try:
        # Send initial state on connect
        await websocket.send_json({
            "type": "init",
            "data": {
                "session": _current_session,
                "recentFights": _fight_history[-5:],
                "wsClients": ws_manager.client_count("dashboard"),
            },
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "ts": _time.time()})
    except WebSocketDisconnect:
        ws_manager.disconnect("dashboard", websocket)
