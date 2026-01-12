"""Tests for session data model."""
from models.session import SessionData


def test_session_defaults():
    """Default session should start with baseline values."""
    session = SessionData()
    assert session.balance == 5000
    assert session.total_credits == 5000
    assert session.base_bet == 200
    assert session.decks_completed == 0
    assert session.win_streak == 0
    assert session.max_win_streak == 0
    assert session.side_missions_enabled is True
    assert session.calibration_enabled is True


def test_session_to_dict_includes_flags():
    """Serialized session should include feature toggles."""
    session = SessionData()
    session.side_missions_enabled = False
    session.calibration_enabled = False
    payload = session.to_dict()
    assert payload["side_missions_enabled"] is False
    assert payload["calibration_enabled"] is False


def test_session_from_dict_defaults_unknown_fields():
    """Loading from partial dict should use defaults."""
    session = SessionData.from_dict({"balance": 1234})
    assert session.balance == 1234
    assert session.base_bet == 200
