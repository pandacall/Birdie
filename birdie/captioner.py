"""Caption generation.

The template Captioner states facts drawn from MatchData and never invents
them; Tone shifts with the Compilation's dominant Category (falling back to the
configured default), and hashtags are derived from match data plus compilation
Signals. The LLM flavour layer (iteration 2) will implement the same port.
"""

from __future__ import annotations

from birdie.models import Category, CompilationPlan, MatchData, Tone
from birdie.signals import Signals, compilation_signals

_MAX_HASHTAGS = 8
_STREAK_TAG = {5: "#Pentakill", 4: "#Quadrakill", 3: "#Triplekill"}
_TONE_BY_CATEGORY = {
    Category.EPIC: Tone.HYPE,
    Category.BLOOPER: Tone.SELF_DEPRECATING,
}


class TemplateCaptioner:
    """Deterministic, fact-only Captioner (implements the Captioner port)."""

    def __init__(self, default_tone: Tone = Tone.DEADPAN) -> None:
        self._default_tone = default_tone

    def caption(self, match: MatchData, plan: CompilationPlan) -> str:
        kda = f"{match.kills}/{match.deaths}/{match.assists}"
        facts = f"{match.champion} • {kda} • {match.result}"
        tone = _TONE_BY_CATEGORY.get(plan.dominant_category, self._default_tone)
        tags = self._hashtags(match, compilation_signals(plan))
        return f"{self._render(tone, facts)}\n\n{' '.join(tags)}"

    def _render(self, tone: Tone, facts: str) -> str:
        if tone == Tone.HYPE:
            return f"🔥 {facts} 🔥"
        if tone == Tone.SELF_DEPRECATING:
            return f"not my proudest game... {facts} 😅"
        return facts  # deadpan

    def _hashtags(self, match: MatchData, signals: Signals) -> list[str]:
        tags = ["#LeagueOfLegends", "#LoL", "#" + match.champion.replace(" ", "")]
        streak_tag = _STREAK_TAG.get(signals.max_multikill)
        if streak_tag is not None:
            tags.append(streak_tag)
        if match.result == "Victory":
            tags.append("#Win")
        return tags[:_MAX_HASHTAGS]
