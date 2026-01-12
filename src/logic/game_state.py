"""Game state enumeration for the infinite card game."""
from __future__ import annotations

from enum import Enum


class GameState(Enum):
    """Represents the current phase of the infinite game."""

    STARTUP = "startup"
    DEALING = "dealing"
    SHOPPING = "shopping"
    SETTINGS = "settings"
    ACHIEVEMENTS = "achievements"
    TERMINATED = "terminated"
