from pathlib import Path

from birdie.eventlog import write_event_log
from birdie.gate import Rule
from birdie.ledger import ProcessedLedger
from birdie.models import CompletedGame, Event, PostingMode, TimelineAnchor
from birdie.postgame import process_game, recover_orphans, run_post_game
from birdie.queue import ReviewQueue

from tests.conftest import make_config
from tests.fakes import FakeCaptioner, FakeEditor, FakeExplodingEditor, FakePublisher

PLAYER = "Me#EUW"
ANCHOR = TimelineAnchor(0.0, 0.0)


def _penta_game(recording: Path) -> CompletedGame:
    return CompletedGame(
        recording=recording,
        events=(Event(1, "Multikill", 100.0, actor=PLAYER, kill_streak=5),),
        anchor=ANCHOR,
        player=PLAYER,
        champion="Katarina",
        result="Victory",
    )


def _auto_config(tmp_path: Path) -> object:
    return make_config(
        compilations_dir=tmp_path / "out",
        recordings_dir=tmp_path / "rec",
        rules=[Rule(kind="contains_multikill", mode=PostingMode.AUTO, min_streak=5)],
    )


def test_publish_failure_parks_the_compilation(tmp_path: Path) -> None:
    queue = ReviewQueue(tmp_path / "q")
    publisher = FakePublisher(error=RuntimeError("401 Unauthorized"))
    result = process_game(
        _penta_game(tmp_path / "g.mkv"),
        _auto_config(tmp_path),
        FakeEditor(),
        FakeCaptioner("cap"),
        publisher,
        queue,
    )

    parked = queue.get(result.queued_id or "")
    assert parked.status == "parked"
    assert "publish failed" in (parked.reason or "")


def test_reprocessing_is_idempotent_and_does_not_double_post(tmp_path: Path) -> None:
    queue = ReviewQueue(tmp_path / "q")
    publisher = FakePublisher()
    ledger = ProcessedLedger(tmp_path / "processed.json")
    args = (_auto_config(tmp_path), FakeEditor(), FakeCaptioner(), publisher, queue, ledger)

    run_post_game(_penta_game(tmp_path / "g.mkv"), *args)
    run_post_game(_penta_game(tmp_path / "g.mkv"), *args)  # re-run

    assert len(publisher.calls) == 1


def test_step_failure_parks_and_does_not_crash(tmp_path: Path) -> None:
    queue = ReviewQueue(tmp_path / "q")
    ledger = ProcessedLedger(tmp_path / "processed.json")

    result = run_post_game(
        _penta_game(tmp_path / "g.mkv"),
        _auto_config(tmp_path),
        FakeExplodingEditor(),
        FakeCaptioner(),
        FakePublisher(),
        queue,
        ledger,
    )

    assert result.video is None
    parked = queue.list_pending()  # parked items aren't "pending"
    assert parked == []
    all_parked = [
        i for i in [queue.get("g")] if i.status == "parked"
    ]
    assert all_parked and "ffmpeg boom" in (all_parked[0].reason or "")


def test_orphan_recovery_processes_logs_once(tmp_path: Path) -> None:
    cfg = _auto_config(tmp_path)
    cfg_recordings = cfg.recordings_dir  # type: ignore[attr-defined]
    for stem in ("game-a", "game-b"):
        write_event_log(
            cfg_recordings / f"{stem}.events.json",
            _penta_game(tmp_path / f"{stem}.mkv"),
        )

    queue = ReviewQueue(tmp_path / "q")
    publisher = FakePublisher()
    ledger = ProcessedLedger(tmp_path / "processed.json")
    deps = (FakeEditor(), FakeCaptioner(), publisher, queue, ledger)

    first = recover_orphans(cfg, *deps)
    second = recover_orphans(cfg, *deps)  # nothing left to do

    assert len(publisher.calls) == 2
    assert len([r for r in first if r.video is not None]) == 2
    assert second == []
