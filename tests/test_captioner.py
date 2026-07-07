from birdie.captioner import TemplateCaptioner
from birdie.models import Category

from tests.conftest import make_match


def test_caption_states_champion_kda_and_result() -> None:
    caption = TemplateCaptioner().caption(make_match(), Category.EPIC)

    assert "Katarina" in caption
    assert "18/3/7" in caption
    assert "Victory" in caption
