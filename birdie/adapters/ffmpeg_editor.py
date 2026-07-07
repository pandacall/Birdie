"""FFmpeg video editor adapter (implements the VideoEditor port).

Executes a CompilationPlan: cut each Window from the recording into a Clip,
normalise it to the OutputProfile's frame (scale + pad, preserving aspect — no
lossy crop for the 16:9 ``video`` profile), and concatenate the Clips into one
Compilation file.

Requires ``ffmpeg`` on PATH.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from birdie.models import CompilationPlan, OutputProfile, Window


class FfmpegEditor:
    def __init__(self, ffmpeg: str = "ffmpeg") -> None:
        self._ffmpeg = ffmpeg

    def render(
        self,
        recording: Path,
        plan: CompilationPlan,
        profile: OutputProfile,
        out: Path,
    ) -> Path:
        if not plan.windows:
            raise ValueError("CompilationPlan has no windows to render")
        out.parent.mkdir(parents=True, exist_ok=True)

        if len(plan.windows) == 1:
            self._cut(recording, plan.windows[0], profile, out)
            return out

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            clips = [
                self._cut(recording, w, profile, tmp / f"clip{i:03d}.mp4")
                for i, w in enumerate(plan.windows)
            ]
            self._concat(clips, out)
        return out

    def _cut(
        self, recording: Path, window: Window, profile: OutputProfile, dest: Path
    ) -> Path:
        w, h = profile.width, profile.height
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        )
        self._run(
            [
                self._ffmpeg, "-y",
                "-i", str(recording),
                "-ss", f"{window.start:.3f}",
                "-to", f"{window.end:.3f}",
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast",
                "-c:a", "aac",
                str(dest),
            ]
        )
        return dest

    def _concat(self, clips: list[Path], out: Path) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        ) as listing:
            for clip in clips:
                listing.write(f"file '{clip.as_posix()}'\n")
            list_path = Path(listing.name)
        try:
            self._run(
                [
                    self._ffmpeg, "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(list_path),
                    "-c", "copy",
                    str(out),
                ]
            )
        finally:
            list_path.unlink(missing_ok=True)

    def _run(self, cmd: list[str]) -> None:
        subprocess.run(cmd, check=True, capture_output=True)
