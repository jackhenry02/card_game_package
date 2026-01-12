"""Tests for game state enum."""
from logic.game_state import GameState


def test_game_state_values():
    """Ensure state enum values are stable."""
    assert GameState.STARTUP.value == "startup"
    assert GameState.DEALING.value == "dealing"
    assert GameState.SHOPPING.value == "shopping"
    assert GameState.SETTINGS.value == "settings"
    assert GameState.ACHIEVEMENTS.value == "achievements"
    assert GameState.TERMINATED.value == "terminated"


def test_game_state_contains_expected_members():
    """Enum should expose the expected states."""
    names = {state.name for state in GameState}
    assert {"STARTUP", "DEALING", "SHOPPING", "SETTINGS", "ACHIEVEMENTS", "TERMINATED"} <= names
