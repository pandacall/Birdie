"""Adapter seams (ports) for the pipeline.

Each Protocol is a boundary the orchestration observes behaviour at. Real
implementations wrap external systems (OBS, FFmpeg, Meta); tests substitute
fakes. Keeping these as Protocols is what lets the walking skeleton be verified
end-to-end without touching any external service.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from birdie.models import Category, CompilationPlan, MatchData, OutputProfile


class Recorder(Protocol):
    """Drives the recorder (OBS) for a single game."""

    def start(self) -> None:
        """Begin recording the full game to a single file."""
        ...

    def stop(self) -> Path:
        """Stop recording and return the path to the recording file."""
        ...


class VideoEditor(Protocol):
    """Turns a recording + a plan into a single compilation video file."""

    def render(
        self,
        recording: Path,
        plan: CompilationPlan,
        profile: OutputProfile,
        out: Path,
    ) -> Path:
        """Cut the plan's Windows from the recording and concat into ``out``."""
        ...


class Captioner(Protocol):
    """Produces the Caption text for a Compilation. Swappable: template now,
    LLM in iteration 2."""

    def caption(self, match: MatchData, dominant_category: Category) -> str:
        ...


class Publisher(Protocol):
    """Publishes a compilation video to the Facebook Page."""

    def publish(self, video: Path, caption: str) -> str:
        """Publish and return the created post's id (or URL)."""
        ...
