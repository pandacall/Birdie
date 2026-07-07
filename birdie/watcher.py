"""The during-game phase: watch the Live Client, drive recording, capture the
timeline anchor and the player-filtered event log, then hand a CompletedGame to
the post-game step.

The polling/sleeping is thin; the interesting logic (event filtering, dedup) is
in ``birdie.events`` and tested there. ``sleep`` is injectable so tests don't
wait.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from birdie.events import game_result, new_player_events
from birdie.models import CompletedGame, Event, TimelineAnchor
from birdie.ports import LiveClient, Recorder


class GameWatcher:
    def __init__(
        self,
        api: LiveClient,
        recorder: Recorder,
        on_game_end: Callable[[CompletedGame], None],
        poll_interval: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api = api
        self._recorder = recorder
        self._on_game_end = on_game_end
        self._poll = poll_interval
        self._sleep = sleep

    def watch_once(self) -> CompletedGame:
        """Block until a game starts, record it to completion, hand it off."""
        player = self._await_game_start()
        champion = self._api.active_champion()
        self._recorder.start()
        anchor = TimelineAnchor(
            recording_position=0.0, game_clock=self._api.game_time()
        )

        seen: set[int] = set()
        events: list[Event] = []
        result = "Unknown"
        while True:
            try:
                if self._api.active_player() is None:
                    break
                batch = self._api.event_dicts()
            except Exception:
                # The live client dropped mid-game — salvage: end the game and
                # process whatever was recorded/collected so far.
                break
            fresh = new_player_events(batch, player, seen)
            for event in fresh:
                seen.add(event.id)
            events.extend(fresh)
            found = game_result(batch)
            if found is not None:
                result = found
            self._sleep(self._poll)

        recording = self._recorder.stop()
        game = CompletedGame(
            recording=recording,
            events=tuple(events),
            anchor=anchor,
            player=player,
            champion=champion,
            result=result,
        )
        self._on_game_end(game)
        return game

    def _await_game_start(self) -> str:
        while True:
            player = self._api.active_player()
            if player is not None:
                return player
            self._sleep(self._poll)
