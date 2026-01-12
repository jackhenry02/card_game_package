"""Achievement definitions for the infinite game."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AchievementDefinition:
    """Defines a single achievement."""

    key: str
    name: str
    description: str


class AchievementCatalog:
    """Catalog of all supported achievements."""

    DEFINITIONS = (
        AchievementDefinition(
            key="first_deck",
            name="First time?",
            description="Complete your first deck.",
        ),
        AchievementDefinition(
            key="win_streak_5",
            name="Winning streak",
            description="Win 5 rounds in a row.",
        ),
        AchievementDefinition(
            key="win_streak_10",
            name="On fire",
            description="Win 10 rounds in a row.",
        ),
        AchievementDefinition(
            key="statistical_anomaly",
            name="Statistical Anomaly",
            description="Win a round with <10% odds.",
        ),
        AchievementDefinition(
            key="market_manipulator",
            name="Market manipulator",
            description="Max out every shop upgrade.",
        ),
        AchievementDefinition(
            key="long_haul",
            name="In it for the long haul",
            description="Complete 5 decks.",
        ),
        AchievementDefinition(
            key="vault_breaker",
            name="Vault breaker",
            description="Reach 100 million credits.",
        ),
        AchievementDefinition(
            key="first_purchase",
            name="First purchase",
            description="Buy your first upgrade.",
        ),
        AchievementDefinition(
            key="shadow_operator",
            name="Shadow operator",
            description="Complete a side mission successfully.",
        ),
        AchievementDefinition(
            key="high_roller",
            name="High roller",
            description="Reach 1 million credits.",
        ),
    )

    @classmethod
    def default_state(cls) -> dict[str, bool]:
        """Return the default locked state for all achievements."""
        return {definition.key: False for definition in cls.DEFINITIONS}

    @classmethod
    def merge_state(cls, stored: dict[str, object]) -> dict[str, bool]:
        """Merge stored achievement state into defaults.

        Args:
            stored: Raw achievement state loaded from storage.

        Returns:
            Normalized dictionary of achievement states.
        """
        state = cls.default_state()
        for key, value in stored.items():
            if key in state:
                state[key] = bool(value)
        return state
