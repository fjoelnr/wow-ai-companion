from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os, json, requests, re

app = FastAPI(title="WoW AI Companion MCP")

MODE = os.getenv("LLM_MODE", "local")  # local|api
OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
FALLBACK = os.getenv("OLLAMA_FALLBACK_MODEL", "mistral-nemo")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

POST_PROMPT = """You are a concise WoW exploration, quest and profession coach.
Return EXACTLY {n} bullet tips (<=160 chars) in the player's locale (field 'locale').
Focus on quests, missed turn-ins, profession next steps, useful zone goals, rares and points of interest.
Never suggest automation; textual tips only.
DATA:
```json
{data}
```"""

def llm_local(prompt: str) -> str:
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=60)
    if r.ok:
        return r.json().get("response", "")
    if FALLBACK:
        r2 = requests.post(f"{OLLAMA}/api/generate",
                           json={"model": FALLBACK, "prompt": prompt, "stream": False}, timeout=60)
        r2.raise_for_status()
        return r2.json().get("response", "")
    r.raise_for_status()

def llm_api(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {"model": OPENAI_MODEL, "messages":[
        {"role":"system","content":"You are a precise WoW coach. Only bullet tips."},
        {"role":"user","content": prompt}],
        "temperature":0.2}
    r = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def to_bullets(text: str, n: int) -> List[str]:
    tips = []
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

class Session(BaseModel):
    ts: Optional[int] = None
    player: Optional[str] = None
    realm: Optional[str] = None
    characterKey: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    specId: Optional[int] = None
    level: Optional[int] = None
    ilvl: Optional[float] = None
    mapId: Optional[int] = None
    zone: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    activeQuests: Optional[List[Dict[str, Any]]] = None
    professions: Optional[List[Dict[str, Any]]] = None
    gold: Optional[int] = None
    fights: Optional[List[Dict[str, Any]]] = None
    locale: Optional[str] = "deDE"

class GenReq(BaseModel):
    session: Session
    tips: int = 5

class GenResp(BaseModel):
    tips: List[str]

class CombatEvent(BaseModel):
    ts: float
    raw: str

LIVE_EVENTS: List[CombatEvent] = []
LATEST_SESSION: Dict[str, Any] = {}
SESSIONS_BY_CHARACTER: Dict[str, Dict[str, Any]] = {}


class SessionEnvelope(BaseModel):
    session: Session

@app.get("/")
def root():
    endpoints = sorted([
        route.path for route in app.routes
        if isinstance(route, APIRoute) and route.path != "/"
    ])
    return {
        "status": "ok",
        "service": "wow-ai-mcp",
        "endpoints": endpoints,
    }

@app.get("/tools/ping")
def ping():
    return {"pong": True}

@app.get("/healthz")
def health():
    return {"ok": True}


@app.post("/api/session")
def ingest_session(req: SessionEnvelope):
    data = req.session.dict(by_alias=True)
    character_key = data.get("characterKey") or _character_key(data)
    if character_key:
        data["characterKey"] = character_key
        SESSIONS_BY_CHARACTER[character_key] = data

    global LATEST_SESSION
    LATEST_SESSION = data
    return {"ok": True, "characterKey": character_key}


@app.get("/api/session")
def get_session(character_key: str | None = None):
    if character_key:
        return SESSIONS_BY_CHARACTER.get(character_key, {})
    return LATEST_SESSION


@app.get("/api/characters")
def list_characters():
    characters = []
    for key, session in sorted(
        SESSIONS_BY_CHARACTER.items(),
        key=lambda item: item[1].get("ts") or 0,
        reverse=True,
    ):
      characters.append({
          "characterKey": key,
          "player": session.get("player"),
          "realm": session.get("realm"),
          "class": session.get("class"),
          "level": session.get("level"),
          "ilvl": session.get("ilvl"),
          "zone": session.get("zone"),
          "ts": session.get("ts"),
      })
    return characters

@app.post("/tools/generate_tips", response_model=GenResp)
def generate_tips(req: GenReq):
    loc = req.session.locale or "deDE"
    data = req.session.dict(by_alias=True)
    data["characterKey"] = data.get("characterKey") or _character_key(data)
    merged = {**(data or {}), "locale": loc}
    prompt = POST_PROMPT.format(n=req.tips, data=json.dumps(merged, ensure_ascii=False))
    if MODE == "api" and OPENAI_KEY:
        out = llm_api(prompt)
    else:
        out = llm_local(prompt)
    tips = to_bullets(out, req.tips) or ["Keine Tipps erzeugt."]
    return GenResp(tips=tips)

@app.post("/tools/ingest_combat_event")
def ingest(ev: CombatEvent):
    LIVE_EVENTS.append(ev)
    if len(LIVE_EVENTS) > 1000:
        del LIVE_EVENTS[: len(LIVE_EVENTS) - 1000]
    return {"ok": True}

@app.get("/tools/live_events")
def live_events(limit: int = 100):
    return [e.dict() for e in LIVE_EVENTS[-limit:]]


def _character_key(data: Dict[str, Any]) -> str | None:
    player = data.get("player")
    realm = data.get("realm")
    if not player:
        return None
    if not realm:
        return player
    return f"{player}-{str(realm).replace(' ', '')}"
