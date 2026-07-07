"""In-memory fakes for the adapter ports, used across pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from birdie.models import Category, CompilationPlan, MatchData, OutputProfile


class FakeLiveClient:
    """Scripted Live Client: ``active_seq`` is consumed one value per
    ``active_player()`` call; ``event_polls`` one batch per ``event_dicts()``."""

    def __init__(
        self,
        active_seq: list[str | None],
        event_polls: list[list[dict[str, Any]]] | None = None,
        game_time: float = 100.0,
    ) -> None:
        self._active = list(active_seq)
        self._polls = list(event_polls or [])
        self._game_time = game_time
        self._i_active = 0
        self._i_polls = 0

    def active_player(self) -> str | None:
        value = self._active[self._i_active]
        self._i_active += 1
        return value

    def game_time(self) -> float:
        return self._game_time

    def event_dicts(self) -> list[dict[str, Any]]:
        if self._i_polls < len(self._polls):
            batch = self._polls[self._i_polls]
            self._i_polls += 1
            return batch
        return []


class FakeRecorder:
    def __init__(self, recording: Path, log: list[str] | None = None) -> None:
        self._recording = recording
        self._log = log
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True
        if self._log is not None:
            self._log.append("start")

    def stop(self) -> Path:
        self.stopped = True
        self._recording.write_bytes(b"fake-recording")
        if self._log is not None:
            self._log.append("stop")
        return self._recording


class FakeEditor:
    def __init__(self, log: list[str] | None = None) -> None:
        self._log = log
        self.calls: list[tuple[Path, CompilationPlan, OutputProfile, Path]] = []

    def render(
        self,
        recording: Path,
        plan: CompilationPlan,
        profile: OutputProfile,
        out: Path,
    ) -> Path:
        self.calls.append((recording, plan, profile, out))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"fake-compilation")
        if self._log is not None:
            self._log.append("render")
        return out


class FakeCaptioner:
    def __init__(self, text: str = "CAPTION", log: list[str] | None = None) -> None:
        self.text = text
        self._log = log
        self.calls: list[tuple[MatchData, Category]] = []

    def caption(self, match: MatchData, dominant_category: Category) -> str:
        self.calls.append((match, dominant_category))
        if self._log is not None:
            self._log.append("caption")
        return self.text


class FakePublisher:
    def __init__(self, post_id: str = "post-123", log: list[str] | None = None) -> None:
        self.post_id = post_id
        self._log = log
        self.calls: list[tuple[Path, str]] = []

    def publish(self, video: Path, caption: str) -> str:
        self.calls.append((video, caption))
        if self._log is not None:
            self._log.append("publish")
        return self.post_id
