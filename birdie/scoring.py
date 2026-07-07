"""Score a single Event into a Moment (or None if it doesn't count).

Pure: base scores come from the caller's config table. A death scores
positively and routes to the blooper Category — it is content, not a penalty.
"""

from __future__ import annotations

from birdie.models import Category, Event, Moment

_STREAK_KEY = {2: "double", 3: "triple", 4: "quadra", 5: "penta"}

# Objective / special events scored when the player is the actor.
_ACTOR_EVENTS = frozenset(
    {"FirstBlood", "Ace", "DragonKill", "BaronKill", "HeraldKill",
     "TurretKilled", "InhibKilled"}
)


def score_event(event: Event, player: str, scores: dict[str, float]) -> Moment | None:
    if event.name == "ChampionKill":
        if event.actor == player:
            return Moment(event, scores["kill"], Category.EPIC)
        if event.victim == player:
            return Moment(event, scores["death"], Category.BLOOPER)
        if player in event.assisters:
            return Moment(event, scores["assist"], Category.EPIC)
        return None

    if event.name == "Multikill" and event.actor == player:
        key = _STREAK_KEY.get(event.kill_streak or 5, "penta")
        return Moment(event, scores[key], Category.EPIC)

    if event.name in _ACTOR_EVENTS and event.actor == player:
        return Moment(event, scores.get(event.name, 1.0), Category.EPIC)

    return None
