"""Post-game processing: turn a CompletedGame into a rendered, captioned
Compilation and route it through the Gate.

Auto-mode compilations publish immediately; everything else is persisted to the
review queue. Failure handling (parking, idempotency) is layered on in issue #7.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from birdie.config import Config
from birdie.eventlog import read_event_log
from birdie.gate import decide_posting_mode
from birdie.ledger import ProcessedLedger
from birdie.match import match_from_game
from birdie.models import CompletedGame, PostingMode
from birdie.planner import plan_compilation
from birdie.ports import Captioner, Publisher, VideoEditor
from birdie.queue import ReviewQueue


@dataclass(frozen=True)
class PostGameResult:
    video: Path | None
    posting_mode: PostingMode | None
    published_id: str | None = None
    queued_id: str | None = None


def process_game(
    game: CompletedGame,
    config: Config,
    editor: VideoEditor,
    captioner: Captioner,
    publisher: Publisher,
    queue: ReviewQueue,
) -> PostGameResult:
    plan = plan_compilation(game, config)
    if not plan.clips:
        return PostGameResult(video=None, posting_mode=None)

    match = match_from_game(game)
    out = config.compilations_dir / f"{game.recording.stem}-compilation.mp4"
    video = editor.render(game.recording, plan, config.output_profile, out)
    caption = captioner.caption(match, plan)

    mode = decide_posting_mode(plan, config.rules, config.default_mode)
    if mode == PostingMode.AUTO:
        try:
            post_id = publisher.publish(video, caption)
        except Exception as exc:  # publish failed (e.g. expired token) — park, never drop
            item = queue.add(
                video, caption, status="parked", reason=f"publish failed: {exc}"
            )
            return PostGameResult(video=video, posting_mode=mode, queued_id=item.id)
        return PostGameResult(video=video, posting_mode=mode, published_id=post_id)

    item = queue.add(video, caption)
    return PostGameResult(video=video, posting_mode=mode, queued_id=item.id)


def run_post_game(
    game: CompletedGame,
    config: Config,
    editor: VideoEditor,
    captioner: Captioner,
    publisher: Publisher,
    queue: ReviewQueue,
    ledger: ProcessedLedger,
) -> PostGameResult:
    """Idempotent, crash-safe wrapper around process_game.

    Skips games already in the ledger (no double-post). A failure in any step
    parks the game with the error and keeps the agent running rather than
    crashing. Marks the game processed either way so it isn't retried in a loop.
    """
    game_id = game.recording.stem
    if ledger.contains(game_id):
        return PostGameResult(video=None, posting_mode=None)
    try:
        result = process_game(game, config, editor, captioner, publisher, queue)
    except Exception as exc:  # any post-game step failed — park, don't crash
        queue.add(
            game.recording,
            caption="[processing failed]",
            status="parked",
            reason=str(exc),
        )
        ledger.mark(game_id)
        return PostGameResult(video=None, posting_mode=None)
    ledger.mark(game_id)
    return result


def recover_orphans(
    config: Config,
    editor: VideoEditor,
    captioner: Captioner,
    publisher: Publisher,
    queue: ReviewQueue,
    ledger: ProcessedLedger,
) -> list[PostGameResult]:
    """Process any persisted event logs whose games weren't finished — e.g. the
    agent crashed after a game ended but before publishing."""
    results: list[PostGameResult] = []
    for log_path in sorted(config.recordings_dir.glob("*.events.json")):
        game = read_event_log(log_path)
        if ledger.contains(game.recording.stem):
            continue
        results.append(
            run_post_game(game, config, editor, captioner, publisher, queue, ledger)
        )
    return results
