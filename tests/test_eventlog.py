from pathlib import Path

from birdie.eventlog import read_event_log, write_event_log
from birdie.models import CompletedGame, Event, TimelineAnchor


def test_event_log_round_trips(tmp_path: Path) -> None:
    game = CompletedGame(
        recording=tmp_path / "2026-07-07.mkv",
        events=(
            Event(1, "ChampionKill", 10.0, actor="Me#EUW", victim="X"),
            Event(2, "Multikill", 12.0, actor="Me#EUW", kill_streak=2),
            Event(3, "ChampionKill", 20.0, actor="Z", victim="Me#EUW",
                  assisters=("Ally#EUW",)),
        ),
        anchor=TimelineAnchor(recording_position=0.0, game_clock=100.0),
        player="Me#EUW",
    )
    path = tmp_path / "log.json"

    write_event_log(path, game)
    restored = read_event_log(path)

    assert restored == game
