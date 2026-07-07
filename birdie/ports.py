"""Adapter seams (ports) for the pipeline.

Each Protocol is a boundary the orchestration observes behaviour at. Real
implementations wrap external systems (OBS, FFmpeg, Meta); tests substitute
fakes. Keeping these as Protocols is what lets the walking skeleton be verified
end-to-end without touching any external service.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from birdie.models import CompilationPlan, MatchData, OutputProfile


class LiveClient(Protocol):
    """Reads the Riot Live Client Data API (localhost:2999) for the live game."""

    def active_player(self) -> str | None:
        """The active player's riot id, or None when no game is running."""
        ...

    def active_champion(self) -> str:
        """The active player's champion name."""
        ...

    def game_time(self) -> float:
        """Current in-game clock in seconds."""
        ...

    def event_dicts(self) -> list[dict[str, Any]]:
        """The raw (cumulative) event list from the API."""
        ...


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

    def caption(self, match: MatchData, plan: CompilationPlan) -> str:
        ...


class Publisher(Protocol):
    """Publishes a compilation video to the Facebook Page."""

    def publish(self, video: Path, caption: str) -> str:
        """Publish and return the created post's id (or URL)."""
        ...
