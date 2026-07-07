"""Domain models for the Birdie pipeline.

Vocabulary follows CONTEXT.md: event -> moment -> window -> clip -> compilation.
This module holds pure data; behaviour lives in the pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    """A per-Clip tag describing the kind of moment."""

    EPIC = "epic"
    BLOOPER = "blooper"


class PostingMode(str, Enum):
    """How a Compilation reaches the Page."""

    AUTO = "auto"
    REVIEW = "review"


@dataclass(frozen=True)
class OutputProfile:
    """Target shape of the published video: aspect ratio + length rules.

    The MVP ships one profile, ``video`` (16:9, no length cap). See ADR 0001.
    """

    name: str
    width: int
    height: int
    max_seconds: float | None = None


@dataclass(frozen=True)
class Event:
    """A single raw occurrence read from the Riot Live Client Data API."""

    name: str
    game_time: float


@dataclass(frozen=True)
class Window:
    """A time span on the recording timeline that will be cut from the footage."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class MatchData:
    """Facts about a game, sourced from Riot data — the basis for a Caption."""

    champion: str
    kills: int
    deaths: int
    assists: int
    result: str  # "Victory" | "Defeat"
    duration_seconds: float


@dataclass(frozen=True)
class CompilationPlan:
    """The pure output of the planner: which Windows to cut, in order, plus the
    gating decision and the dominant Category (which drives caption tone).

    The Caption *text* is produced separately by a Captioner seam operating on
    this plan, so the template/LLM captioner stays swappable.
    """

    windows: tuple[Window, ...]
    posting_mode: PostingMode
    dominant_category: Category
