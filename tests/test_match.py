from pathlib import Path

from birdie.match import match_from_game
from birdie.models import CompletedGame, Event, TimelineAnchor

PLAYER = "Me#EUW"


def test_kda_is_counted_from_events_and_facts_carried() -> None:
    events = (
        Event(1, "ChampionKill", 100.0, actor=PLAYER, victim="A"),
        Event(2, "ChampionKill", 110.0, actor=PLAYER, victim="B"),
        Event(3, "ChampionKill", 200.0, actor="Z", victim=PLAYER),
        Event(4, "ChampionKill", 300.0, actor="W", victim="V", assisters=(PLAYER,)),
    )
    game = CompletedGame(
        recording=Path("g.mkv"),
        events=events,
        anchor=TimelineAnchor(0.0, 0.0),
        player=PLAYER,
        champion="Katarina",
        result="Victory",
    )

    match = match_from_game(game)

    assert (match.kills, match.deaths, match.assists) == (2, 1, 1)
    assert match.champion == "Katarina"
    assert match.result == "Victory"
    assert match.duration_seconds == 300.0
