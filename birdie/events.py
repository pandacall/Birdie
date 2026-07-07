"""Pure event processing: parse Riot Live Client event dicts into Events and
filter a batch down to new events involving the active player.

Kept free of I/O so it is exhaustively testable; the HTTP polling lives in the
live-client adapter.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from birdie.models import Event

# Riot spreads "who did it" across differently-named fields per event type.
_ACTOR_FIELDS = ("KillerName", "Recipient", "Acer")


def parse_event(raw: dict[str, Any]) -> Event | None:
    """Convert one Riot event dict into an Event, or None if it lacks an id."""
    if "EventID" not in raw or "EventName" not in raw:
        return None

    actor: str | None = None
    for source in _ACTOR_FIELDS:
        if raw.get(source):
            actor = str(raw[source])
            break

    victim = raw.get("VictimName")
    assisters = tuple(raw.get("Assisters", ()) or ())
    kill_streak = raw.get("KillStreak")

    return Event(
        id=int(raw["EventID"]),
        name=str(raw["EventName"]),
        game_time=float(raw.get("EventTime", 0.0)),
        actor=str(actor) if actor is not None else None,
        victim=str(victim) if victim is not None else None,
        assisters=tuple(str(a) for a in assisters),
        kill_streak=int(kill_streak) if kill_streak is not None else None,
    )


def is_player_involved(event: Event, player: str) -> bool:
    return player in (event.actor, event.victim) or player in event.assisters


def game_result(batch: Iterable[dict[str, Any]]) -> str | None:
    """Read Victory/Defeat from a GameEnd event in the raw batch, or None."""
    for raw in batch:
        if raw.get("EventName") == "GameEnd":
            return "Victory" if raw.get("Result") == "Win" else "Defeat"
    return None


def new_player_events(
    batch: Iterable[dict[str, Any]],
    player: str,
    seen_ids: set[int],
) -> list[Event]:
    """Parse a raw event batch, keeping only events that involve the player and
    whose ids have not been seen before (in batch order)."""
    fresh: list[Event] = []
    for raw in batch:
        event = parse_event(raw)
        if event is None or event.id in seen_ids:
            continue
        if is_player_involved(event, player):
            fresh.append(event)
    return fresh
