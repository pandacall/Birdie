"""Walking-skeleton orchestration.

Wires the adapter ports into the thinnest end-to-end path: record a game, plan a
(trivial) compilation, caption it, render it, publish it, then delete the
transient recording. ``wait_for_stop`` is the human-in-the-loop signal (the CLI
blocks on input; tests pass a no-op), keeping start->stop ordering testable.

Later slices replace this with the auto game lifecycle (issue #3) and the real
planner/gate; the port wiring stays the same.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from birdie.config import Config
from birdie.ports import Captioner, Publisher, Recorder, VideoEditor
from birdie.models import Category, Clip, CompilationPlan, MatchData, PostingMode


@dataclass(frozen=True)
class PublishResult:
    post_id: str
    video: Path
    caption: str


class SkeletonPipeline:
    def __init__(
        self,
        recorder: Recorder,
        editor: VideoEditor,
        captioner: Captioner,
        publisher: Publisher,
        config: Config,
    ) -> None:
        self._recorder = recorder
        self._editor = editor
        self._captioner = captioner
        self._publisher = publisher
        self._config = config

    def run(
        self,
        match: MatchData,
        wait_for_stop: Callable[[], None],
    ) -> PublishResult:
        self._recorder.start()
        wait_for_stop()
        recording = self._recorder.stop()

        # M0 has no scoring: one hardcoded Window becomes the whole plan. The
        # real event-driven planner (issue #4) serves the auto/watch path.
        plan = CompilationPlan(
            clips=(
                Clip(
                    window=self._config.skeleton_window,
                    score=0.0,
                    category=Category.EPIC,
                    moments=(),
                ),
            ),
            posting_mode=PostingMode.REVIEW,
            dominant_category=Category.EPIC,
        )
        caption = self._captioner.caption(match, plan.dominant_category)

        out = self._config.compilations_dir / f"{match.champion}-compilation.mp4"
        video = self._editor.render(recording, plan, self._config.output_profile, out)

        # M0 has no Gate: it always publishes. The Gate (issue #5) will route by
        # plan.posting_mode instead of publishing unconditionally here.
        post_id = self._publisher.publish(video, caption)

        recording.unlink(missing_ok=True)
        return PublishResult(post_id=post_id, video=video, caption=caption)
