"""Caption generation.

The template Captioner states facts drawn from MatchData and never invents
them; tone shifts with the Compilation's dominant Category, and hashtags are
derived from match data plus compilation Signals. The LLM flavour layer
(iteration 2) will implement the same Captioner port.
"""

from __future__ import annotations

from birdie.models import Category, CompilationPlan, MatchData
from birdie.signals import Signals, compilation_signals

_MAX_HASHTAGS = 8
_STREAK_TAG = {5: "#Pentakill", 4: "#Quadrakill", 3: "#Triplekill"}


class TemplateCaptioner:
    """Deterministic, fact-only Captioner (implements the Captioner port)."""

    def caption(self, match: MatchData, plan: CompilationPlan) -> str:
        kda = f"{match.kills}/{match.deaths}/{match.assists}"
        facts = f"{match.champion} • {kda} • {match.result}"
        body = self._apply_tone(facts, plan.dominant_category)
        tags = self._hashtags(match, compilation_signals(plan))
        return f"{body}\n\n{' '.join(tags)}"

    def _apply_tone(self, facts: str, category: Category) -> str:
        if category == Category.EPIC:
            return f"🔥 {facts} 🔥"
        return f"not my proudest game... {facts} 😅"

    def _hashtags(self, match: MatchData, signals: Signals) -> list[str]:
        tags = ["#LeagueOfLegends", "#LoL", "#" + match.champion.replace(" ", "")]
        streak_tag = _STREAK_TAG.get(signals.max_multikill)
        if streak_tag is not None:
            tags.append(streak_tag)
        if match.result == "Victory":
            tags.append("#Win")
        return tags[:_MAX_HASHTAGS]
