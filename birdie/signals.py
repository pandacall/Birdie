"""Compilation-level signals derived from a plan.

Single source of truth for the facts the Gate keys on and the Captioner uses for
event hashtags, so both agree.
"""

from __future__ import annotations

from dataclasses import dataclass

from birdie.models import Category, CompilationPlan


@dataclass(frozen=True)
class Signals:
    max_multikill: int
    peak_category: Category
    aggregate_score: float


def compilation_signals(plan: CompilationPlan) -> Signals:
    max_multikill = 0
    aggregate = 0.0
    for clip in plan.clips:
        aggregate += clip.score
        for moment in clip.moments:
            if moment.event.name == "Multikill" and moment.event.kill_streak:
                max_multikill = max(max_multikill, moment.event.kill_streak)
    return Signals(
        max_multikill=max_multikill,
        peak_category=plan.dominant_category,
        aggregate_score=aggregate,
    )
