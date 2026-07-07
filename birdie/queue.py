"""The durable Review queue.

Backs the review web page (issue #6) and holds compilations awaiting a human
decision. Failed publishes are *parked* here rather than dropped (issue #7).
State is a single JSON index; the video files live on disk beside it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PENDING = "pending"


@dataclass(frozen=True)
class QueuedCompilation:
    id: str
    video: Path
    caption: str
    status: str  # pending | approved | discarded | parked
    reason: str | None = None


class ReviewQueue:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._index = root / "index.json"

    def add(
        self,
        video: Path,
        caption: str,
        status: str = _PENDING,
        reason: str | None = None,
    ) -> QueuedCompilation:
        items = self._load()
        record = {
            "id": video.stem,
            "video": str(video),
            "caption": caption,
            "status": status,
            "reason": reason,
        }
        items = [i for i in items if i["id"] != record["id"]]
        items.append(record)
        self._save(items)
        return _to_obj(record)

    def list_pending(self) -> list[QueuedCompilation]:
        return [_to_obj(i) for i in self._load() if i["status"] == _PENDING]

    def get(self, item_id: str) -> QueuedCompilation:
        for record in self._load():
            if record["id"] == item_id:
                return _to_obj(record)
        raise KeyError(item_id)

    def update_caption(self, item_id: str, caption: str) -> None:
        self._mutate(item_id, caption=caption)

    def approve(self, item_id: str) -> None:
        self._mutate(item_id, status="approved")

    def discard(self, item_id: str) -> None:
        self._mutate(item_id, status="discarded")

    def park(self, item_id: str, reason: str) -> None:
        self._mutate(item_id, status="parked", reason=reason)

    # -- internals -------------------------------------------------------

    def _mutate(self, item_id: str, **changes: Any) -> None:
        items = self._load()
        for record in items:
            if record["id"] == item_id:
                record.update(changes)
                break
        else:
            raise KeyError(item_id)
        self._save(items)

    def _load(self) -> list[dict[str, Any]]:
        if not self._index.exists():
            return []
        loaded: list[dict[str, Any]] = json.loads(self._index.read_text("utf-8"))
        return loaded

    def _save(self, items: list[dict[str, Any]]) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._index.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _to_obj(record: dict[str, Any]) -> QueuedCompilation:
    return QueuedCompilation(
        id=record["id"],
        video=Path(record["video"]),
        caption=record["caption"],
        status=record["status"],
        reason=record.get("reason"),
    )
