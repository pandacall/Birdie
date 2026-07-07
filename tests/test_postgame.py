from pathlib import Path

from birdie.models import CompletedGame, Event, TimelineAnchor
from birdie.postgame import process_game

from tests.conftest import make_config
from tests.fakes import FakeEditor

PLAYER = "Me#EUW"
ANCHOR = TimelineAnchor(0.0, 0.0)


def _game(events: tuple[Event, ...], recording: Path) -> CompletedGame:
    return CompletedGame(recording=recording, events=events, anchor=ANCHOR, player=PLAYER)


def test_process_game_renders_a_compilation_from_the_plan(tmp_path: Path) -> None:
    editor = FakeEditor()
    cfg = make_config(compilations_dir=tmp_path / "out")
    game = _game(
        (
            Event(1, "ChampionKill", 100.0, actor=PLAYER, victim="X"),
            Event(2, "ChampionKill", 300.0, actor=PLAYER, victim="Y"),
        ),
        tmp_path / "2026.mkv",
    )

    out = process_game(game, cfg, editor)

    assert out is not None and out.exists()
    (recording, plan, profile, dest) = editor.calls[0]
    assert recording == game.recording
    assert len(plan.clips) == 2
    assert dest.parent == tmp_path / "out"


def test_process_game_skips_when_no_scorable_events(tmp_path: Path) -> None:
    editor = FakeEditor()
    cfg = make_config(compilations_dir=tmp_path / "out")
    game = _game((Event(1, "MinionsSpawning", 65.0),), tmp_path / "2026.mkv")

    out = process_game(game, cfg, editor)

    assert out is None
    assert editor.calls == []
