"""Review service: the logic behind the review web page.

Wraps the durable ReviewQueue and the Publisher so the web layer stays a thin
adapter. Approving publishes the queued compilation with its current caption.
"""

from __future__ import annotations

from birdie.ports import Publisher
from birdie.queue import QueuedCompilation, ReviewQueue


class ReviewService:
    def __init__(self, queue: ReviewQueue, publisher: Publisher) -> None:
        self._queue = queue
        self._publisher = publisher

    def pending(self) -> list[QueuedCompilation]:
        return self._queue.list_pending()

    def get(self, item_id: str) -> QueuedCompilation:
        return self._queue.get(item_id)

    def edit(self, item_id: str, caption: str) -> None:
        self._queue.update_caption(item_id, caption)

    def discard(self, item_id: str) -> None:
        self._queue.discard(item_id)

    def approve(self, item_id: str) -> str:
        item = self._queue.get(item_id)
        post_id = self._publisher.publish(item.video, item.caption)
        self._queue.approve(item_id)
        return post_id
