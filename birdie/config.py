"""Load the Birdie TOML config into a typed Config.

All tuning knobs live here (CONTEXT.md: "config, not architecture"). The
walking skeleton only needs a handful; later slices add scores, rules, tone.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from birdie.gate import Rule
from birdie.models import Category, OutputProfile, PostingMode, Window

_DEFAULT_PROFILE = OutputProfile(name="video", width=1920, height=1080, max_seconds=None)

# Per-event base scores (CONTEXT.md: tuning knobs, not architecture). A death
# scores positively — it is blooper *content*, not a penalty.
_DEFAULT_SCORES: dict[str, float] = {
    "kill": 1.0,
    "assist": 0.5,
    "death": 1.0,
    "double": 3.0,
    "triple": 6.0,
    "quadra": 10.0,
    "penta": 20.0,
    "FirstBlood": 3.0,
    "Ace": 5.0,
    "DragonKill": 2.0,
    "BaronKill": 4.0,
    "HeraldKill": 2.0,
    "TurretKilled": 1.0,
    "InhibKilled": 2.0,
}


@dataclass(frozen=True)
class Config:
    page_id: str
    output_profile: OutputProfile
    skeleton_window: Window
    recordings_dir: Path
    compilations_dir: Path
    merge_gap: float
    length_budget: float
    scores: dict[str, float]
    window_pre: float = 8.0
    window_post: float = 4.0
    rules: list[Rule] = field(default_factory=list)
    default_mode: PostingMode = PostingMode.REVIEW
    obs_host: str = "localhost"
    obs_port: int = 4455
    meta_api_version: str = "v21.0"


def load_config(path: Path) -> Config:
    with path.open("rb") as fh:
        raw: dict[str, Any] = tomllib.load(fh)

    profile_raw = raw.get("output_profile", {})
    profile = OutputProfile(
        name=profile_raw.get("name", _DEFAULT_PROFILE.name),
        width=profile_raw.get("width", _DEFAULT_PROFILE.width),
        height=profile_raw.get("height", _DEFAULT_PROFILE.height),
        max_seconds=profile_raw.get("max_seconds", _DEFAULT_PROFILE.max_seconds),
    )

    skeleton_raw = raw.get("skeleton", {})
    skeleton_window = Window(
        start=float(skeleton_raw.get("window_start", 0.0)),
        end=float(skeleton_raw.get("window_end", 15.0)),
    )

    paths_raw = raw.get("paths", {})
    tuning_raw = raw.get("tuning", {})
    obs_raw = raw.get("obs", {})
    meta_raw = raw.get("meta", {})

    scores = dict(_DEFAULT_SCORES)
    scores.update({k: float(v) for k, v in raw.get("scores", {}).items()})

    rules = [_parse_rule(r) for r in raw.get("rules", [])]
    default_mode = PostingMode(str(raw.get("default_posting_mode", "review")))

    return Config(
        page_id=str(raw.get("page_id", "")),
        output_profile=profile,
        skeleton_window=skeleton_window,
        recordings_dir=Path(paths_raw.get("recordings", "recordings")),
        compilations_dir=Path(paths_raw.get("compilations", "compilations")),
        merge_gap=float(tuning_raw.get("merge_gap", 6.0)),
        length_budget=float(tuning_raw.get("length_budget", 75.0)),
        scores=scores,
        window_pre=float(tuning_raw.get("window_pre", 8.0)),
        window_post=float(tuning_raw.get("window_post", 4.0)),
        rules=rules,
        default_mode=default_mode,
        obs_host=str(obs_raw.get("host", "localhost")),
        obs_port=int(obs_raw.get("port", 4455)),
        meta_api_version=str(meta_raw.get("api_version", "v21.0")),
    )


def _parse_rule(raw: dict[str, Any]) -> Rule:
    return Rule(
        kind=str(raw["kind"]),
        mode=PostingMode(str(raw["mode"])),
        min_streak=int(raw["min_streak"]) if "min_streak" in raw else None,
        category=Category(str(raw["category"])) if "category" in raw else None,
        min_score=float(raw["min_score"]) if "min_score" in raw else None,
    )
