from birdie.models import TimelineAnchor
from birdie.timeline import to_recording_offset


def test_offset_maps_game_time_through_the_anchor() -> None:
    anchor = TimelineAnchor(recording_position=2.0, game_clock=100.0)

    # An event 30s of game-time after the anchor sits 30s further into the
    # recording than the anchor's recording position.
    assert to_recording_offset(anchor, 130.0) == 32.0


def test_offset_clamps_to_zero_before_anchor() -> None:
    anchor = TimelineAnchor(recording_position=0.0, game_clock=100.0)

    assert to_recording_offset(anchor, 90.0) == 0.0
