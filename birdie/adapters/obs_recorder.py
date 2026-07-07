"""OBS recorder adapter (implements the Recorder port) via obs-websocket.

Assumes OBS is already running with obs-websocket enabled and a capture scene
configured (ADR: assume-OBS-running for the MVP). Records the full game to a
single file; ``stop`` returns the path OBS wrote.
"""

from __future__ import annotations

from pathlib import Path

import obsws_python as obs


class ObsRecorder:
    def __init__(self, host: str, port: int, password: str, timeout: float = 5.0) -> None:
        self._client = obs.ReqClient(
            host=host, port=port, password=password, timeout=timeout
        )

    def start(self) -> None:
        self._client.start_record()

    def stop(self) -> Path:
        resp = self._client.stop_record()
        return Path(resp.output_path)
