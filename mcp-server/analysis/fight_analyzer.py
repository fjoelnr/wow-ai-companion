"""Fight analyzer – takes a FightSummary + player context and produces
coaching feedback via LLM."""

from __future__ import annotations

import json
import logging
import pathlib
from dataclasses import dataclass

from llm.base import LLMProvider

from .prompt_templates import (
    FIGHT_ANALYSIS_PROMPT,
    SYSTEM_ANALYZE,
    format_player_line,
    format_top_spells,
)

log = logging.getLogger(__name__)

# Class profile directory (markdown files)
_PROFILES_DIR = pathlib.Path(__file__).parent / "class_profiles"


@dataclass
class AnalysisResult:
    """Structured output from fight analysis."""

    summary: str = ""
    rating: str = "?"
    highlights: list[str] | None = None
    improvements: list[str] | None = None
    tips: list[str] | None = None
    raw: str = ""  # raw LLM output for debugging

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "rating": self.rating,
            "highlights": self.highlights or [],
            "improvements": self.improvements or [],
            "tips": self.tips or [],
        }


def _load_class_profile(class_name: str) -> str:
    """Load class-specific analysis notes from markdown files."""
    slug = class_name.lower().strip()
    # Map common WoW class identifiers
    slug_map = {
        "deathknight": "warrior",  # fallback until DK profile exists
        "demonhunter": "default",
        "evoker": "default",
        "druid": "default",
        "monk": "default",
        "rogue": "default",
        "shaman": "default",
        "warlock": "default",
    }
    slug = slug_map.get(slug, slug)

    profile_path = _PROFILES_DIR / f"{slug}.md"
    if profile_path.exists():
        return profile_path.read_text(encoding="utf-8")

    default_path = _PROFILES_DIR / "default.md"
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")

    return "(no class-specific notes available)"


def _format_number(n: int | float) -> str:
    """Format large numbers nicely."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"


class FightAnalyzer:
    """Analyzes completed fights using an LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def analyze(
        self,
        fight: dict,
        player_guid: str | None = None,
        player_class: str = "",
        locale: str = "deDE",
    ) -> AnalysisResult:
        """Analyze a fight summary and return coaching feedback.

        Args:
            fight: FightSummary dict (from aggregator.to_dict()).
            player_guid: GUID of the player to coach. If None, picks the
                         first player or highest DPS.
            player_class: WoW class name for class-specific notes.
            locale: Response language (deDE or enUS).

        Returns:
            AnalysisResult with structured feedback.
        """
        players = fight.get("players", {})
        if not players:
            return AnalysisResult(summary="No player data in this fight.")

        # Find the player to coach
        if player_guid and player_guid in players:
            target = players[player_guid]
        else:
            # Pick highest DPS player
            target = max(players.values(), key=lambda p: p.get("dps", 0))

        target_name = target.get("name", "Unknown")
        target_class = player_class or target.get("class", "Unknown")

        # Build all-players summary
        all_lines = []
        for _guid, pdata in sorted(
            players.items(), key=lambda x: x[1].get("dps", 0), reverse=True
        ):
            all_lines.append(format_player_line(pdata.get("name", "?"), pdata))

        # Format the prompt
        duration_sec = fight.get("durationSec", 0)
        duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}"

        prompt = FIGHT_ANALYSIS_PROMPT.format(
            encounter_name=fight.get("encounterName") or "Trash / Open World",
            result=fight.get("result", "unknown"),
            duration=duration_str,
            total_damage=_format_number(fight.get("totalDamage", 0)),
            total_healing=_format_number(fight.get("totalHealing", 0)),
            player_name=target_name,
            player_class=target_class,
            player_dps=_format_number(target.get("dps", 0)),
            player_hps=_format_number(target.get("hps", 0)),
            player_deaths=target.get("deaths", 0),
            player_interrupts=target.get("interrupts", 0),
            player_dispels=target.get("dispels", 0),
            player_damage_taken=_format_number(target.get("damageTaken", 0)),
            top_spells=format_top_spells(target.get("topSpells", [])),
            all_players="\n".join(all_lines) or "(solo)",
            class_notes=_load_class_profile(target_class),
            locale=locale,
        )

        # Call LLM
        try:
            raw = await self._provider.generate(prompt, system=SYSTEM_ANALYZE)
        except Exception as exc:
            log.error("LLM analysis failed: %s", exc)
            return AnalysisResult(
                summary=f"Analysis failed: {exc}",
                raw=str(exc),
            )

        # Parse JSON from LLM response
        return self._parse_response(raw)

    @staticmethod
    def _parse_response(raw: str) -> AnalysisResult:
        """Parse the LLM JSON response into an AnalysisResult."""
        result = AnalysisResult(raw=raw)

        # Extract JSON from response (LLM might wrap in markdown code block)
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1]
            text = text.split("```", 1)[0]

        try:
            data = json.loads(text.strip())
            result.summary = data.get("summary", "")
            result.rating = data.get("rating", "?")
            result.highlights = data.get("highlights", [])
            result.improvements = data.get("improvements", [])
            result.tips = data.get("tips", [])
        except json.JSONDecodeError:
            log.warning("Failed to parse LLM analysis as JSON, using raw text")
            result.summary = raw[:200]

        return result
