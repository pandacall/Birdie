"""Caption generation.

The walking skeleton ships the template Captioner only: it states facts drawn
from MatchData and never invents them. Tone shift by dominant Category and the
hashtag policy arrive in a later slice; the LLM flavour layer is iteration 2.
"""

from __future__ import annotations

from birdie.models import Category, MatchData


class TemplateCaptioner:
    """Deterministic, fact-only Captioner (implements the Captioner port)."""

    def caption(self, match: MatchData, dominant_category: Category) -> str:
        kda = f"{match.kills}/{match.deaths}/{match.assists}"
        return f"{match.champion} • {kda} • {match.result}"
