"""Tests for achievement catalog definitions."""
from models.achievements import AchievementCatalog


def test_achievement_keys_are_unique():
    """Each achievement should have a unique key."""
    keys = [definition.key for definition in AchievementCatalog.DEFINITIONS]
    assert len(keys) == len(set(keys))


def test_default_state_starts_locked():
    """Default state should mark all achievements locked."""
    defaults = AchievementCatalog.default_state()
    assert defaults
    assert all(state is False for state in defaults.values())


def test_merge_state_respects_known_keys():
    """Merge should apply stored values for known keys only."""
    stored = {"first_deck": True, "unknown_key": True}
    merged = AchievementCatalog.merge_state(stored)
    assert merged["first_deck"] is True
    assert "unknown_key" not in merged
