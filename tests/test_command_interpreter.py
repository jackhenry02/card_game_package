"""Tests for command interpreter and commands."""
from pathlib import Path

from logic.command_interpreter import CommandContext, CommandInterpreter
from logic.command_interpreter import ExitCommand, HelpCommand, ShopCommand
from logic.save_manager import SaveManager
from models.session import SessionData
from logic.game_state import GameState


class DummyIO:
    """Minimal IO for command tests."""

    def __init__(self) -> None:
        self.messages = []

    def show_message(self, message: str, *, instant: bool = False):
        self.messages.append(message)


def test_interpreter_unknown_command_returns_none(tmp_path: Path):
    """Unknown commands should not be handled."""
    io = DummyIO()
    context = CommandContext(
        io_provider=io,
        session=SessionData(),
        save_manager=SaveManager(tmp_path / "session.json"),
    )
    interpreter = CommandInterpreter({})
    assert interpreter.interpret("unknown", context) is None


def test_shop_command_transitions_state(tmp_path: Path):
    """Shop command should request shopping state."""
    io = DummyIO()
    context = CommandContext(
        io_provider=io,
        session=SessionData(),
        save_manager=SaveManager(tmp_path / "session.json"),
    )
    interpreter = CommandInterpreter({"shop": ShopCommand()})
    result = interpreter.interpret("shop", context)
    assert result is not None
    assert result.next_state == GameState.SHOPPING


def test_help_command_emits_messages(tmp_path: Path):
    """Help command should output command list."""
    io = DummyIO()
    context = CommandContext(
        io_provider=io,
        session=SessionData(),
        save_manager=SaveManager(tmp_path / "session.json"),
    )
    result = HelpCommand().execute(context)
    assert result.handled is True
    assert any("COMMANDS" in message for message in io.messages)


def test_exit_command_sets_should_exit(tmp_path: Path):
    """Exit command should flag termination."""
    io = DummyIO()
    context = CommandContext(
        io_provider=io,
        session=SessionData(),
        save_manager=SaveManager(tmp_path / "session.json"),
    )
    result = ExitCommand().execute(context)
    assert result.should_exit is True
