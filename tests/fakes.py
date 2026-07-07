"""In-memory fakes for the adapter ports, used across pipeline tests."""

from __future__ import annotations

from pathlib import Path

from birdie.models import Category, CompilationPlan, MatchData, OutputProfile


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
