"""Command-line entrypoint for the walking skeleton.

Wires the real adapters and runs one manual record -> publish cycle:

    birdie --config birdie.toml --champion Katarina --kills 18 --deaths 3 \
        --assists 7 --result Victory --duration 1500

Secrets come from the environment, never the config file:
    BIRDIE_OBS_PASSWORD   obs-websocket password
    BIRDIE_META_TOKEN     Meta Page access token
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from birdie.adapters.ffmpeg_editor import FfmpegEditor
from birdie.adapters.meta_publisher import MetaPublisher
from birdie.adapters.obs_recorder import ObsRecorder
from birdie.captioner import TemplateCaptioner
from birdie.config import load_config
from birdie.models import MatchData
from birdie.pipeline import SkeletonPipeline


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="birdie", description="LoL highlights walking skeleton")
    p.add_argument("--config", type=Path, default=Path("birdie.toml"))
    p.add_argument("--champion", required=True)
    p.add_argument("--kills", type=int, required=True)
    p.add_argument("--deaths", type=int, required=True)
    p.add_argument("--assists", type=int, required=True)
    p.add_argument("--result", required=True, choices=["Victory", "Defeat"])
    p.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="game length in seconds (recorded on the match; unused by the M0 caption)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    config = load_config(args.config)

    obs_password = os.environ.get("BIRDIE_OBS_PASSWORD", "")
    meta_token = os.environ.get("BIRDIE_META_TOKEN")
    if not meta_token:
        print("error: BIRDIE_META_TOKEN is not set", file=sys.stderr)
        return 2

    pipeline = SkeletonPipeline(
        recorder=ObsRecorder(config.obs_host, config.obs_port, obs_password),
        editor=FfmpegEditor(),
        captioner=TemplateCaptioner(),
        publisher=MetaPublisher(config.page_id, meta_token, config.meta_api_version),
        config=config,
    )

    match = MatchData(
        champion=args.champion,
        kills=args.kills,
        deaths=args.deaths,
        assists=args.assists,
        result=args.result,
        duration_seconds=args.duration,
    )

    def wait_for_stop() -> None:
        input("Press Enter when the game is over to publish... ")

    print("Recording started. Play your game...")
    result = pipeline.run(match, wait_for_stop=wait_for_stop)
    print(f"Published: {result.post_id}")
    print(f"Caption:   {result.caption}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
