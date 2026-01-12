"""Side mission definitions and state handling."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random


class SideMissionType(Enum):
    """Supported side mission types."""

    DOUBLE_OR_NOTHING = "double_or_nothing"
    BIG_MONEY = "big_money"
    LUCKY_SEVEN = "lucky_seven"
    GONE_BLIND = "gone_blind"
    REVERSE_PSYCHOLOGY = "reverse_psychology"


@dataclass(frozen=True)
class SideMissionDefinition:
    """Defines the behavior of a side mission."""

    kind: SideMissionType
    title: str
    description: tuple[str, ...]
    rounds: int = 0
    wins_required: int = 0
    bonus_multiplier: int = 1
    reverse_logic: bool = False
    blind_rounds: int = 0
    skip_penalty_ratio: float | None = None


@dataclass
class SideMissionState:
    """Tracks an active side mission."""

    definition: SideMissionDefinition
    rounds_left: int
    wins_in_row: int = 0
    active: bool = True
    completed: bool = False
    failed: bool = False

    def is_blind(self) -> bool:
        """Return True when the mission requires blind rounds."""
        return self.definition.blind_rounds > 0 and self.rounds_left > 0

    def is_reverse(self) -> bool:
        """Return True when the mission reverses win logic."""
        return self.definition.reverse_logic and self.rounds_left > 0


class SideMissionManager:
    """Creates and provides side missions."""

    _DEFINITIONS = (
        SideMissionDefinition(
            kind=SideMissionType.DOUBLE_OR_NOTHING,
            title="DOUBLE OR NOTHING",
            description=(
                "Win 3 rounds in a row to double your balance.",
                "Fail and you just carry on as normal.",
            ),
            wins_required=3,
        ),
        SideMissionDefinition(
            kind=SideMissionType.BIG_MONEY,
            title="BIG MONEY",
            description=("Your next win pays 5x.",),
            rounds=1,
            bonus_multiplier=5,
        ),
        SideMissionDefinition(
            kind=SideMissionType.LUCKY_SEVEN,
            title="LUCKY SEVEN",
            description=(
                "Next 7 rounds pay triple.",
                "First loss ends the bonus early.",
            ),
            rounds=7,
            bonus_multiplier=3,
        ),
        SideMissionDefinition(
            kind=SideMissionType.GONE_BLIND,
            title="GONE BLIND",
            description=(
                "Next 3 rounds you play blind.",
                "Pay 10% of balance to skip.",
            ),
            rounds=3,
            blind_rounds=3,
            skip_penalty_ratio=0.10,
        ),
        SideMissionDefinition(
            kind=SideMissionType.REVERSE_PSYCHOLOGY,
            title="REVERSE PSYCHOLOGY",
            description=(
                "Next 3 rounds you must guess wrong to win.",
                "Equal still loses.",
            ),
            rounds=3,
            reverse_logic=True,
        ),
    )

    def random_definition(self) -> SideMissionDefinition:
        """Return a random side mission definition."""
        return random.choice(self._DEFINITIONS)

    def start(self, definition: SideMissionDefinition) -> SideMissionState:
        """Create a new side mission state from a definition."""
        rounds = definition.rounds or definition.wins_required
        return SideMissionState(definition=definition, rounds_left=rounds)
