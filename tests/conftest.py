from pathlib import Path

from birdie.config import _DEFAULT_SCORES, Config
from birdie.models import MatchData, OutputProfile, Window


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
