"""Post-game processing: turn a CompletedGame into a rendered, captioned
Compilation and route it through the Gate.

Auto-mode compilations publish immediately; everything else is persisted to the
review queue. Failure handling (parking, idempotency) is layered on in issue #7.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from birdie.config import Config
from birdie.gate import decide_posting_mode
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
        post_id = publisher.publish(video, caption)
        return PostGameResult(video=video, posting_mode=mode, published_id=post_id)

    item = queue.add(video, caption)
    return PostGameResult(video=video, posting_mode=mode, queued_id=item.id)
