"""Post-game processing: turn a CompletedGame into a rendered Compilation.

This slice (issue #4) plans and renders. The Gate, captioning, and the
publish/review-queue routing arrive in issue #5, layered on top of this step.
"""

from __future__ import annotations

from pathlib import Path

from birdie.config import Config
from birdie.models import CompletedGame
from birdie.planner import plan_compilation
from birdie.ports import VideoEditor


def process_game(
    game: CompletedGame,
    config: Config,
    editor: VideoEditor,
) -> Path | None:
    """Plan and render the game's Compilation. Returns the video path, or None
    when the game produced no clip-worthy Moments."""
    plan = plan_compilation(game, config)
    if not plan.clips:
        return None
    out = config.compilations_dir / f"{game.recording.stem}-compilation.mp4"
    return editor.render(game.recording, plan, config.output_profile, out)
