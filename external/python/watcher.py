import io
import json
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


def parse_sv(text: str) -> dict:
    """Very rough Lua table to JSON heuristic for MVP."""
    text = re.sub(r"--.*", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= 0:
        return {}
    blob = text[start:end]
    blob = re.sub(r'([a-zA-Z_]\w*)\s*=', r'"\1":', blob)
    blob = blob.replace("'", '"').replace("nil", "null")
    return json.loads(blob)


def write_reco(tips: list[str]) -> None:
    out = "AICompanionSV = AICompanionSV or {}\n"
    out += "AICompanionCharSV = AICompanionCharSV or {}\n"
    out += 'AICompanionCharSV["pendingReco"] = {\n'
    for tip in tips:
        out += f"  {json.dumps(tip, ensure_ascii=False)},\n"
    out += "}\n"
    pathlib.Path(SV_WRITE).write_text(out, encoding="utf-8")


def mcp_generate_tips(session: dict, tips_count: int) -> list[str]:
    resp = requests.post(
        f"{MCP_URL}/tools/generate_tips",
        json={"session": session, "tips": tips_count},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("tips", [])


def mcp_ingest_combat_event(event: dict) -> None:
    try:
        requests.post(f"{MCP_URL}/tools/ingest_combat_event", json=event, timeout=5)
    except Exception:
        # Best-effort only; never crash the loop due to network hiccups.
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
        if not self.fp:
            if not self.open():
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
    print("Watcher gestartet.")
    last_sv_mtime = 0.0
    tail = Tailer(COMBATLOG_PATH)

    while True:
        # 1) SavedVariables snapshot detected
        try:
            if os.path.exists(SV_PATH):
                mtime = os.path.getmtime(SV_PATH)
                if mtime != last_sv_mtime:
                    last_sv_mtime = mtime
                    raw = pathlib.Path(SV_PATH).read_text(encoding="utf-8", errors="ignore")
                    sv = parse_sv(raw)
                    sessions = sv.get("sessions", [])
                    if sessions:
                        session = sessions[-1]
                        tips = mcp_generate_tips(session, TIPS_COUNT) or ["Keine Tipps erzeugt."]
                        write_reco(tips)
                        print(f"[SV] {len(tips)} Tipps geschrieben. (/reload im Spiel)")
        except Exception as exc:
            print("SV-Fehler:", exc)

        # 2) Stream combat log
        try:
            for raw_line in tail.poll_lines():
                event = parse_combatlog_line(raw_line)
                if event:
                    mcp_ingest_combat_event(event)
        except Exception as exc:
            print("CombatLog-Fehler:", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
