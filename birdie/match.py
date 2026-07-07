"""Derive MatchData (the caption's facts) from a CompletedGame.

KDA is counted from the player-filtered event log; champion and result are
captured live and carried on the game.
"""

from __future__ import annotations

from birdie.models import CompletedGame, MatchData


def match_from_game(game: CompletedGame) -> MatchData:
    kills = deaths = assists = 0
    for event in game.events:
        if event.name != "ChampionKill":
            continue
        if event.actor == game.player:
            kills += 1
        elif event.victim == game.player:
            deaths += 1
        elif game.player in event.assisters:
            assists += 1

    duration = max((e.game_time for e in game.events), default=0.0)
    return MatchData(
        champion=game.champion,
        kills=kills,
        deaths=deaths,
        assists=assists,
        result=game.result,
        duration_seconds=duration,
    )
