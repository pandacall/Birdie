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
from birdie.postgame import process_game
from birdie.queue import ReviewQueue
from birdie.review import ReviewService
from birdie.watcher import GameWatcher
from birdie.webreview import serve


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

    rv = sub.add_parser("review", help="serve the local review queue web page")
    rv.add_argument("--host", default="127.0.0.1")
    rv.add_argument("--port", type=int, default=8765)
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


def _run_watch(config: Config, meta_token: str) -> int:
    obs_password = os.environ.get("BIRDIE_OBS_PASSWORD", "")
    editor = FfmpegEditor()
    captioner = TemplateCaptioner()
    publisher = MetaPublisher(config.page_id, meta_token, config.meta_api_version)
    queue = ReviewQueue(config.compilations_dir / "queue")

    def on_game_end(game: CompletedGame) -> None:
        write_event_log(
            config.recordings_dir / f"{game.recording.stem}.events.json", game
        )
        result = process_game(game, config, editor, captioner, publisher, queue)
        if result.video is None:
            outcome = "no clip-worthy moments"
        elif result.published_id is not None:
            outcome = f"auto-published {result.published_id}"
        else:
            outcome = f"queued for review ({result.queued_id})"
        print(f"Game ended: {len(game.events)} events for {game.player} -> {outcome}")

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
    if not meta_token:
        print("error: BIRDIE_META_TOKEN is not set", file=sys.stderr)
        return 2
    if args.command == "skeleton":
        return _run_skeleton(config, args, meta_token)
    if args.command == "watch":
        return _run_watch(config, meta_token)
    if args.command == "review":
        return _run_review(config, meta_token, args.host, args.port)
    return 2


def _run_review(config: Config, meta_token: str, host: str, port: int) -> int:
    publisher = MetaPublisher(config.page_id, meta_token, config.meta_api_version)
    service = ReviewService(ReviewQueue(config.compilations_dir / "queue"), publisher)
    serve(service, host, port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
