"""Map Riot game-time onto the recording clock via the timeline anchor."""

from __future__ import annotations

from birdie.models import TimelineAnchor


def to_recording_offset(anchor: TimelineAnchor, game_time: float) -> float:
    """Recording-timeline position (seconds) for a given game-time.

    Clamped to zero: nothing can sit before the start of the recording.
    """
    offset = anchor.recording_position + (game_time - anchor.game_clock)
    return max(0.0, offset)
