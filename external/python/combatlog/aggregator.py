"""Fight aggregator – groups CombatEvents into FightSummary objects.

Tracks ENCOUNTER_START / ENCOUNTER_END boundaries.  Falls back to
PLAYER_REGEN_DISABLED / ENABLED windows from addon SavedVariables.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    DAMAGE_EVENTS,
    ENCOUNTER_KILL,
    GUID_PLAYER,
    HEAL_EVENTS,
)
from .parser import CombatEvent


@dataclass
class SpellUsage:
    """Aggregated usage of a single spell."""

    spell_id: int
    spell_name: str
    casts: int = 0
    total_amount: int = 0  # total damage or heal

    def to_dict(self) -> dict:
        return {
            "spellId": self.spell_id,
            "spellName": self.spell_name,
            "casts": self.casts,
            "totalAmount": self.total_amount,
        }


@dataclass
class PlayerStats:
    """Per-player statistics within a single fight."""

    guid: str
    name: str
    class_: str = ""

    damage_done: int = 0
    healing_done: int = 0
    damage_taken: int = 0
    deaths: int = 0
    interrupts: int = 0
    dispels: int = 0
    spells: dict[int, SpellUsage] = field(default_factory=dict)

    # Computed after fight ends
    dps: float = 0.0
    hps: float = 0.0

    def finalize(self, duration_sec: float) -> None:
        """Compute DPS/HPS from accumulated totals."""
        if duration_sec > 0:
            self.dps = round(self.damage_done / duration_sec, 1)
            self.hps = round(self.healing_done / duration_sec, 1)

    def top_spells(self, n: int = 5) -> list[SpellUsage]:
        """Return top N spells by total amount."""
        return sorted(
            self.spells.values(), key=lambda s: s.total_amount, reverse=True
        )[:n]

    def to_dict(self) -> dict:
        return {
            "guid": self.guid,
            "name": self.name,
            "class": self.class_,
            "damageDone": self.damage_done,
            "healingDone": self.healing_done,
            "damageTaken": self.damage_taken,
            "deaths": self.deaths,
            "interrupts": self.interrupts,
            "dispels": self.dispels,
            "dps": self.dps,
            "hps": self.hps,
            "topSpells": [s.to_dict() for s in self.top_spells()],
        }


@dataclass
class FightSummary:
    """Aggregated summary of a single fight/encounter."""

    encounter_id: int | None = None
    encounter_name: str | None = None
    start: float = 0.0
    end: float = 0.0
    duration_sec: float = 0.0
    result: str = "unknown"  # "kill" | "wipe" | "unknown"
    total_damage: int = 0
    total_healing: int = 0
    players: dict[str, PlayerStats] = field(default_factory=dict)

    def finalize(self) -> None:
        """Compute duration and per-player DPS/HPS."""
        self.duration_sec = round(self.end - self.start, 2) if self.end > self.start else 0.0
        self.total_damage = sum(p.damage_done for p in self.players.values())
        self.total_healing = sum(p.healing_done for p in self.players.values())
        for p in self.players.values():
            p.finalize(self.duration_sec)

    def to_dict(self) -> dict:
        return {
            "encounterId": self.encounter_id,
            "encounterName": self.encounter_name,
            "start": self.start,
            "end": self.end,
            "durationSec": self.duration_sec,
            "result": self.result,
            "totalDamage": self.total_damage,
            "totalHealing": self.total_healing,
            "players": {g: p.to_dict() for g, p in self.players.items()},
        }


class FightAggregator:
    """Stateful aggregator: feed it CombatEvents, get FightSummaries out."""

    def __init__(self) -> None:
        self._current: FightSummary | None = None
        self._completed: list[FightSummary] = []

    @property
    def in_fight(self) -> bool:
        return self._current is not None

    @property
    def current(self) -> FightSummary | None:
        return self._current

    def drain(self) -> list[FightSummary]:
        """Return and clear completed fights."""
        out = self._completed
        self._completed = []
        return out

    def feed(self, ev: CombatEvent) -> FightSummary | None:
        """Process a single event. Returns a FightSummary if a fight just ended."""
        # ── Encounter boundaries ────────────────────────────────────
        if ev.subevent == "ENCOUNTER_START":
            self._current = FightSummary(
                encounter_id=ev.encounter_id,
                encounter_name=ev.encounter_name,
                start=ev.timestamp,
            )
            return None

        if ev.subevent == "ENCOUNTER_END":
            if self._current is None:
                return None
            self._current.end = ev.timestamp
            self._current.result = (
                "kill" if ev.encounter_success == ENCOUNTER_KILL else "wipe"
            )
            self._current.finalize()
            finished = self._current
            self._completed.append(finished)
            self._current = None
            return finished

        # ── If no active fight, start one on first damage/heal event ─
        if self._current is None:
            if ev.subevent in DAMAGE_EVENTS or ev.subevent in HEAL_EVENTS:
                self._current = FightSummary(start=ev.timestamp)
            else:
                return None

        fight = self._current

        # ── Get or create player stats ──────────────────────────────
        def _player(guid: str, name: str) -> PlayerStats:
            if guid not in fight.players:
                fight.players[guid] = PlayerStats(guid=guid, name=name)
            return fight.players[guid]

        # ── Track damage ────────────────────────────────────────────
        if ev.subevent in DAMAGE_EVENTS and ev.amount:
            if ev.source_guid.startswith(GUID_PLAYER):
                ps = _player(ev.source_guid, ev.source_name)
                ps.damage_done += ev.amount
                if ev.spell_id and ev.spell_name:
                    sp = ps.spells.setdefault(
                        ev.spell_id, SpellUsage(ev.spell_id, ev.spell_name)
                    )
                    sp.total_amount += ev.amount
                    sp.casts += 1
            if ev.dest_guid.startswith(GUID_PLAYER):
                pt = _player(ev.dest_guid, ev.dest_name)
                pt.damage_taken += ev.amount

        # ── Track healing ───────────────────────────────────────────
        elif ev.subevent in HEAL_EVENTS and ev.amount:
            if ev.source_guid.startswith(GUID_PLAYER):
                ps = _player(ev.source_guid, ev.source_name)
                ps.healing_done += ev.amount
                if ev.spell_id and ev.spell_name:
                    sp = ps.spells.setdefault(
                        ev.spell_id, SpellUsage(ev.spell_id, ev.spell_name)
                    )
                    sp.total_amount += ev.amount
                    sp.casts += 1

        # ── Track casts ─────────────────────────────────────────────
        elif ev.subevent == "SPELL_CAST_SUCCESS":
            if ev.source_guid.startswith(GUID_PLAYER) and ev.spell_id and ev.spell_name:
                ps = _player(ev.source_guid, ev.source_name)
                sp = ps.spells.setdefault(
                    ev.spell_id, SpellUsage(ev.spell_id, ev.spell_name)
                )
                sp.casts += 1

        # ── Track interrupts ────────────────────────────────────────
        elif ev.subevent == "SPELL_INTERRUPT":
            if ev.source_guid.startswith(GUID_PLAYER):
                ps = _player(ev.source_guid, ev.source_name)
                ps.interrupts += 1

        # ── Track dispels ───────────────────────────────────────────
        elif ev.subevent == "SPELL_DISPEL":
            if ev.source_guid.startswith(GUID_PLAYER):
                ps = _player(ev.source_guid, ev.source_name)
                ps.dispels += 1

        # ── Track deaths ────────────────────────────────────────────
        elif ev.subevent == "UNIT_DIED":
            if ev.dest_guid.startswith(GUID_PLAYER):
                pt = _player(ev.dest_guid, ev.dest_name)
                pt.deaths += 1

        return None

    def force_end(self, timestamp: float) -> FightSummary | None:
        """End current fight (e.g., due to combat drop without ENCOUNTER_END)."""
        if self._current is None:
            return None
        self._current.end = timestamp

        # Determine result based on whether there was meaningful combat
        if self._current.encounter_id:
            # Boss fight timed out = wipe
            self._current.result = "wipe"
        elif any(p.damage_done > 0 for p in self._current.players.values()):
            # Trash with damage = kill (stuff died)
            self._current.result = "kill"
        else:
            self._current.result = "unknown"

        self._current.finalize()
        finished = self._current
        self._completed.append(finished)
        self._current = None
        return finished
