"""Tests for settings menu toggles."""
from logic.settings_menu import SettingsMenu
from models.session import SessionData, VisualSettings


class QueueIO:
    """IO provider returning queued inputs."""

    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.messages = []
        self.settings_applied = None

    def get_input(self, prompt: str) -> str:
        if not self._inputs:
            return "b"
        return self._inputs.pop(0)

    def show_message(self, message: str, *, instant: bool = False):
        self.messages.append(message)

    def apply_visual_settings(self, settings: VisualSettings) -> None:
        self.settings_applied = settings


def test_settings_menu_toggles_flags():
    """Settings menu should flip toggles."""
    session = SessionData()
    io = QueueIO(["1", "2", "3", "4", "b"])
    menu = SettingsMenu()
    menu.open(io, session)
    assert session.visual.show_card_art is False
    assert session.visual.typewriter is False
    assert session.side_missions_enabled is False
    assert session.calibration_enabled is False


def test_settings_menu_applies_visual_settings():
    """Settings menu should apply visual settings changes."""
    session = SessionData()
    io = QueueIO(["1", "b"])
    menu = SettingsMenu()
    menu.open(io, session)
    assert io.settings_applied is session.visual
