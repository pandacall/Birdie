"""Load the Birdie TOML config into a typed Config.

All tuning knobs live here (CONTEXT.md: "config, not architecture"). The
walking skeleton only needs a handful; later slices add scores, rules, tone.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from birdie.models import OutputProfile, Window

_DEFAULT_PROFILE = OutputProfile(name="video", width=1920, height=1080, max_seconds=None)


@dataclass(frozen=True)
class Config:
    page_id: str
    output_profile: OutputProfile
    skeleton_window: Window
    recordings_dir: Path
    compilations_dir: Path
    merge_gap: float
    length_budget: float
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

    return Config(
        page_id=str(raw.get("page_id", "")),
        output_profile=profile,
        skeleton_window=skeleton_window,
        recordings_dir=Path(paths_raw.get("recordings", "recordings")),
        compilations_dir=Path(paths_raw.get("compilations", "compilations")),
        merge_gap=float(tuning_raw.get("merge_gap", 6.0)),
        length_budget=float(tuning_raw.get("length_budget", 75.0)),
        obs_host=str(obs_raw.get("host", "localhost")),
        obs_port=int(obs_raw.get("port", 4455)),
        meta_api_version=str(meta_raw.get("api_version", "v21.0")),
    )
