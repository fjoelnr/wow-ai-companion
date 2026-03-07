"""WoW CombatLog constants – event types, damage schools, etc."""

# ── Subevent categories ─────────────────────────────────────────────────
# Events we parse and track for analysis.

DAMAGE_EVENTS = frozenset({
    "SPELL_DAMAGE",
    "SPELL_PERIODIC_DAMAGE",
    "SWING_DAMAGE",
    "RANGE_DAMAGE",
    "ENVIRONMENTAL_DAMAGE",
})

HEAL_EVENTS = frozenset({
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
})

CAST_EVENTS = frozenset({
    "SPELL_CAST_SUCCESS",
    "SPELL_CAST_START",
})

AURA_EVENTS = frozenset({
    "SPELL_AURA_APPLIED",
    "SPELL_AURA_REMOVED",
    "SPELL_AURA_REFRESH",
})

TRACKED_EVENTS = (
    DAMAGE_EVENTS
    | HEAL_EVENTS
    | CAST_EVENTS
    | AURA_EVENTS
    | frozenset({
        "SPELL_INTERRUPT",
        "SPELL_DISPEL",
        "SPELL_MISSED",
        "UNIT_DIED",
        "ENCOUNTER_START",
        "ENCOUNTER_END",
        "SPELL_SUMMON",
    })
)

# ── Damage schools (bitmask) ────────────────────────────────────────────
SCHOOLS = {
    1: "Physical",
    2: "Holy",
    4: "Fire",
    8: "Nature",
    16: "Frost",
    32: "Shadow",
    64: "Arcane",
}

# ── GUID prefixes ───────────────────────────────────────────────────────
GUID_PLAYER = "Player-"
GUID_CREATURE = "Creature-"
GUID_PET = "Pet-"

# ── Encounter results ──────────────────────────────────────────────────
ENCOUNTER_KILL = 1
ENCOUNTER_WIPE = 0
