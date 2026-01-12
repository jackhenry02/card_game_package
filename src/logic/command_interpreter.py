"""Command interpreter for the infinite game."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from interfaces.infinite_io_provider import InfiniteIOProvider
from logic.game_state import GameState
from logic.save_manager import SaveManager
from models.session import SessionData


@dataclass
class CommandContext:
    """Shared context passed to command handlers."""

    io_provider: InfiniteIOProvider
    session: SessionData
    save_manager: SaveManager


@dataclass(frozen=True)
class CommandResult:
    """Result of executing a command."""

    handled: bool
    next_state: GameState | None = None
    should_exit: bool = False


class Command(Protocol):
    """Protocol for game commands."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the command.

        Args:
            context: Shared command context.

        Returns:
            CommandResult describing the outcome.
        """
        raise NotImplementedError


class CommandInterpreter:
    """Interprets and dispatches text commands."""

    def __init__(self, commands: dict[str, Command]) -> None:
        """Initialise with a mapping of command keywords.

        Args:
            commands: Mapping of command strings to handlers.
        """
        self._commands = commands

    def interpret(self, raw_input: str, context: CommandContext) -> CommandResult | None:
        """Interpret user input and execute commands when matched.

        Args:
            raw_input: Raw input string from the player.
            context: Shared command context.

        Returns:
            CommandResult if a command matched, otherwise None.
        """
        normalized = raw_input.strip().lower()
        command = self._commands.get(normalized)
        if command is None:
            return None
        return command.execute(context)


class ShopCommand:
    """Command to enter the shop."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Request transition to the shop state."""
        context.io_provider.show_message(
            "[SHOP] Routing to the black market...",
            instant=True,
        )
        return CommandResult(handled=True, next_state=GameState.SHOPPING)


class SettingsCommand:
    """Command to open settings."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Request transition to the settings state."""
        context.io_provider.show_message(
            "[SETTINGS] Opening visual controls...",
            instant=True,
        )
        return CommandResult(handled=True, next_state=GameState.SETTINGS)


class SaveCommand:
    """Command to save the current session."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Persist the current session to disk."""
        context.save_manager.save(context.session)
        context.io_provider.show_message(
            "[SAVE] Session written to disk.",
            instant=True,
        )
        return CommandResult(handled=True)


class ExitCommand:
    """Command to save and exit."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Save progress and request termination."""
        context.save_manager.save(context.session)
        context.io_provider.show_message(
            "[EXIT] Session saved. Disconnecting...",
            instant=True,
        )
        return CommandResult(handled=True, should_exit=True)


class HelpCommand:
    """Command to show available commands."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Display help information for command shortcuts."""
        lines = [
            "",
            "COMMANDS:",
            "shop     -> open the black-market shop",
            "settings -> toggle visual effects",
            "achievements -> view mission badges",
            "save     -> save your current run",
            "exit     -> save and leave the terminal",
            "help     -> show this list",
            "",
        ]
        for line in lines:
            context.io_provider.show_message(line, instant=True)
        return CommandResult(handled=True)


class AchievementsCommand:
    """Command to view achievements."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Request transition to the achievements state."""
        context.io_provider.show_message(
            "[ACHIEVEMENTS] Pulling classified record...",
            instant=True,
        )
        return CommandResult(handled=True, next_state=GameState.ACHIEVEMENTS)
