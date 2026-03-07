"""Prompt templates for fight analysis."""

SYSTEM_ANALYZE = """\
You are an expert World of Warcraft combat analyst and coach.
You analyze post-fight data and provide actionable, specific feedback.
Be concise, constructive, and reference actual numbers from the data.
Never suggest using third-party automation tools.
Respond in the player's locale (given in the data)."""

FIGHT_ANALYSIS_PROMPT = """\
Analyze this fight and provide coaching feedback.

## Fight Data
- Encounter: {encounter_name} ({result})
- Duration: {duration}
- Total Damage: {total_damage}
- Total Healing: {total_healing}

## Player to Coach
- Name: {player_name}
- Class/Spec: {player_class}
- DPS: {player_dps}
- HPS: {player_hps}
- Deaths: {player_deaths}
- Interrupts: {player_interrupts}
- Dispels: {player_dispels}
- Damage Taken: {player_damage_taken}

## Top Spells Used
{top_spells}

## All Players in Fight
{all_players}

## Class-Specific Notes
{class_notes}

## Locale
{locale}

---

Provide your analysis in this exact JSON format:
{{
  "summary": "1-2 sentence fight summary",
  "rating": "S/A/B/C/D/F",
  "highlights": ["positive point 1", "positive point 2", ...],
  "improvements": ["improvement 1", "improvement 2", ...],
  "tips": ["actionable tip 1", "actionable tip 2", ...]
}}

Keep each point under 120 characters. Return 2-4 highlights, 2-4 improvements, and 2-3 tips."""


def format_player_line(name: str, stats: dict) -> str:
    """Format a single player line for the prompt."""
    dps = stats.get("dps", 0)
    hps = stats.get("hps", 0)
    deaths = stats.get("deaths", 0)
    interrupts = stats.get("interrupts", 0)
    parts = [f"{name}: {dps:.0f} DPS, {hps:.0f} HPS"]
    if deaths:
        parts.append(f"{deaths} deaths")
    if interrupts:
        parts.append(f"{interrupts} interrupts")
    return ", ".join(parts)


def format_top_spells(spells: list[dict], limit: int = 8) -> str:
    """Format top spells list for the prompt."""
    if not spells:
        return "(no spell data)"
    lines = []
    for sp in spells[:limit]:
        name = sp.get("spellName", "Unknown")
        casts = sp.get("casts", 0)
        total = sp.get("totalAmount", 0)
        lines.append(f"- {name}: {casts} casts, {total:,} total")
    return "\n".join(lines)
