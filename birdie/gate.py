"""The Gate: route a finished Compilation to a Posting mode.

Rules are evaluated top-to-bottom, first match wins, with a default at the
bottom (CONTEXT.md). Rules key only on compilation-level Signals, never on raw
clips, so the decision is explainable and testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from birdie.models import Category, CompilationPlan, PostingMode
from birdie.signals import Signals, compilation_signals


@dataclass(frozen=True)
class Rule:
    kind: str  # "contains_multikill" | "peak_category" | "min_score"
    mode: PostingMode
    min_streak: int | None = None
    category: Category | None = None
    min_score: float | None = None


def _matches(rule: Rule, signals: Signals) -> bool:
    if rule.kind == "contains_multikill":
        return rule.min_streak is not None and signals.max_multikill >= rule.min_streak
    if rule.kind == "peak_category":
        return signals.peak_category == rule.category
    if rule.kind == "min_score":
        return rule.min_score is not None and signals.aggregate_score >= rule.min_score
    return False


def decide_posting_mode(
    plan: CompilationPlan,
    rules: list[Rule],
    default: PostingMode,
) -> PostingMode:
    signals = compilation_signals(plan)
    for rule in rules:
        if _matches(rule, signals):
            return rule.mode
    return default
