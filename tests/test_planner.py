import pytest

from birdie.models import Category, CompletedGame, Event, PostingMode, TimelineAnchor
from birdie.planner import plan_compilation

from tests.conftest import make_config

PLAYER = "Me#EUW"
# Anchor at (0, 0) so a game-time t maps to recording offset t; windows are
# [t - window_pre, t + window_post] = [t-8, t+4].
ANCHOR = TimelineAnchor(recording_position=0.0, game_clock=0.0)


def _game(*events: Event) -> CompletedGame:
    return CompletedGame(
        recording=__import__("pathlib").Path("game.mkv"),
        events=events,
        anchor=ANCHOR,
        player=PLAYER,
    )


def _kill(id_: int, t: float) -> Event:
    return Event(id_, "ChampionKill", t, actor=PLAYER, victim="X")


def _death(id_: int, t: float) -> Event:
    return Event(id_, "ChampionKill", t, actor="Z", victim=PLAYER)


def _multi(id_: int, t: float, streak: int) -> Event:
    return Event(id_, "Multikill", t, actor=PLAYER, kill_streak=streak)


def test_adjacent_moments_merge_into_one_clip() -> None:
    plan = plan_compilation(_game(_kill(1, 100.0), _kill(2, 105.0)), make_config())

    assert len(plan.clips) == 1
    clip = plan.clips[0]
    assert clip.window.start == 92.0 and clip.window.end == 109.0
    assert len(clip.moments) == 2


def test_far_apart_moments_stay_separate_and_are_chronological() -> None:
    plan = plan_compilation(_game(_kill(1, 200.0), _kill(2, 100.0)), make_config())

    assert len(plan.clips) == 2
    assert [c.window.start for c in plan.clips] == [92.0, 192.0]


def test_death_clip_is_blooper() -> None:
    plan = plan_compilation(_game(_death(1, 100.0)), make_config())

    assert plan.clips[0].category == Category.BLOOPER
    assert plan.dominant_category == Category.BLOOPER


def test_clip_aggregate_uses_diminishing_returns() -> None:
    # two merged kills: 1.0 + 1.0*0.7
    plan = plan_compilation(_game(_kill(1, 100.0), _kill(2, 104.0)), make_config())

    assert plan.clips[0].score == pytest.approx(1.7)


def test_selection_fills_to_length_budget_by_score() -> None:
    # each clip is 12s; budget 25 fits two; the two highest-scored win
    cfg = make_config(length_budget=25.0)
    plan = plan_compilation(
        _game(
            _multi(1, 100.0, 5),   # penta 20
            _multi(2, 300.0, 4),   # quadra 10
            _kill(3, 500.0),       # 1
        ),
        cfg,
    )

    assert len(plan.clips) == 2
    kept = {c.moments[0].event.id for c in plan.clips}
    assert kept == {1, 2}


def test_one_clip_game_still_produces_a_compilation() -> None:
    cfg = make_config(length_budget=0.0)  # nothing "fits"
    plan = plan_compilation(_game(_kill(1, 100.0)), cfg)

    assert len(plan.clips) == 1  # guarantee floor


def test_reserved_blooper_slot_swaps_in_top_blooper() -> None:
    cfg = make_config(length_budget=25.0)  # fits two clips
    plan = plan_compilation(
        _game(
            _multi(1, 100.0, 5),   # penta 20 (epic)
            _multi(2, 300.0, 4),   # quadra 10 (epic)
            _kill(3, 500.0),       # 1 (epic)
            _death(4, 700.0),      # 1 (blooper)
        ),
        cfg,
    )

    categories = {c.category for c in plan.clips}
    assert Category.BLOOPER in categories  # a blooper was reserved a slot
    assert len(plan.clips) == 2


def test_posting_mode_defaults_to_review() -> None:
    plan = plan_compilation(_game(_kill(1, 100.0)), make_config())
    assert plan.posting_mode == PostingMode.REVIEW
