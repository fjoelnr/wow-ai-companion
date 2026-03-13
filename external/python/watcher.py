import io
import json
import logging
import os
import pathlib
import re
import time
import glob

import requests

SV_PATH = os.getenv("SV_PATH", "/svshare/WTF/Account/.../SavedVariables/AICompanion.lua")
SV_WRITE = os.getenv("SV_WRITE", SV_PATH)
COMBATLOG_PATH = os.getenv("COMBATLOG_PATH", "/svshare/Logs/WoWCombatLog.txt")
COMBATLOG_DIR = os.getenv("COMBATLOG_DIR", "")
MCP_URL = os.getenv("MCP_URL", "http://mcp:8080")
TIPS_COUNT = int(os.getenv("TIPS_COUNT", "5"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))

logging.basicConfig(
    level=os.getenv("WATCHER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [watcher] %(levelname)s: %(message)s",
)
log = logging.getLogger("watcher")

_HTTP = requests.Session()


class LuaParser:
    """Small Lua table parser for WoW SavedVariables."""

    def __init__(self, text: str) -> None:
        self.text = re.sub(r"--[^\n]*", "", text)
        self.pos = 0

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def _expect(self, ch: str) -> None:
        self._skip_ws()
        if self.pos >= len(self.text) or self.text[self.pos] != ch:
            raise ValueError(f"Expected {ch!r} at {self.pos}")
        self.pos += 1

    def parse_value(self):
        self._skip_ws()
        ch = self.text[self.pos] if self.pos < len(self.text) else ""
        if ch == "{":
            return self.parse_table()
        if ch == '"':
            return self.parse_string('"')
        if ch == "'":
            return self.parse_string("'")
        return self.parse_literal()

    def parse_string(self, quote: str) -> str:
        self._expect(quote)
        out = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 1
                if self.pos < len(self.text):
                    out.append(self.text[self.pos])
                    self.pos += 1
                continue
            if ch == quote:
                self.pos += 1
                return "".join(out)
            out.append(ch)
            self.pos += 1
        return "".join(out)

    def parse_literal(self):
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] not in " ,}\t\r\n":
            self.pos += 1
        token = self.text[start:self.pos].strip()
        if token == "true":
            return True
        if token == "false":
            return False
        if token == "nil":
            return None
        try:
            return int(token)
        except ValueError:
            pass
        try:
            return float(token)
        except ValueError:
            pass
        return token

    def parse_table(self):
        self._expect("{")
        result_dict = {}
        result_list = []
        is_array = True

        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                break
            if self.text[self.pos] == "}":
                self.pos += 1
                break

            key = self._try_parse_key()
            if key is not None:
                is_array = False
                result_dict[key] = self.parse_value()
            else:
                result_list.append(self.parse_value())

            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == ",":
                self.pos += 1

        if is_array and result_list:
            return result_list
        if not is_array:
            return result_dict
        return result_dict

    def _try_parse_key(self):
        saved = self.pos
        self._skip_ws()

        if self.pos < len(self.text) and self.text[self.pos] == "[":
            self.pos += 1
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] in ('"', "'"):
                key = self.parse_string(self.text[self.pos])
                self._skip_ws()
                if self.pos < len(self.text) and self.text[self.pos] == "]":
                    self.pos += 1
                    self._skip_ws()
                    if self.pos < len(self.text) and self.text[self.pos] == "=":
                        self.pos += 1
                        return key
            self.pos = saved
            return None

        if self.pos < len(self.text) and (
            self.text[self.pos].isalpha() or self.text[self.pos] == "_"
        ):
            start = self.pos
            while self.pos < len(self.text) and (
                self.text[self.pos].isalnum() or self.text[self.pos] == "_"
            ):
                self.pos += 1
            key = self.text[start:self.pos]
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == "=":
                self.pos += 1
                return key
            self.pos = saved
            return None

        return None


def parse_sv(text: str) -> dict:
    match = re.search(r"[a-zA-Z_]\w*\s*=\s*\{", text)
    if not match:
        return {}
    brace_pos = text.index("{", match.start())
    parser = LuaParser(text[brace_pos:])
    try:
        data = parser.parse_value()
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        log.error("Lua parse error: %s", exc)
        return {}


def normalize_session(session: dict) -> dict:
    normalized = dict(session)
    for key in ("fights", "activeQuests", "professions"):
        if isinstance(normalized.get(key), dict):
            normalized[key] = []
    normalized["characterKey"] = normalized.get("characterKey") or derive_character_key(normalized)
    return normalized


def derive_character_key(session: dict) -> str | None:
    player = session.get("player")
    realm = session.get("realm")
    if not player:
        return None
    if not realm:
        return player
    return f"{player}-{str(realm).replace(' ', '')}"


def to_lua(value, indent: int = 0) -> str:
    pad = "  " * indent
    next_pad = "  " * (indent + 1)
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value:
            return "{ }"
        lines = ["{"]
        for item in value:
            lines.append(f"{next_pad}{to_lua(item, indent + 1)},")
        lines.append(f"{pad}}}")
        return "\n".join(lines)
    if isinstance(value, dict):
        if not value:
            return "{ }"
        lines = ["{"]
        for key, item in value.items():
            key_lit = json.dumps(str(key), ensure_ascii=False)
            lines.append(f'{next_pad}[{key_lit}] = {to_lua(item, indent + 1)},')
        lines.append(f"{pad}}}")
        return "\n".join(lines)
    return json.dumps(str(value), ensure_ascii=False)


def write_reco(base_text: str, character_key: str, tips: list[str], ts_value) -> None:
    sv = parse_sv(base_text)
    if not isinstance(sv, dict):
        log.error("Cannot update recommendations: SavedVariables parse failed")
        return

    sv["recommendations"] = sv.get("recommendations") or {}
    if not isinstance(sv["recommendations"], dict):
        sv["recommendations"] = {}

    sv["recommendations"][character_key] = {
        "tips": list(tips or []),
        "updatedAt": int(ts_value or time.time()),
    }

    rendered = "AICompanionSV = " + to_lua(sv, 0) + "\n"
    pathlib.Path(SV_WRITE).write_text(rendered, encoding="utf-8")


def mcp_generate_tips(session: dict, tips_count: int) -> list[str]:
    resp = _HTTP.post(
        f"{MCP_URL}/tools/generate_tips",
        json={"session": session, "tips": tips_count},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("tips", [])


def mcp_push_session(session: dict) -> bool:
    try:
        resp = _HTTP.post(f"{MCP_URL}/api/session", json={"session": session}, timeout=10)
        return resp.ok
    except Exception as exc:
        log.warning("Session push failed: %s", exc)
        return False


def mcp_push_recommendations(character_key: str, tips: list[str], ts_value) -> bool:
    try:
        resp = _HTTP.post(
            f"{MCP_URL}/api/recommendations",
            json={
                "characterKey": character_key,
                "tips": tips,
                "updatedAt": int(ts_value or time.time()),
            },
            timeout=10,
        )
        return resp.ok
    except Exception as exc:
        log.warning("Recommendation push failed: %s", exc)
        return False


def mcp_ingest_combat_event(event: dict) -> None:
    try:
        _HTTP.post(f"{MCP_URL}/tools/ingest_combat_event", json=event, timeout=5)
    except Exception:
        pass


class Tailer:
    def __init__(self, path: str, logs_dir: str | None = None) -> None:
        self.path = path
        self.logs_dir = logs_dir or ""
        self.fp: io.TextIOWrapper | None = None
        self.pos = 0
        self.current_path: str | None = None
        self.last_scan = 0.0

    def open(self) -> bool:
        target = self.resolve_path()
        if not target or not os.path.exists(target):
            return False
        self.fp = open(target, "r", encoding="utf-8", errors="ignore")
        self.fp.seek(0, io.SEEK_END)
        self.pos = self.fp.tell()
        self.current_path = target
        return True

    def poll_lines(self) -> list[str]:
        self.maybe_rotate()
        if not self.fp and not self.open():
            return []
        self.fp.seek(self.pos)
        lines = self.fp.readlines()
        self.pos = self.fp.tell()
        return [line.rstrip("\n") for line in lines]

    def resolve_path(self) -> str | None:
        if os.path.isfile(self.path):
            return self.path
        if self.logs_dir:
            return find_latest_combatlog(self.logs_dir)
        return None

    def maybe_rotate(self) -> None:
        if not self.logs_dir:
            return
        now = time.time()
        if now - self.last_scan < 5:
            return
        self.last_scan = now
        latest = find_latest_combatlog(self.logs_dir)
        if latest and latest != self.current_path:
            if self.fp:
                self.fp.close()
            self.fp = None
            self.pos = 0
            self.current_path = latest


def find_latest_combatlog(logs_dir: str) -> str | None:
    candidates = []
    classic = os.path.join(logs_dir, "WoWCombatLog.txt")
    if os.path.exists(classic):
        candidates.append(classic)
    candidates.extend(glob.glob(os.path.join(logs_dir, "WoWCombatLog-*.txt")))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def parse_combatlog_line(line: str) -> dict | None:
    if not line or line.startswith("#"):
        return None
    return {"raw": line, "ts": time.time()}


def main() -> None:
    log.info("Watcher gestartet")
    last_sv_mtime = 0.0
    logs_dir = COMBATLOG_DIR or os.path.dirname(COMBATLOG_PATH)
    tail = Tailer(COMBATLOG_PATH, logs_dir=logs_dir)
    pending_session: dict | None = None
    known_sessions: dict[str, dict] = {}
    pending_raw_sv: str = ""
    retry_session_at = 0.0
    retry_reco_at = 0.0
    session_backoff = 5.0
    reco_backoff = 5.0
    reco_done_for_ts: int | float | None = None

    while True:
        try:
            if os.path.exists(SV_PATH):
                mtime = os.path.getmtime(SV_PATH)
                if mtime != last_sv_mtime:
                    last_sv_mtime = mtime
                    raw = pathlib.Path(SV_PATH).read_text(encoding="utf-8", errors="ignore")
                    sv = parse_sv(raw)
                    sessions = sv.get("sessions", [])
                    if isinstance(sessions, list) and sessions:
                        latest_by_character: dict[str, dict] = {}
                        for raw_session in sessions:
                            if not isinstance(raw_session, dict):
                                continue
                            session = normalize_session(raw_session)
                            character_key = session.get("characterKey")
                            if not character_key:
                                continue
                            current = latest_by_character.get(character_key)
                            current_ts = int((current or {}).get("ts") or 0)
                            session_ts = int(session.get("ts") or 0)
                            if not current or session_ts >= current_ts:
                                latest_by_character[character_key] = session

                        if latest_by_character:
                            known_sessions = latest_by_character
                            pending_session = max(
                                latest_by_character.values(),
                                key=lambda s: int(s.get("ts") or 0),
                            )
                            pending_raw_sv = raw
                            retry_session_at = 0.0
                            retry_reco_at = 0.0
        except Exception as exc:
            log.error("SV-Fehler: %s", exc)

        now = time.time()
        if known_sessions and now >= retry_session_at:
            all_ok = True
            for session in known_sessions.values():
                if not mcp_push_session(session):
                    all_ok = False
                    break
            if all_ok:
                retry_session_at = float("inf")
                session_backoff = 5.0
            else:
                retry_session_at = now + session_backoff
                session_backoff = min(session_backoff * 2, 60.0)

        if pending_session and now >= retry_reco_at:
            session_ts = pending_session.get("ts")
            if session_ts == reco_done_for_ts:
                retry_reco_at = float("inf")
            else:
                try:
                    tips = mcp_generate_tips(pending_session, TIPS_COUNT) or ["Keine Tipps erzeugt."]
                    character_key = pending_session.get("characterKey") or "unknown"
                    write_reco(pending_raw_sv, character_key, tips, pending_session.get("ts"))
                    mcp_push_recommendations(character_key, tips, pending_session.get("ts"))
                    reco_done_for_ts = session_ts
                    retry_reco_at = float("inf")
                    reco_backoff = 5.0
                    log.info("Wrote %d tips for %s", len(tips), character_key)
                except Exception as exc:
                    log.error("Recommendation generation failed: %s", exc)
                    retry_reco_at = now + reco_backoff
                    reco_backoff = min(reco_backoff * 2, 60.0)

        try:
            for raw_line in tail.poll_lines():
                event = parse_combatlog_line(raw_line)
                if event:
                    mcp_ingest_combat_event(event)
        except Exception as exc:
            log.error("CombatLog-Fehler: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
