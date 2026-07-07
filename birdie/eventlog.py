"""Persist a CompletedGame's event log to disk and read it back.

Written when a game ends; read by orphan recovery (issue #7). The recording
path is stored so a crashed run can resume post-game processing from the log
alone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from birdie.models import CompletedGame, Event, TimelineAnchor


def _event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "name": event.name,
        "game_time": event.game_time,
        "actor": event.actor,
        "victim": event.victim,
        "assisters": list(event.assisters),
        "kill_streak": event.kill_streak,
    }


def _event_from_dict(raw: dict[str, Any]) -> Event:
    return Event(
        id=raw["id"],
        name=raw["name"],
        game_time=raw["game_time"],
        actor=raw["actor"],
        victim=raw["victim"],
        assisters=tuple(raw["assisters"]),
        kill_streak=raw["kill_streak"],
    )


def write_event_log(path: Path, game: CompletedGame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recording": str(game.recording),
        "player": game.player,
        "champion": game.champion,
        "result": game.result,
        "anchor": {
            "recording_position": game.anchor.recording_position,
            "game_clock": game.anchor.game_clock,
        },
        "events": [_event_to_dict(e) for e in game.events],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_event_log(path: Path) -> CompletedGame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return CompletedGame(
        recording=Path(payload["recording"]),
        events=tuple(_event_from_dict(e) for e in payload["events"]),
        anchor=TimelineAnchor(
            recording_position=payload["anchor"]["recording_position"],
            game_clock=payload["anchor"]["game_clock"],
        ),
        player=payload["player"],
        champion=payload.get("champion", "Unknown"),
        result=payload.get("result", "Unknown"),
    )
