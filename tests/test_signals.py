from birdie.models import Category
from birdie.signals import compilation_signals

from tests.conftest import make_clip, make_moment, make_plan


def test_signals_report_highest_multikill() -> None:
    penta = make_moment(name="Multikill", score=20.0, kill_streak=5)
    clip = make_clip(score=20.0, category=Category.EPIC, moments=(penta,))
    plan = make_plan(clips=(clip,), dominant_category=Category.EPIC)

    signals = compilation_signals(plan)

    assert signals.max_multikill == 5


def test_signals_sum_clip_scores_and_carry_peak_category() -> None:
    plan = make_plan(
        clips=(
            make_clip(score=20.0, category=Category.EPIC),
            make_clip(score=5.0, category=Category.BLOOPER),
        ),
        dominant_category=Category.EPIC,
    )

    signals = compilation_signals(plan)

    assert signals.aggregate_score == 25.0
    assert signals.peak_category == Category.EPIC


def test_signals_zero_multikill_when_none_present() -> None:
    plan = make_plan()
    assert compilation_signals(plan).max_multikill == 0
