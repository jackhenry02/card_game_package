"""Tests for achievements menu output."""
from logic.achievements_menu import AchievementsMenu
from models.session import SessionData


class DummyIO:
    """IO provider that captures output."""

    def __init__(self):
        self.messages = []

    def show_message(self, message: str, *, instant: bool = False):
        self.messages.append(message)

    def get_input(self, prompt: str) -> str:
        return ""


def test_achievements_menu_lists_entries():
    """Menu should output the achievements header."""
    session = SessionData()
    io = DummyIO()
    AchievementsMenu().open(io, session)
    assert any("ACHIEVEMENTS" in message for message in io.messages)


def test_achievements_menu_marks_unlocked():
    """Unlocked achievements should be reported as such."""
    session = SessionData()
    session.achievements["first_deck"] = True
    io = DummyIO()
    AchievementsMenu().open(io, session)
    assert any("UNLOCKED" in message for message in io.messages)
