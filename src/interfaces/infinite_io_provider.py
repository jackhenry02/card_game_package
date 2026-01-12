"""Interface definition for the infinite game IO layer."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.card import Card
from models.session import VisualSettings


class InfiniteIOProvider(ABC):
    """Abstract base class for infinite game input/output providers."""

    @abstractmethod
    def show_message(
        self,
        message: str,
        *,
        instant: bool = False,
        speed: float | None = None,
    ) -> None:
        """Display a message to the player.

        Args:
            message: Text to display.
            instant: When True, bypass typewriter effects.
            speed: Optional override for typewriter speed in seconds.
        """
        raise NotImplementedError

    @abstractmethod
    def display_card(self, card: Card) -> None:
        """Display the current card.

        Args:
            card: Card to render.
        """
        raise NotImplementedError

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """Collect input from the player.

        Args:
            prompt: Prompt displayed to the player.

        Returns:
            Raw input string.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        raise NotImplementedError

    @abstractmethod
    def apply_visual_settings(self, settings: VisualSettings) -> None:
        """Apply visual settings to the IO provider.

        Args:
            settings: Visual settings preferences.
        """
        raise NotImplementedError
