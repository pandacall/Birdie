from birdie.gate import Rule, decide_posting_mode
from birdie.models import Category, PostingMode

from tests.conftest import make_clip, make_moment, make_plan


def _penta_plan() -> object:
    penta = make_moment(name="Multikill", score=20.0, kill_streak=5)
    return make_plan(
        clips=(make_clip(score=20.0, moments=(penta,)),),
        dominant_category=Category.EPIC,
    )


def test_pentakill_rule_auto_posts() -> None:
    rules = [Rule(kind="contains_multikill", mode=PostingMode.AUTO, min_streak=5)]

    assert decide_posting_mode(_penta_plan(), rules, PostingMode.REVIEW) == PostingMode.AUTO


def test_blooper_peak_routes_to_review() -> None:
    rules = [Rule(kind="peak_category", mode=PostingMode.REVIEW, category=Category.BLOOPER)]
    plan = make_plan(
        clips=(make_clip(category=Category.BLOOPER),),
        dominant_category=Category.BLOOPER,
    )

    assert decide_posting_mode(plan, rules, PostingMode.AUTO) == PostingMode.REVIEW


def test_default_applies_when_no_rule_matches() -> None:
    rules = [Rule(kind="contains_multikill", mode=PostingMode.AUTO, min_streak=5)]
    plan = make_plan()  # a single ordinary kill, no penta

    assert decide_posting_mode(plan, rules, PostingMode.REVIEW) == PostingMode.REVIEW


def test_first_matching_rule_wins() -> None:
    rules = [
        Rule(kind="min_score", mode=PostingMode.AUTO, min_score=10.0),
        Rule(kind="peak_category", mode=PostingMode.REVIEW, category=Category.EPIC),
    ]
    plan = make_plan(clips=(make_clip(score=20.0),), dominant_category=Category.EPIC)

    # both would match; the first (min_score -> auto) wins
    assert decide_posting_mode(plan, rules, PostingMode.REVIEW) == PostingMode.AUTO
