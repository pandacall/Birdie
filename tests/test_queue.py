from pathlib import Path

from birdie.queue import ReviewQueue


def test_added_compilation_is_listed_as_pending(tmp_path: Path) -> None:
    q = ReviewQueue(tmp_path / "queue")

    item = q.add(video=tmp_path / "katarina.mp4", caption="gg")

    assert item.status == "pending"
    assert [i.id for i in q.list_pending()] == [item.id]
    assert q.get(item.id).caption == "gg"


def test_discard_removes_from_pending(tmp_path: Path) -> None:
    q = ReviewQueue(tmp_path / "queue")
    item = q.add(video=tmp_path / "a.mp4", caption="x")

    q.discard(item.id)

    assert q.list_pending() == []
    assert q.get(item.id).status == "discarded"


def test_edit_caption_then_approve(tmp_path: Path) -> None:
    q = ReviewQueue(tmp_path / "queue")
    item = q.add(video=tmp_path / "a.mp4", caption="draft")

    q.update_caption(item.id, "final caption")
    q.approve(item.id)

    approved = q.get(item.id)
    assert approved.caption == "final caption"
    assert approved.status == "approved"
    assert q.list_pending() == []


def test_park_records_reason_and_persists_across_instances(tmp_path: Path) -> None:
    root = tmp_path / "queue"
    ReviewQueue(root).add(video=tmp_path / "a.mp4", caption="x")

    q1 = ReviewQueue(root)
    (item,) = q1.list_pending()
    q1.park(item.id, reason="expired token")

    # a fresh instance reads the same durable store
    reopened = ReviewQueue(root).get(item.id)
    assert reopened.status == "parked"
    assert reopened.reason == "expired token"
