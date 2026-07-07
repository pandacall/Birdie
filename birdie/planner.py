"""The planner — the pure heart of the post-game pipeline.

``plan_compilation`` is the primary test seam (see the PRD): given a game's
event log, match data, and config, it returns a CompilationPlan with no I/O.

For the walking skeleton it is deliberately trivial: it emits the single
configured window and defaults the gating decision. Later slices replace the
body with real scoring, the merge pass, selection, and the gate — the signature
and return type stay put.
"""

from __future__ import annotations

from birdie.config import Config
from birdie.models import (
    Category,
    CompilationPlan,
    Event,
    MatchData,
    PostingMode,
)


def plan_compilation(
    event_log: list[Event],
    match: MatchData,
    config: Config,
) -> CompilationPlan:
    return CompilationPlan(
        windows=(config.skeleton_window,),
        # The documented default is REVIEW (CONTEXT.md). M0 has no Gate yet and
        # publishes directly regardless (see SkeletonPipeline); the Gate that
        # honours this field arrives in issue #5.
        posting_mode=PostingMode.REVIEW,
        dominant_category=Category.EPIC,
    )
