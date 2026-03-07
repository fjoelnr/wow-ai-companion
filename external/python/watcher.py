"""WoW AI Companion – File Watcher.

Monitors SavedVariables and CombatLog files, sends structured data
to the MCP server for processing and WebSocket broadcast.

Supports WoW's timestamped combat log naming: WoWCombatLog-MMDDYY_HHMMSS.txt
"""

import glob
import io
import json
import logging
import os
import pathlib
import re
import time

import requests

from combatlog.parser import parse_line
from combatlog.aggregator import FightAggregator

# ── Configuration ───────────────────────────────────────────────────────
SV_PATH = os.getenv("SV_PATH", "/svshare/WTF/Account/.../SavedVariables/AICompanion.lua")
SV_WRITE = os.getenv("SV_WRITE", SV_PATH)
COMBATLOG_PATH = os.getenv("COMBATLOG_PATH", "/wow/Logs/WoWCombatLog.txt")
COMBATLOG_DIR = os.getenv("COMBATLOG_DIR", "")  # Auto-detect dir from COMBATLOG_PATH
MCP_URL = os.getenv("MCP_URL", "http://mcp:9090")
TIPS_COUNT = int(os.getenv("TIPS_COUNT", "5"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))

# No-encounter timeout: if we're tracking a non-boss fight and see no
# events for this many seconds, force-close the fight.
COMBAT_TIMEOUT = float(os.getenv("COMBAT_TIMEOUT", "15.0"))

logging.basicConfig(
    level=os.getenv("WATCHER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [watcher] %(levelname)s: %(message)s",
)
log = logging.getLogger("watcher")

_MARKER_START = "-- AICOACH_PENDING_RECO_START"
_MARKER_END = "-- AICOACH_PENDING_RECO_END"
_HTTP = requests.Session()


# ── SavedVariables helpers ──────────────────────────────────────────────


class LuaParser:
    """Minimal Lua table parser for WoW SavedVariables."""

    def __init__(self, text: str) -> None:
        # Strip Lua comments
        self.text = re.sub(r"--[^\n]*", "", text)
        self.pos = 0

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def _peek(self) -> str:
        self._skip_ws()
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def _expect(self, ch: str) -> None:
        self._skip_ws()
        if self.pos < len(self.text) and self.text[self.pos] == ch:
            self.pos += 1
        else:
            raise ValueError(
                f"Expected '{ch}' at pos {self.pos}, got '{self.text[self.pos:self.pos+20]}'"
            )

    def parse_value(self) -> object:
        self._skip_ws()
        ch = self.text[self.pos] if self.pos < len(self.text) else ""

        if ch == "{":
            return self.parse_table()
        elif ch == '"':
            return self.parse_string()
        elif ch == "'":
            return self.parse_string("'")
        else:
            return self.parse_literal()

    def parse_string(self, quote: str = '"') -> str:
        self._expect(quote)
        result = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 1
                if self.pos < len(self.text):
                    result.append(self.text[self.pos])
                    self.pos += 1
                continue
            if ch == quote:
                self.pos += 1
                return "".join(result)
            result.append(ch)
            self.pos += 1
        return "".join(result)

    def parse_literal(self) -> object:
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] not in " ,}\t\r\n":
            self.pos += 1
        token = self.text[start : self.pos].strip()
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

    def parse_table(self) -> dict | list:
        """Parse a Lua table. Returns dict (keyed) or list (array)."""
        self._expect("{")
        result_dict: dict = {}
        result_list: list = []
        is_array = True  # Assume array until we see a key

        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                break
            if self.text[self.pos] == "}":
                self.pos += 1
                break

            # Try to detect key = value
            key = self._try_parse_key()
            if key is not None:
                is_array = False
                val = self.parse_value()
                result_dict[key] = val
            else:
                val = self.parse_value()
                result_list.append(val)

            # Skip optional comma
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == ",":
                self.pos += 1

        if is_array and result_list:
            return result_list
        if not is_array:
            return result_dict
        return result_dict  # empty → dict

    def _try_parse_key(self) -> str | None:
        """Try to parse a key (bracket or bare) before '='. Returns None if no key found."""
        saved = self.pos
        self._skip_ws()

        # Bracket key: ["key"]
        if self.pos < len(self.text) and self.text[self.pos] == "[":
            bracket_start = self.pos
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
            # Not a string key in brackets, restore
            self.pos = saved
            return None

        # Bare key: identifier =
        if self.pos < len(self.text) and (
            self.text[self.pos].isalpha() or self.text[self.pos] == "_"
        ):
            start = self.pos
            while self.pos < len(self.text) and (
                self.text[self.pos].isalnum() or self.text[self.pos] == "_"
            ):
                self.pos += 1
            key = self.text[start : self.pos]
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == "=":
                self.pos += 1
                return key
            # Not followed by =, restore
            self.pos = saved
            return None

        return None


def parse_sv(text: str) -> dict:
    """Parse WoW SavedVariables Lua table to Python dict."""
    # Find the first top-level assignment: VarName = { ... }
    match = re.search(r"[a-zA-Z_]\w*\s*=\s*\{", text)
    if not match:
        return {}
    # Position parser at the opening brace
    brace_pos = text.index("{", match.start())
    parser = LuaParser(text[brace_pos:])
    try:
        result = parser.parse_value()
        return result if isinstance(result, dict) else {}
    except Exception as exc:
        print(f"[SV] Lua parse error: {exc}")
        return {}


def normalize_session(session: dict) -> dict:
    """Normalize parser output to match MCP schema expectations."""
    normalized = dict(session)
    for key in ("fights", "activeQuests", "professions"):
        if isinstance(normalized.get(key), dict):
            normalized[key] = []
    return normalized


def write_reco(tips: list[str], base_text: str = "") -> None:
    """Write/replace pending recommendations in SavedVariables safely.

    We keep existing SavedVariables content and only replace our own managed
    block, so session history is not lost.
    """
    out = f"{_MARKER_START}\n"
    out += "AICompanionCharSV = AICompanionCharSV or {}\n"
    out += 'AICompanionCharSV["pendingReco"] = {\n'
    for tip in tips:
        out += f"  {json.dumps(tip, ensure_ascii=False)},\n"
    out += "}\n"
    out += f"{_MARKER_END}\n"

    current = base_text
    if not current and pathlib.Path(SV_WRITE).exists():
        current = pathlib.Path(SV_WRITE).read_text(encoding="utf-8", errors="ignore")
    if current:
        pattern = rf"\n?{re.escape(_MARKER_START)}.*?{re.escape(_MARKER_END)}\n?"
        current = re.sub(pattern, "\n", current, flags=re.DOTALL)
        current = current.rstrip() + "\n\n"
    pathlib.Path(SV_WRITE).write_text(current + out, encoding="utf-8")


# ── MCP API calls ──────────────────────────────────────────────────────


def mcp_generate_tips(session: dict, tips_count: int) -> list[str]:
    resp = _HTTP.post(
        f"{MCP_URL}/tools/generate_tips",
        json={"session": session, "tips": tips_count},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("tips", [])


def mcp_send_combat_event(event: dict) -> None:
    """Send a structured combat event to the MCP server."""
    try:
        resp = _HTTP.post(f"{MCP_URL}/api/combat-event", json=event, timeout=5)
        if not resp.ok:
            log.warning("[EVENT] MCP rejected combat event: HTTP %s", resp.status_code)
    except Exception as exc:
        log.warning("[EVENT] Failed to send combat event: %s", exc)


def mcp_send_fight_summary(summary: dict) -> None:
    """Send a completed fight summary to the MCP server."""
    try:
        _HTTP.post(f"{MCP_URL}/api/fight-summary", json=summary, timeout=10)
    except Exception as exc:
        log.error("[FIGHT] Failed to send fight summary: %s", exc)


def mcp_send_session(session: dict) -> None:
    """Push session data to the MCP server."""
    try:
        resp = _HTTP.post(f"{MCP_URL}/api/session", json={"session": session}, timeout=5)
        if not resp.ok:
            log.warning("[SV] MCP rejected session update: HTTP %s", resp.status_code)
    except Exception as exc:
        log.warning("[SV] Failed to push session update: %s", exc)


# ── CombatLog file detection ─────────────────────────────────────────


def find_latest_combatlog(logs_dir: str) -> str | None:
    """Find the most recently modified WoWCombatLog file.

    WoW creates timestamped files like WoWCombatLog-MMDDYY_HHMMSS.txt.
    Also checks for the classic WoWCombatLog.txt name.
    """
    candidates = []

    # Check classic single-file name
    classic = os.path.join(logs_dir, "WoWCombatLog.txt")
    if os.path.exists(classic):
        candidates.append(classic)

    # Check timestamped names
    pattern = os.path.join(logs_dir, "WoWCombatLog-*.txt")
    candidates.extend(glob.glob(pattern))

    if not candidates:
        return None

    # Return the most recently modified file
    return max(candidates, key=os.path.getmtime)


# ── CombatLog tailer ───────────────────────────────────────────────────


class Tailer:
    """Tails the latest CombatLog file, auto-detects new files."""

    def __init__(self, logs_dir: str, explicit_path: str | None = None) -> None:
        self.logs_dir = logs_dir
        self.explicit_path = explicit_path  # If a specific file was set
        self.current_file: str | None = None
        self.fp: io.TextIOWrapper | None = None
        self.pos = 0
        self._last_scan = 0.0
        self._scan_interval = 5.0  # Check for new files every 5s

    def _resolve_file(self) -> str | None:
        """Determine which file to tail."""
        # If an explicit path was given and it exists, use it
        if self.explicit_path and os.path.isfile(self.explicit_path):
            return self.explicit_path
        # Otherwise auto-detect latest in directory
        return find_latest_combatlog(self.logs_dir)

    def _open_file(self, path: str, from_end: bool = True) -> bool:
        """Open a file for tailing."""
        try:
            self.fp = open(path, "r", encoding="utf-8", errors="ignore")
            if from_end:
                self.fp.seek(0, io.SEEK_END)
            self.pos = self.fp.tell()
            self.current_file = path
            return True
        except Exception as exc:
            print(f"[TAIL] Failed to open {path}: {exc}")
            return False

    def _check_for_new_file(self) -> None:
        """Periodically check if a newer combat log file appeared."""
        now = time.time()
        if now - self._last_scan < self._scan_interval:
            return
        self._last_scan = now

        latest = find_latest_combatlog(self.logs_dir)
        if latest and latest != self.current_file:
            print(f"[TAIL] New combat log detected: {os.path.basename(latest)}")
            if self.fp:
                self.fp.close()
                self.fp = None
            # Open the new file from the end (don't replay old data)
            self._open_file(latest, from_end=True)

    def poll_lines(self) -> list[str]:
        """Return new lines since last poll."""
        # First time: find and open a file
        if not self.fp:
            target = self._resolve_file()
            if not target:
                return []
            if not self._open_file(target, from_end=True):
                return []
            print(f"[TAIL] Tailing: {os.path.basename(target)}")

        # Check for newer files periodically
        self._check_for_new_file()

        try:
            self.fp.seek(self.pos)
            lines = self.fp.readlines()
            self.pos = self.fp.tell()
            return [line.rstrip("\n") for line in lines if line.strip()]
        except Exception:
            # File may have been rotated/truncated
            self.fp = None
            self.pos = 0
            return []


# ── Main loop ──────────────────────────────────────────────────────────


def main() -> None:
    log.info("Watcher gestartet. MCP=%s", MCP_URL)
    log.info("  SV_PATH=%s", SV_PATH)
    log.info("  SV_WRITE=%s", SV_WRITE)
    log.info("  COMBATLOG_PATH=%s", COMBATLOG_PATH)

    # Determine combat log directory
    logs_dir = COMBATLOG_DIR
    if not logs_dir:
        # Derive from COMBATLOG_PATH
        logs_dir = os.path.dirname(COMBATLOG_PATH)
    log.info("  COMBATLOG_DIR=%s", logs_dir)

    # If COMBATLOG_PATH points to a specific existing file, pass it explicitly
    explicit = COMBATLOG_PATH if os.path.isfile(COMBATLOG_PATH) else None

    # Find initial file
    latest = find_latest_combatlog(logs_dir)
    if latest:
        log.info("  Latest CombatLog: %s", os.path.basename(latest))
    else:
        log.info("  No CombatLog files found yet (will auto-detect when WoW starts logging)")

    last_sv_mtime = 0.0
    last_tip_session_ts: int | float | None = None
    tail = Tailer(logs_dir, explicit_path=explicit)
    aggregator = FightAggregator()
    last_event_wall = 0.0    # wall clock: when we last processed an event
    last_event_log_ts = 0.0  # CombatLog timestamp of last event

    while True:
        # ── 1) SavedVariables snapshot ──────────────────────────────
        try:
            if os.path.exists(SV_PATH):
                mtime = os.path.getmtime(SV_PATH)
                if mtime != last_sv_mtime:
                    last_sv_mtime = mtime
                    raw = pathlib.Path(SV_PATH).read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    sv = parse_sv(raw)
                    sessions = sv.get("sessions", [])
                    if sessions:
                        session = normalize_session(sessions[-1])
                        # Push session to MCP (for WebSocket broadcast)
                        mcp_send_session(session)
                        log.info(
                            "[SV] Session: %s (%s) iLvl %s @ %s",
                            session.get("player", "?"),
                            session.get("class", "?"),
                            session.get("ilvl", "?"),
                            session.get("zone", "?"),
                        )

                        # Generate tips once per exported session.
                        session_ts = session.get("ts")
                        if session_ts != last_tip_session_ts:
                            try:
                                tips = mcp_generate_tips(session, TIPS_COUNT)
                                if tips:
                                    write_reco(tips, base_text=raw)
                                    log.info("[SV] Wrote %d recommendations to pendingReco", len(tips))
                                else:
                                    log.warning("[SV] MCP returned no tips for session ts=%s", session_ts)
                                last_tip_session_ts = session_ts
                            except Exception as exc:
                                log.error("[SV] Failed to generate/write tips: %s", exc)
        except Exception as exc:
            log.error("SV-Fehler: %s", exc)

        # ── 2) Stream combat log (structured) ──────────────────────
        try:
            for raw_line in tail.poll_lines():
                event = parse_line(raw_line)
                if event is None:
                    continue

                last_event_wall = time.time()
                last_event_log_ts = event.timestamp

                # Send structured event to MCP → WebSocket broadcast
                ev_dict = {
                    "ts": event.timestamp,
                    "subevent": event.subevent,
                    "sourceName": event.source_name,
                    "destName": event.dest_name,
                    "spellId": event.spell_id,
                    "spellName": event.spell_name,
                    "amount": event.amount,
                    "extra": event.extra,
                }
                mcp_send_combat_event(ev_dict)

                # Feed aggregator
                finished = aggregator.feed(event)
                if finished:
                    summary = finished.to_dict()
                    mcp_send_fight_summary(summary)
                    log.info(
                        "[FIGHT] %s (%s) - %.0fs - %d players",
                        finished.encounter_name or "Trash",
                        finished.result,
                        finished.duration_sec,
                        len(finished.players),
                    )
        except Exception as exc:
            log.error("CombatLog-Fehler: %s", exc)

        # ── 3) Timeout: end stale non-encounter fights ─────────────
        # Use wall clock to detect timeout, but CombatLog timestamp for fight end time
        if aggregator.in_fight and last_event_wall > 0:
            if time.time() - last_event_wall > COMBAT_TIMEOUT:
                finished = aggregator.force_end(last_event_log_ts)
                if finished:
                    mcp_send_fight_summary(finished.to_dict())
                    log.info("[FIGHT] Timeout - fight ended after %ss idle", COMBAT_TIMEOUT)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
