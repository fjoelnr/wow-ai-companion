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

POST_PROMPT = """You are a precise WoW quest and profession assistant.
You must only use the provided data. Do not invent NPC names, locations, quest IDs, or rewards.
Write in language: {lang_name}.
Return EXACTLY {n} tips in strict JSON:
{{"tips":["...","..."]}}
Rules:
- each tip <= 160 characters
- actionable, concrete, non-automating advice
- prioritize active quests, turn-ins, profession progression, and current zone goals
- if data is missing, say that briefly instead of guessing
DATA:
{data}
"""

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
        {"role":"system","content":"Return strict JSON only: {\"tips\":[...]} with concise grounded WoW tips."},
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


def locale_language_name(locale: str | None) -> str:
    value = (locale or "deDE").lower()
    if value.startswith("de"):
        return "German"
    if value.startswith("en"):
        return "English"
    return "German"


def compact_session_for_prompt(data: Dict[str, Any]) -> Dict[str, Any]:
    quests = data.get("activeQuests") or []
    profs = data.get("professions") or []
    compact_quests = []
    for q in quests[:20]:
        compact_quests.append({
            "id": q.get("id"),
            "title": q.get("title"),
            "isComplete": q.get("isComplete"),
        })
    compact_profs = []
    for p in profs[:8]:
        compact_profs.append({
            "name": p.get("name"),
            "skillLevel": p.get("skillLevel"),
            "maxLevel": p.get("maxLevel"),
        })

    return {
        "locale": data.get("locale"),
        "characterKey": data.get("characterKey"),
        "player": data.get("player"),
        "class": data.get("class"),
        "level": data.get("level"),
        "ilvl": data.get("ilvl"),
        "zone": data.get("zone"),
        "subZone": (data.get("location") or {}).get("subZone"),
        "activeQuests": compact_quests,
        "professions": compact_profs,
    }


def extract_tips(text: str, n: int) -> List[str]:
    payload = text.strip()
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, dict) and isinstance(parsed.get("tips"), list):
            tips = [str(x).strip() for x in parsed["tips"] if str(x).strip()]
            return tips[:n]
        if isinstance(parsed, list):
            tips = [str(x).strip() for x in parsed if str(x).strip()]
            return tips[:n]
    except Exception:
        pass
    return to_bullets(text, n)


def normalize_tip(text: str) -> str:
    tip = re.sub(r"\s+", " ", str(text or "")).strip()
    tip = tip.lstrip("-•* ").strip()
    if len(tip) > 160:
        tip = tip[:157].rstrip() + "..."
    return tip


def add_tokens(terms: List[str], text: Any) -> None:
    if not isinstance(text, str):
        return
    value = text.strip().lower()
    if not value:
        return
    terms.append(value)
    for token in re.findall(r"[a-zA-Z0-9äöüÄÖÜß]{4,}", value):
        terms.append(token.lower())


def build_grounding_terms(session: Dict[str, Any]) -> List[str]:
    terms = []
    zone = session.get("zone")
    sub_zone = (session.get("location") or {}).get("subZone")
    add_tokens(terms, zone)
    add_tokens(terms, sub_zone)
    for q in session.get("activeQuests") or []:
        qid = q.get("id")
        title = q.get("title")
        if qid is not None:
            terms.append(str(qid).lower())
        add_tokens(terms, title)
    for p in session.get("professions") or []:
        add_tokens(terms, p.get("name"))
    return terms


def is_grounded_tip(tip: str, terms: List[str]) -> bool:
    if not terms:
        return True
    lower_tip = tip.lower()
    for term in terms:
        if term and term in lower_tip:
            return True
    return False


SPEC_ROLE_MAP: Dict[int, str] = {
    # Tank
    73: "tank", 250: "tank", 268: "tank", 66: "tank", 581: "tank", 104: "tank",
    # Healer
    65: "healer", 256: "healer", 257: "healer", 264: "healer", 270: "healer",
    105: "healer", 1468: "healer",
    # DPS
    71: "dps", 72: "dps", 253: "dps", 254: "dps", 255: "dps", 251: "dps",
    252: "dps", 577: "dps", 102: "dps", 103: "dps", 1467: "dps", 62: "dps",
    63: "dps", 64: "dps", 269: "dps", 70: "dps", 258: "dps", 259: "dps",
    260: "dps", 261: "dps", 262: "dps", 263: "dps", 265: "dps", 266: "dps",
    267: "dps", 1473: "dps",
}

CLASS_ROLE_FALLBACK: Dict[str, str] = {
    "warrior": "dps",
    "paladin": "dps",
    "hunter": "dps",
    "rogue": "dps",
    "priest": "healer",
    "death knight": "dps",
    "shaman": "dps",
    "mage": "dps",
    "warlock": "dps",
    "monk": "dps",
    "druid": "dps",
    "demon hunter": "dps",
    "evoker": "dps",
}


def infer_role(session: Dict[str, Any]) -> str | None:
    spec_id = session.get("specId")
    if isinstance(spec_id, int) and spec_id in SPEC_ROLE_MAP:
        return SPEC_ROLE_MAP[spec_id]
    raw_class = str(session.get("class") or "").strip().lower().replace("_", " ")
    if raw_class in CLASS_ROLE_FALLBACK:
        return CLASS_ROLE_FALLBACK[raw_class]
    return None


def class_role_tip(session: Dict[str, Any], locale: str) -> str | None:
    is_de = (locale or "deDE").lower().startswith("de")
    role = infer_role(session)
    if not role:
        return None
    if is_de:
        if role == "tank":
            return "Als Tank: Def-CDs für große Pulls/Elite-Mobs einplanen und zuerst gefährliche Caster markieren."
        if role == "healer":
            return "Als Heiler: Mana für Kampfspitzen sparen und Questkämpfe mit Def-CD/Utility vorplanen."
        return "Als DD: Prioritätsziel zuerst fokussieren, CDs in kurzen Fenstern bündeln und Downtime minimieren."
    if role == "tank":
        return "As tank: plan defensives for big pulls/elites and mark dangerous casters first."
    if role == "healer":
        return "As healer: preserve mana for damage spikes and pre-plan defensives/utility for quest fights."
    return "As DPS: focus priority targets first, stack burst CDs in short windows, and reduce downtime."


def fallback_tips(session: Dict[str, Any], n: int, locale: str) -> List[str]:
    is_de = (locale or "deDE").lower().startswith("de")
    tips: List[str] = []
    quests = session.get("activeQuests") or []
    professions = session.get("professions") or []
    zone = session.get("zone") or "deiner Zone"

    complete_quests = [q for q in quests if q.get("isComplete")]
    open_quests = [q for q in quests if not q.get("isComplete")]

    if complete_quests:
        q = complete_quests[0]
        if is_de:
            tips.append(f'Gib die fertige Quest "{q.get("title", q.get("id"))}" ab, bevor du neue Aufgaben startest.')
        else:
            tips.append(f'Turn in completed quest "{q.get("title", q.get("id"))}" before picking new tasks.')
    if open_quests:
        q = open_quests[0]
        if is_de:
            tips.append(f'Fokussiere als Nächstes "{q.get("title", q.get("id"))}" für klaren Quest-Fortschritt.')
        else:
            tips.append(f'Focus next on "{q.get("title", q.get("id"))}" for clean quest progress.')
    if professions:
        p = professions[0]
        cur = p.get("skillLevel", 0)
        maxv = p.get("maxLevel", 0)
        if is_de:
            tips.append(f'Berufsschritt: {p.get("name","Beruf")} von {cur}/{maxv} auf den nächsten Meilenstein pushen.')
        else:
            tips.append(f'Profession step: push {p.get("name","profession")} from {cur}/{maxv} to next milestone.')
    if is_de:
        tips.append(f'In {zone} zuerst Questziele und Abgabepunkte abarbeiten, dann Nebenaktivitäten.')
    else:
        tips.append(f'In {zone}, clear quest objectives and turn-ins first, then side activities.')

    while len(tips) < n:
        tips.append("Keine zusätzlichen sicheren Hinweise aus den aktuellen Daten ableitbar.")
    return [normalize_tip(t) for t in tips[:n]]

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
RECOMMENDATIONS_BY_CHARACTER: Dict[str, Dict[str, Any]] = {}


class SessionEnvelope(BaseModel):
    session: Session


class RecommendationEnvelope(BaseModel):
    characterKey: str
    tips: List[str]
    updatedAt: Optional[int] = None

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


@app.post("/api/recommendations")
def ingest_recommendations(req: RecommendationEnvelope):
    RECOMMENDATIONS_BY_CHARACTER[req.characterKey] = {
        "characterKey": req.characterKey,
        "tips": req.tips,
        "updatedAt": req.updatedAt,
    }
    return {"ok": True}


@app.get("/api/recommendations")
def get_recommendations(character_key: str | None = None):
    if character_key:
        return RECOMMENDATIONS_BY_CHARACTER.get(character_key, {})
    return RECOMMENDATIONS_BY_CHARACTER

@app.post("/tools/generate_tips", response_model=GenResp)
def generate_tips(req: GenReq):
    loc = req.session.locale or "deDE"
    data = req.session.dict(by_alias=True)
    data["characterKey"] = data.get("characterKey") or _character_key(data)
    merged = {**(data or {}), "locale": loc}
    compact = compact_session_for_prompt(merged)
    prompt = POST_PROMPT.format(
        n=req.tips,
        lang_name=locale_language_name(loc),
        data=json.dumps(compact, ensure_ascii=False),
    )
    if MODE == "api" and OPENAI_KEY:
        out = llm_api(prompt)
    else:
        out = llm_local(prompt)
    candidate_tips = [normalize_tip(t) for t in extract_tips(out, req.tips) if normalize_tip(t)]
    terms = build_grounding_terms(merged)
    grounded = [t for t in candidate_tips if is_grounded_tip(t, terms)]
    tips = grounded[:req.tips]
    if not tips and candidate_tips:
        tips = candidate_tips[:req.tips]
    role_tip = normalize_tip(class_role_tip(merged, loc))
    if role_tip and len(tips) < req.tips and role_tip not in tips:
        tips.append(role_tip)
    if len(tips) < req.tips:
        for tip in fallback_tips(merged, req.tips, loc):
            if len(tips) >= req.tips:
                break
            if tip not in tips:
                tips.append(tip)
    while len(tips) < req.tips:
        tips.append("Keine zusätzlichen sicheren Hinweise aus den aktuellen Daten ableitbar.")
    tips = tips[:req.tips]
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
