from pathlib import Path

from birdie.models import CompletedGame
from birdie.watcher import GameWatcher

from tests.fakes import FakeLiveClient, FakeRecorder


def _kill(id_: int, killer: str, victim: str, t: float) -> dict[str, object]:
    return {
        "EventID": id_,
        "EventName": "ChampionKill",
        "EventTime": t,
        "KillerName": killer,
        "VictimName": victim,
    }


def test_watcher_records_from_start_to_end_and_hands_off(tmp_path: Path) -> None:
    player = "Me#EUW"
    api = FakeLiveClient(
        # await: None (wait) -> player (start); loop: player, player, None (end)
        active_seq=[None, player, player, player, None],
        # cumulative event lists, as Riot returns them
        event_polls=[
            [_kill(1, player, "X", 10.0)],
            [_kill(1, player, "X", 10.0), _kill(2, "Z", player, 20.0)],
        ],
        game_time=100.0,
    )
    recorder = FakeRecorder(tmp_path / "game.mkv")
    captured: list[CompletedGame] = []

    watcher = GameWatcher(
        api=api,
        recorder=recorder,
        on_game_end=captured.append,
        sleep=lambda _seconds: None,
    )
    game = watcher.watch_once()

    assert recorder.started and recorder.stopped
    assert game is not None
    assert captured == [game]
    assert game.player == player
    assert game.recording == tmp_path / "game.mkv"
    # anchor pins the game clock at recording start
    assert game.anchor.game_clock == 100.0
    # cumulative polls deduped to two distinct player-involved events
    assert [e.id for e in game.events] == [1, 2]


def test_watcher_only_logs_events_involving_the_player(tmp_path: Path) -> None:
    player = "Me#EUW"
    api = FakeLiveClient(
        active_seq=[player, player, None],
        event_polls=[
            [_kill(1, "Rando", "Other", 5.0), _kill(2, player, "X", 8.0)],
        ],
    )
    watcher = GameWatcher(
        api=api,
        recorder=FakeRecorder(tmp_path / "g.mkv"),
        on_game_end=lambda _g: None,
        sleep=lambda _s: None,
    )

    game = watcher.watch_once()

    assert game is not None
    assert [e.id for e in game.events] == [2]
