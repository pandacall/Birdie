from pathlib import Path

from birdie.gate import Rule
from birdie.models import CompletedGame, Event, PostingMode, TimelineAnchor
from birdie.postgame import process_game
from birdie.queue import ReviewQueue

from tests.conftest import make_config
from tests.fakes import FakeCaptioner, FakeEditor, FakePublisher

PLAYER = "Me#EUW"
ANCHOR = TimelineAnchor(0.0, 0.0)


def _game(events: tuple[Event, ...], recording: Path, **kw: object) -> CompletedGame:
    base = dict(recording=recording, events=events, anchor=ANCHOR, player=PLAYER)
    base.update(kw)
    return CompletedGame(**base)  # type: ignore[arg-type]


def _penta(id_: int, t: float) -> Event:
    return Event(id_, "Multikill", t, actor=PLAYER, kill_streak=5)


def test_auto_rule_publishes_without_queueing(tmp_path: Path) -> None:
    editor, captioner, publisher = FakeEditor(), FakeCaptioner("cap"), FakePublisher("post-1")
    queue = ReviewQueue(tmp_path / "q")
    cfg = make_config(
        compilations_dir=tmp_path / "out",
        rules=[Rule(kind="contains_multikill", mode=PostingMode.AUTO, min_streak=5)],
    )
    game = _game((_penta(1, 100.0),), tmp_path / "g.mkv", champion="Katarina", result="Victory")

    result = process_game(game, cfg, editor, captioner, publisher, queue)

    assert result.posting_mode == PostingMode.AUTO
    assert result.published_id == "post-1"
    assert publisher.calls and publisher.calls[0][1] == "cap"
    assert queue.list_pending() == []


def test_review_default_queues_without_publishing(tmp_path: Path) -> None:
    editor, captioner, publisher = FakeEditor(), FakeCaptioner("cap"), FakePublisher()
    queue = ReviewQueue(tmp_path / "q")
    cfg = make_config(compilations_dir=tmp_path / "out")  # default_mode = review
    game = _game(
        (Event(1, "ChampionKill", 100.0, actor=PLAYER, victim="X"),),
        tmp_path / "g.mkv",
        champion="Katarina",
        result="Victory",
    )

    result = process_game(game, cfg, editor, captioner, publisher, queue)

    assert result.posting_mode == PostingMode.REVIEW
    assert publisher.calls == []
    pending = queue.list_pending()
    assert len(pending) == 1 and pending[0].caption == "cap"


def test_no_scorable_events_produces_nothing(tmp_path: Path) -> None:
    editor, captioner, publisher = FakeEditor(), FakeCaptioner(), FakePublisher()
    queue = ReviewQueue(tmp_path / "q")
    cfg = make_config(compilations_dir=tmp_path / "out")
    game = _game((Event(1, "MinionsSpawning", 65.0),), tmp_path / "g.mkv")

    result = process_game(game, cfg, editor, captioner, publisher, queue)

    assert result.video is None
    assert editor.calls == [] and publisher.calls == [] and queue.list_pending() == []
