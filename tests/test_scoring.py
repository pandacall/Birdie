from birdie.config import _DEFAULT_SCORES
from birdie.models import Category, Event
from birdie.scoring import score_event

PLAYER = "Me#EUW"
S = _DEFAULT_SCORES


def _ck(**kw: object) -> Event:
    base = dict(id=1, name="ChampionKill", game_time=10.0)
    base.update(kw)
    return Event(**base)  # type: ignore[arg-type]


def test_player_kill_is_epic() -> None:
    moment = score_event(_ck(actor=PLAYER, victim="X"), PLAYER, S)
    assert moment is not None
    assert moment.category == Category.EPIC
    assert moment.score == S["kill"]


def test_player_death_is_blooper_not_a_penalty() -> None:
    moment = score_event(_ck(actor="Z", victim=PLAYER), PLAYER, S)
    assert moment is not None
    assert moment.category == Category.BLOOPER
    assert moment.score == S["death"]
    assert moment.score > 0  # a death is content, scored positively


def test_player_assist_is_epic() -> None:
    moment = score_event(_ck(actor="W", victim="V", assisters=(PLAYER,)), PLAYER, S)
    assert moment is not None
    assert moment.category == Category.EPIC
    assert moment.score == S["assist"]


def test_multikill_scores_by_streak() -> None:
    triple = Event(2, "Multikill", 20.0, actor=PLAYER, kill_streak=3)
    moment = score_event(triple, PLAYER, S)
    assert moment is not None
    assert moment.score == S["triple"]
    assert moment.category == Category.EPIC


def test_objective_by_player_is_epic() -> None:
    dragon = Event(3, "DragonKill", 400.0, actor=PLAYER)
    moment = score_event(dragon, PLAYER, S)
    assert moment is not None
    assert moment.score == S["DragonKill"]


def test_events_not_involving_player_or_unscored_return_none() -> None:
    assert score_event(_ck(actor="A", victim="B"), PLAYER, S) is None
    assert score_event(Event(4, "MinionsSpawning", 65.0), PLAYER, S) is None
