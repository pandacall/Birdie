"""Command-line entrypoint.

Subcommands:
  skeleton   Manual one-shot record -> publish (M0, issue #2).
  watch      Auto game lifecycle: detect games, record, capture the event log,
             hand off to post-game (issue #3).

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
from birdie.adapters.live_client import RiotLiveClient
from birdie.adapters.meta_publisher import MetaPublisher
from birdie.adapters.obs_recorder import ObsRecorder
from birdie.captioner import TemplateCaptioner
from birdie.config import Config, load_config
from birdie.eventlog import write_event_log
from birdie.models import CompletedGame, MatchData
from birdie.pipeline import SkeletonPipeline
from birdie.watcher import GameWatcher


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="birdie", description="LoL highlights pipeline")
    p.add_argument("--config", type=Path, default=Path("birdie.toml"))
    sub = p.add_subparsers(dest="command", required=True)

    sk = sub.add_parser("skeleton", help="manual one-shot record -> publish")
    sk.add_argument("--champion", required=True)
    sk.add_argument("--kills", type=int, required=True)
    sk.add_argument("--deaths", type=int, required=True)
    sk.add_argument("--assists", type=int, required=True)
    sk.add_argument("--result", required=True, choices=["Victory", "Defeat"])
    sk.add_argument("--duration", type=float, default=0.0)

    sub.add_parser("watch", help="auto-detect games and record them")
    return p


def _run_skeleton(config: Config, args: argparse.Namespace, meta_token: str) -> int:
    obs_password = os.environ.get("BIRDIE_OBS_PASSWORD", "")
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


def _run_watch(config: Config) -> int:
    obs_password = os.environ.get("BIRDIE_OBS_PASSWORD", "")

    def on_game_end(game: CompletedGame) -> None:
        log_path = config.recordings_dir / f"{game.recording.stem}.events.json"
        write_event_log(log_path, game)
        print(
            f"Game ended: {len(game.events)} events logged for {game.player}\n"
            f"  recording: {game.recording}\n  event log: {log_path}"
        )

    watcher = GameWatcher(
        api=RiotLiveClient(),
        recorder=ObsRecorder(config.obs_host, config.obs_port, obs_password),
        on_game_end=on_game_end,
    )
    print("Watching for a League game... (Ctrl-C to stop)")
    while True:
        watcher.watch_once()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    config = load_config(args.config)

    meta_token = os.environ.get("BIRDIE_META_TOKEN", "")
    if args.command == "skeleton":
        if not meta_token:
            print("error: BIRDIE_META_TOKEN is not set", file=sys.stderr)
            return 2
        return _run_skeleton(config, args, meta_token)
    if args.command == "watch":
        return _run_watch(config)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
