from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="WoW AI Companion MCP")

# Runtime config
MODE = os.getenv("LLM_MODE", "local")  # "local" | "api"
OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
FALLBACK = os.getenv("OLLAMA_FALLBACK_MODEL", "mistral-nemo")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

POST_PROMPT = """You are a concise WoW exploration/quest coach.
Return EXACTLY {n} bullet tips (<=160 chars) in the player's locale (field 'locale').
Focus on exploration, missed turn-ins, quest items, rares, points of interest.
Never suggest automation; textual tips only.
DATA:
```json
{data}
```"""


def llm_local(prompt: str) -> str:
    r = requests.post(
        f"{OLLAMA}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    if r.ok:
        return r.json().get("response", "")
    if FALLBACK:
        r2 = requests.post(
            f"{OLLAMA}/api/generate",
            json={"model": FALLBACK, "prompt": prompt, "stream": False},
            timeout=60,
        )
        r2.raise_for_status()
        return r2.json().get("response", "")
    r.raise_for_status()
    return ""  # never reached


def llm_api(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise WoW coach. Only bullet tips."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def to_bullets(text: str, n: int) -> List[str]:
    """Extrahiere bis zu n Bullet-Tipps aus einem LLM-Text."""
    tips: List[str] = []

    # Unordered bullets (- • *)
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] in "-•*":
            s = s.lstrip("-•* ").strip()
            if s:
                tips.append(s)

    # Fallback: nummerierte Liste ("1. foo")
    if not tips:
        for line in text.splitlines():
            m = re.match(r"^\s*\d+\.\s*(.+)$", line.strip())
            if m:
                tips.append(m.group(1).strip())

    return tips[:n] if tips else []


# ---- Schemas ---------------------------------------------------------------------

class Session(BaseModel):
    ts: Optional[int] = None
    player: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    specId: Optional[int] = None
    zone: Optional[str] = None
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


# ---- State -----------------------------------------------------------------------

LIVE_EVENTS: List[CombatEvent] = []

# ---- Endpoints -------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "wow-ai-mcp",
        "endpoints": [
            "/tools/ping",
            "/tools/generate_tips",
            "/tools/ingest_combat_event",
            "/tools/live_events",
            "/healthz",
        ],
    }


@app.get("/tools/ping")
def ping():
    return {"pong": True}


@app.get("/healthz")
def health():
    return {"ok": True}


@app.post("/tools/generate_tips", response_model=GenResp)
def generate_tips(req: GenReq):
    loc = req.session.locale or "deDE"
    data = req.session.model_dump(by_alias=True)
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
    return [e.model_dump() for e in LIVE_EVENTS[-limit:]]
