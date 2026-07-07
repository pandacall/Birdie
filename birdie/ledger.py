"""A durable set of processed game ids, for idempotency and orphan recovery.

Keyed by game id (the recording stem). Ensures a re-run — after a crash, or from
orphan recovery — never processes (or publishes) the same game twice.
"""

from __future__ import annotations

import json
from pathlib import Path


class ProcessedLedger:
    def __init__(self, path: Path) -> None:
        self._path = path

    def contains(self, game_id: str) -> bool:
        return game_id in self._load()

    def mark(self, game_id: str) -> None:
        ids = self._load()
        ids.add(game_id)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(sorted(ids)), encoding="utf-8")

    def _load(self) -> set[str]:
        if not self._path.exists():
            return set()
        return set(json.loads(self._path.read_text("utf-8")))
