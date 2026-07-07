from birdie.captioner import TemplateCaptioner
from birdie.models import Category

from tests.conftest import make_clip, make_match, make_moment, make_plan


def test_caption_states_champion_kda_and_result() -> None:
    caption = TemplateCaptioner().caption(make_match(), make_plan())

    assert "Katarina" in caption
    assert "18/3/7" in caption
    assert "Victory" in caption


def test_epic_dominant_caption_is_hype() -> None:
    plan = make_plan(dominant_category=Category.EPIC)
    caption = TemplateCaptioner().caption(make_match(), plan)
    assert "🔥" in caption


def test_blooper_dominant_caption_is_self_deprecating() -> None:
    plan = make_plan(
        clips=(make_clip(category=Category.BLOOPER),),
        dominant_category=Category.BLOOPER,
    )
    caption = TemplateCaptioner().caption(make_match(result="Defeat"), plan)
    assert "proudest" in caption.lower()


def test_caption_has_core_and_champion_hashtags() -> None:
    caption = TemplateCaptioner().caption(make_match(champion="Miss Fortune"), make_plan())

    assert "#LeagueOfLegends" in caption
    assert "#LoL" in caption
    assert "#MissFortune" in caption  # spaces stripped


def test_pentakill_adds_event_hashtag() -> None:
    penta = make_moment(name="Multikill", score=20.0, kill_streak=5)
    plan = make_plan(clips=(make_clip(score=20.0, moments=(penta,)),))

    caption = TemplateCaptioner().caption(make_match(), plan)

    assert "#Pentakill" in caption
