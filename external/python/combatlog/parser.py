"""CombatLog.txt line parser.

Parses the standard WoW CombatLog format:
  timestamp  SUBEVENT,srcGUID,srcName,srcFlags,srcRaidFlags,dstGUID,dstName,dstFlags,dstRaidFlags,...

Supports both classic and WoW 12.0+ (Midnight) Advanced Combat Log format,
which inserts 19 extra "unit info" fields before damage/heal suffixes.

Returns structured CombatEvent dataclass instances.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .constants import DAMAGE_EVENTS, HEAL_EVENTS, TRACKED_EVENTS

# Regex to split the timestamp from the rest of the line.
# Old format: "3/6 20:00:00.123  SPELL_DAMAGE,..."
# New format (12.0+): "3/6/2026 19:01:55.3611  SPELL_DAMAGE,..."
_TS_RE = re.compile(r"^(\d+/\d+(?:/\d+)?\s+[\d:.]+)\s\s(.+)$")

# GUID prefixes used to detect Advanced Combat Log info block.
# When ADVANCED_LOG_ENABLED=1, 19 extra fields are inserted between
# the spell prefix and the damage/heal suffix.
_GUID_PREFIXES = (
    "Player-", "Creature-", "Pet-", "Vehicle-",
    "GameObject-", "Vignette-", "Item-",
)
_NIL_GUID = "0000000000000000"

# Number of fields in the Advanced Combat Log info block.
_ADVANCED_FIELD_COUNT = 19


@dataclass(slots=True)
class CombatEvent:
    """A single parsed combat log event."""

    timestamp: float  # Unix timestamp (seconds, fractional)
    subevent: str
    source_guid: str = ""
    source_name: str = ""
    source_flags: int = 0
    dest_guid: str = ""
    dest_name: str = ""
    dest_flags: int = 0
    spell_id: int | None = None
    spell_name: str | None = None
    spell_school: int | None = None
    amount: int | None = None
    overkill: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    # Encounter-specific
    encounter_id: int | None = None
    encounter_name: str | None = None
    encounter_success: int | None = None


def _parse_ts(raw: str, year: int | None = None) -> float:
    """Parse WoW timestamp → Unix float.

    Supports both formats:
      - Old:  '3/6 20:00:00.123'       (no year)
      - New:  '3/6/2026 19:01:55.3611'  (with year, WoW 12.0+)
    """
    raw = raw.strip()

    # Try new format first (month/day/year time)
    try:
        dt = datetime.strptime(raw, "%m/%d/%Y %H:%M:%S.%f")
        return dt.timestamp()
    except ValueError:
        pass

    # Fallback: old format without year
    yr = year or datetime.now().year
    try:
        dt = datetime.strptime(f"{yr}/{raw}", "%Y/%m/%d %H:%M:%S.%f")
        return dt.timestamp()
    except ValueError:
        return 0.0


def _safe_int(val: str) -> int | None:
    """Convert string to int, return None on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_hex(val: str) -> int:
    """Convert hex string like '0x511' to int."""
    try:
        return int(val, 16) if val.startswith("0x") else int(val)
    except (ValueError, TypeError):
        return 0


def _is_guid(val: str) -> bool:
    """Check if a value looks like a WoW GUID (used to detect advanced log fields)."""
    val = val.strip()
    if val == _NIL_GUID:
        return True
    return any(val.startswith(p) for p in _GUID_PREFIXES)


def _skip_advanced_info(parts: list[str], idx: int) -> int:
    """Skip the 19-field Advanced Combat Log info block if present.

    Advanced log inserts unit info (GUID, ownerGUID, HP, stats, position, etc.)
    between the spell prefix and the damage/heal suffix.
    Detection: if parts[idx] looks like a GUID, we have advanced fields.
    """
    if idx < len(parts) and _is_guid(parts[idx]):
        return idx + _ADVANCED_FIELD_COUNT
    return idx


def parse_line(line: str, year: int | None = None) -> CombatEvent | None:
    """Parse a single CombatLog.txt line into a CombatEvent.

    Returns None if the line is unparseable or not a tracked event.
    """
    line = line.strip()
    if not line:
        return None

    m = _TS_RE.match(line)
    if not m:
        return None

    ts_raw, payload = m.group(1), m.group(2)
    ts = _parse_ts(ts_raw, year)

    # Parse CSV payload (handles quoted strings with commas)
    reader = csv.reader(io.StringIO(payload))
    try:
        parts = next(reader)
    except StopIteration:
        return None

    if not parts:
        return None

    subevent = parts[0].strip()

    # Only parse events we care about
    if subevent not in TRACKED_EVENTS:
        return None

    ev = CombatEvent(timestamp=ts, subevent=subevent)

    # ── Encounter events have a different format ────────────────────
    if subevent == "ENCOUNTER_START":
        ev.encounter_id = _safe_int(parts[1]) if len(parts) > 1 else None
        ev.encounter_name = parts[2].strip() if len(parts) > 2 else None
        return ev

    if subevent == "ENCOUNTER_END":
        ev.encounter_id = _safe_int(parts[1]) if len(parts) > 1 else None
        ev.encounter_name = parts[2].strip() if len(parts) > 2 else None
        ev.encounter_success = _safe_int(parts[5]) if len(parts) > 5 else None
        return ev

    # ── Standard base params (8 fields after subevent) ──────────────
    if len(parts) < 9:
        return ev

    ev.source_guid = parts[1].strip()
    ev.source_name = parts[2].strip()
    ev.source_flags = _safe_hex(parts[3])
    # parts[4] = srcRaidFlags (skip)
    ev.dest_guid = parts[5].strip()
    ev.dest_name = parts[6].strip()
    ev.dest_flags = _safe_hex(parts[7])
    # parts[8] = dstRaidFlags (skip)

    idx = 9  # next param index

    # ── UNIT_DIED has no spell prefix or suffix ───────────────────
    if subevent == "UNIT_DIED":
        return ev

    # ── SWING_DAMAGE has no spell prefix ──────────────────────────
    if subevent == "SWING_DAMAGE":
        # Skip advanced info block if present
        idx = _skip_advanced_info(parts, idx)
        ev.amount = _safe_int(parts[idx]) if len(parts) > idx else None
        ev.overkill = _safe_int(parts[idx + 1]) if len(parts) > idx + 1 else None
        return ev

    # ── Spell prefix (spellId, spellName, spellSchool) ────────────
    if len(parts) > idx + 2:
        ev.spell_id = _safe_int(parts[idx])
        ev.spell_name = parts[idx + 1].strip()
        ev.spell_school = _safe_int(parts[idx + 2])
        idx += 3

    # ── Skip Advanced Combat Log info block if present ────────────
    idx = _skip_advanced_info(parts, idx)

    # ── Damage suffix ─────────────────────────────────────────────
    if subevent in DAMAGE_EVENTS and len(parts) > idx:
        ev.amount = _safe_int(parts[idx])
        ev.overkill = _safe_int(parts[idx + 1]) if len(parts) > idx + 1 else None

    # ── Heal suffix ───────────────────────────────────────────────
    elif subevent in HEAL_EVENTS and len(parts) > idx:
        ev.amount = _safe_int(parts[idx])
        if len(parts) > idx + 1:
            ev.extra["overheal"] = _safe_int(parts[idx + 1])

    # ── Interrupt suffix ──────────────────────────────────────────
    elif subevent == "SPELL_INTERRUPT" and len(parts) > idx + 2:
        ev.extra["interrupted_spell_id"] = _safe_int(parts[idx])
        ev.extra["interrupted_spell_name"] = (
            parts[idx + 1].strip() if len(parts) > idx + 1 else None
        )

    # ── Dispel suffix ─────────────────────────────────────────────
    elif subevent == "SPELL_DISPEL" and len(parts) > idx + 2:
        ev.extra["dispelled_spell_id"] = _safe_int(parts[idx])
        ev.extra["dispelled_spell_name"] = (
            parts[idx + 1].strip() if len(parts) > idx + 1 else None
        )

    # ── Miss suffix ───────────────────────────────────────────────
    elif subevent == "SPELL_MISSED" and len(parts) > idx:
        ev.extra["miss_type"] = parts[idx].strip()

    return ev
