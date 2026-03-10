import io
import json
import logging
import os
import pathlib
import re
import time

import requests

SV_PATH = os.getenv("SV_PATH", "/svshare/WTF/Account/.../SavedVariables/AICompanion.lua")
SV_WRITE = os.getenv("SV_WRITE", SV_PATH)
COMBATLOG_PATH = os.getenv("COMBATLOG_PATH", "/svshare/Logs/WoWCombatLog.txt")
MCP_URL = os.getenv("MCP_URL", "http://mcp:8080")
TIPS_COUNT = int(os.getenv("TIPS_COUNT", "5"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))

logging.basicConfig(
    level=os.getenv("WATCHER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [watcher] %(levelname)s: %(message)s",
)
log = logging.getLogger("watcher")

_HTTP = requests.Session()
_MARKER_START = "-- AICOACH_MANAGED_RECO_START"
_MARKER_END = "-- AICOACH_MANAGED_RECO_END"


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


def managed_reco_block(character_key: str, tips: list[str], ts_value) -> str:
    key_literal = json.dumps(character_key, ensure_ascii=False)
    lines = [
        _MARKER_START,
        "AICompanionSV = AICompanionSV or {}",
        "AICompanionSV.recommendations = AICompanionSV.recommendations or {}",
        f"AICompanionSV.recommendations[{key_literal}] = {{",
        f'  ["tips"] = {{',
    ]
    for tip in tips:
        lines.append(f"    {json.dumps(tip, ensure_ascii=False)},")
    lines.extend(
        [
            "  },",
            f'  ["updatedAt"] = {int(ts_value or time.time())},',
            "}",
            "AICompanionCharSV = AICompanionCharSV or {}",
            f'AICompanionCharSV["pendingReco"] = AICompanionSV.recommendations[{key_literal}]["tips"]',
            _MARKER_END,
            "",
        ]
    )
    return "\n".join(lines)


def write_reco(base_text: str, character_key: str, tips: list[str], ts_value) -> None:
    content = re.sub(
        rf"\n?{re.escape(_MARKER_START)}.*?{re.escape(_MARKER_END)}\n?",
        "\n",
        base_text,
        flags=re.DOTALL,
    ).rstrip()
    block = managed_reco_block(character_key, tips, ts_value)
    if content:
        content += "\n\n"
    pathlib.Path(SV_WRITE).write_text(content + block, encoding="utf-8")


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
    def __init__(self, path: str) -> None:
        self.path = path
        self.fp: io.TextIOWrapper | None = None
        self.pos = 0

    def open(self) -> bool:
        if not os.path.exists(self.path):
            return False
        self.fp = open(self.path, "r", encoding="utf-8", errors="ignore")
        self.fp.seek(0, io.SEEK_END)
        self.pos = self.fp.tell()
        return True

    def poll_lines(self) -> list[str]:
        if not self.fp and not self.open():
            return []
        self.fp.seek(self.pos)
        lines = self.fp.readlines()
        self.pos = self.fp.tell()
        return [line.rstrip("\n") for line in lines]


def parse_combatlog_line(line: str) -> dict | None:
    if not line or line.startswith("#"):
        return None
    return {"raw": line, "ts": time.time()}


def main() -> None:
    log.info("Watcher gestartet")
    last_sv_mtime = 0.0
    tail = Tailer(COMBATLOG_PATH)

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
                        session = normalize_session(sessions[-1])
                        mcp_push_session(session)
                        tips = mcp_generate_tips(session, TIPS_COUNT) or ["Keine Tipps erzeugt."]
                        character_key = session.get("characterKey") or "unknown"
                        write_reco(raw, character_key, tips, session.get("ts"))
                        mcp_push_recommendations(character_key, tips, session.get("ts"))
                        log.info("Wrote %d tips for %s", len(tips), character_key)
        except Exception as exc:
            log.error("SV-Fehler: %s", exc)

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
