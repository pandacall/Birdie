from pathlib import Path

from birdie.queue import ReviewQueue
from birdie.review import ReviewService

from tests.fakes import FakePublisher


def _service(tmp_path: Path) -> tuple[ReviewService, ReviewQueue, FakePublisher]:
    queue = ReviewQueue(tmp_path / "q")
    publisher = FakePublisher(post_id="post-42")
    return ReviewService(queue, publisher), queue, publisher


def test_approve_publishes_current_caption_and_clears_pending(tmp_path: Path) -> None:
    service, queue, publisher = _service(tmp_path)
    item = queue.add(video=tmp_path / "a.mp4", caption="hello")

    post_id = service.approve(item.id)

    assert post_id == "post-42"
    assert publisher.calls[0] == (tmp_path / "a.mp4", "hello")
    assert queue.get(item.id).status == "approved"
    assert service.pending() == []


def test_edit_then_approve_publishes_edited_caption(tmp_path: Path) -> None:
    service, queue, publisher = _service(tmp_path)
    item = queue.add(video=tmp_path / "a.mp4", caption="draft")

    service.edit(item.id, "polished")
    service.approve(item.id)

    assert publisher.calls[0][1] == "polished"


def test_approve_parks_on_publish_failure(tmp_path: Path) -> None:
    queue = ReviewQueue(tmp_path / "q")
    publisher = FakePublisher(error=RuntimeError("401"))
    service = ReviewService(queue, publisher)
    item = queue.add(video=tmp_path / "a.mp4", caption="x")

    result = service.approve(item.id)

    assert result is None
    parked = queue.get(item.id)
    assert parked.status == "parked"
    assert "publish failed" in (parked.reason or "")


def test_discard_removes_without_publishing(tmp_path: Path) -> None:
    service, queue, publisher = _service(tmp_path)
    item = queue.add(video=tmp_path / "a.mp4", caption="x")

    service.discard(item.id)

    assert publisher.calls == []
    assert service.pending() == []
    assert queue.get(item.id).status == "discarded"
