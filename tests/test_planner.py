from birdie.models import Category, PostingMode, Window
from birdie.planner import plan_compilation

from tests.conftest import make_config, make_match


def test_skeleton_plan_uses_configured_window() -> None:
    cfg = make_config(skeleton_window=Window(10.0, 25.0))

    plan = plan_compilation(event_log=[], match=make_match(), config=cfg)

    assert plan.windows == (Window(10.0, 25.0),)
    assert plan.posting_mode == PostingMode.REVIEW
    assert plan.dominant_category == Category.EPIC
