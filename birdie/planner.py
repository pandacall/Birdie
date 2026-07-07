"""The planner — the pure heart of the post-game pipeline and the primary test
seam.

``plan_compilation`` turns a CompletedGame into a CompilationPlan with no I/O:
score events into Moments, build Windows via the timeline anchor, merge adjacent
Moments into Clips, select Clips to a length budget (with the per-game guarantee
and the reserved blooper slot), and order them chronologically.

Match data is deliberately *not* an input: nothing here needs it. It is a
caption concern, handled by the Captioner seam. The Gate (issue #5) recomputes
``posting_mode``; the planner defaults it to the documented ``review``.
"""

from __future__ import annotations

from birdie.config import Config
from birdie.models import (
    Category,
    Clip,
    CompilationPlan,
    CompletedGame,
    Moment,
    PostingMode,
    Window,
)
from birdie.scoring import score_event
from birdie.timeline import to_recording_offset

_DIMINISH = 0.7


def plan_compilation(game: CompletedGame, config: Config) -> CompilationPlan:
    moments = [
        m
        for e in game.events
        if (m := score_event(e, game.player, config.scores)) is not None
    ]
    clips = _merge(
        moments, game, config.window_pre, config.window_post, config.merge_gap
    )
    selected = _select(clips, config.length_budget)
    selected.sort(key=lambda c: c.window.start)
    return CompilationPlan(
        clips=tuple(selected),
        posting_mode=PostingMode.REVIEW,
        dominant_category=_dominant_category(selected),
    )


def _merge(
    moments: list[Moment],
    game: CompletedGame,
    pre: float,
    post: float,
    gap: float,
) -> list[Clip]:
    if not moments:
        return []

    paired = [
        (
            m,
            Window(
                to_recording_offset(game.anchor, m.event.game_time - pre),
                to_recording_offset(game.anchor, m.event.game_time + post),
            ),
        )
        for m in moments
    ]
    paired.sort(key=lambda pw: pw[1].start)

    groups: list[list[tuple[Moment, Window]]] = [[paired[0]]]
    group_end = paired[0][1].end
    for moment, window in paired[1:]:
        if window.start - group_end <= gap:
            groups[-1].append((moment, window))
            group_end = max(group_end, window.end)
        else:
            groups.append([(moment, window)])
            group_end = window.end

    return [_clip_from_group(group) for group in groups]


def _clip_from_group(group: list[tuple[Moment, Window]]) -> Clip:
    moments = tuple(m for m, _ in group)
    start = min(w.start for _, w in group)
    end = max(w.end for _, w in group)
    peak = max(moments, key=lambda m: m.score)
    return Clip(
        window=Window(start, end),
        score=_aggregate([m.score for m in moments]),
        category=peak.category,
        moments=moments,
    )


def _aggregate(scores: list[float]) -> float:
    ordered = sorted(scores, reverse=True)
    return sum(score * (_DIMINISH**i) for i, score in enumerate(ordered))


def _select(clips: list[Clip], budget: float) -> list[Clip]:
    ranked = sorted(clips, key=lambda c: c.score, reverse=True)

    selected: list[Clip] = []
    total = 0.0
    for clip in ranked:
        if total + clip.window.duration <= budget:
            selected.append(clip)
            total += clip.window.duration

    if not selected and ranked:
        selected = [ranked[0]]  # per-game guarantee floor

    _reserve_blooper_slot(selected, clips)
    return selected


def _reserve_blooper_slot(selected: list[Clip], all_clips: list[Clip]) -> None:
    """If the selection is all epics but a blooper exists, swap the lowest-scored
    epic for the top blooper. Only when >=2 clips are selected, so the headline
    epic is never dropped from a tiny compilation."""
    if len(selected) < 2 or any(c.category == Category.BLOOPER for c in selected):
        return
    bloopers = [c for c in all_clips if c.category == Category.BLOOPER]
    if not bloopers:
        return
    top_blooper = max(bloopers, key=lambda c: c.score)
    lowest_epic = min(selected, key=lambda c: c.score)
    selected.remove(lowest_epic)
    selected.append(top_blooper)


def _dominant_category(clips: list[Clip]) -> Category:
    if not clips:
        return Category.EPIC
    return max(clips, key=lambda c: c.score).category
