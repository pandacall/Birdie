from pathlib import Path

from birdie.config import _DEFAULT_SCORES, Config
from birdie.models import (
    Category,
    Clip,
    CompilationPlan,
    Event,
    MatchData,
    Moment,
    OutputProfile,
    PostingMode,
    Window,
)


def make_config(**overrides: object) -> Config:
    base = dict(
        page_id="test-page",
        output_profile=OutputProfile("video", 1920, 1080, None),
        skeleton_window=Window(10.0, 25.0),
        recordings_dir=Path("recordings"),
        compilations_dir=Path("compilations"),
        merge_gap=6.0,
        length_budget=75.0,
        scores=dict(_DEFAULT_SCORES),
        window_pre=8.0,
        window_post=4.0,
    )
    base.update(overrides)
    return Config(**base)  # type: ignore[arg-type]


def make_match(**overrides: object) -> MatchData:
    base = dict(
        champion="Katarina",
        kills=18,
        deaths=3,
        assists=7,
        result="Victory",
        duration_seconds=1500.0,
    )
    base.update(overrides)
    return MatchData(**base)  # type: ignore[arg-type]


def make_moment(
    name: str = "ChampionKill",
    score: float = 1.0,
    category: Category = Category.EPIC,
    kill_streak: int | None = None,
) -> Moment:
    event = Event(id=1, name=name, game_time=100.0, kill_streak=kill_streak)
    return Moment(event=event, score=score, category=category)


def make_clip(
    score: float = 1.0,
    category: Category = Category.EPIC,
    moments: tuple[Moment, ...] | None = None,
    start: float = 0.0,
    end: float = 12.0,
) -> Clip:
    return Clip(
        window=Window(start, end),
        score=score,
        category=category,
        moments=moments if moments is not None else (make_moment(score=score, category=category),),
    )


def make_plan(
    clips: tuple[Clip, ...] | None = None,
    posting_mode: PostingMode = PostingMode.REVIEW,
    dominant_category: Category = Category.EPIC,
) -> CompilationPlan:
    return CompilationPlan(
        clips=clips if clips is not None else (make_clip(),),
        posting_mode=posting_mode,
        dominant_category=dominant_category,
    )
