"""Spy-themed CLI for the infinite card game."""
from __future__ import annotations

import time

from interfaces.infinite_io_provider import InfiniteIOProvider
from models.card import Card, Rank, Suit
from models.session import VisualSettings


class SpyCLI(InfiniteIOProvider):
    """CLI implementation with typewriter effects and ASCII card art."""

    _SUIT_SYMBOLS = {
        Suit.HEARTS: "♥",
        Suit.DIAMONDS: "♦",
        Suit.SPADES: "♠",
        Suit.CLUBS: "♣",
        Suit.JOKER: "J",
    }
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _RED = "\033[31m"
    _BLUE = "\033[34m"
    _GREEN = "\033[32m"
    _CYAN = "\033[36m"
    _YELLOW = "\033[33m"

    def __init__(self, *, enable_colour: bool = True) -> None:
        """Initialise the CLI with default visual settings."""
        self._show_card_art = True
        self._typewriter = True
        self._default_speed = 0.03
        self._enable_colour = enable_colour

    def show_message(
        self,
        message: str,
        *,
        instant: bool = False,
        speed: float | None = None,
    ) -> None:
        """Display a message to the player."""
        message = self._style_message(message)
        use_typewriter = not instant and (self._typewriter or speed is not None)
        if use_typewriter:
            self._typewriter_print(message, speed)
        else:
            print(message)

    def display_card(self, card: Card) -> None:
        """Render a card to the terminal."""
        if not self._show_card_art:
            print(str(card))
            return
        print("")
        for line in self._render_card(card):
            if self._enable_colour:
                line = self._colourise_text(line, card)
            print(line)
        text = f"\n{card}"
        if self._enable_colour:
            text = self._colourise_text(text, card)
        print(text)

    def get_input(self, prompt: str) -> str:
        """Collect input from the player."""
        return input(prompt)

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        print("\033c", end="")

    def apply_visual_settings(self, settings: VisualSettings) -> None:
        """Apply visual settings to the CLI."""
        self._show_card_art = settings.show_card_art
        self._typewriter = settings.typewriter

    def _typewriter_print(self, message: str, speed: float | None) -> None:
        """Print text with a typewriter effect."""
        delay = self._default_speed if speed is None else speed
        for char in message:
            print(char, end="", flush=True)
            if delay > 0:
                time.sleep(delay)
        print()

    def _style_message(self, message: str) -> str:
        """Apply subtle styling to HUD-like messages."""
        if not self._enable_colour or not message:
            return message
        stripped = message.lstrip()
        if stripped.startswith("WIN"):
            return f"{self._BOLD}{self._GREEN}{message}{self._RESET}"
        if stripped.startswith("LOSS"):
            return f"{self._BOLD}{self._RED}{message}{self._RESET}"
        if stripped.startswith(">") or stripped.startswith("["):
            return f"{self._CYAN}{message}{self._RESET}"
        if "===" in message:
            return f"{self._BOLD}{self._YELLOW}{message}{self._RESET}"
        return message

    def _colourise_text(self, text: str, card: Card) -> str:
        """Return colourised text based on the card suit."""
        colour = (
            self._RED
            if card.suit in {Suit.HEARTS, Suit.DIAMONDS}
            else self._BLUE
        )
        return f"{self._BOLD}{colour}{text}{self._RESET}"

    def _render_card(self, card: Card) -> list[str]:
        """Return a simple ASCII drawing of a card."""
        display_label = self._short_rank_label(card)
        suit_icon = self._SUIT_SYMBOLS[card.suit]
        return [
            "+---------+",
            f"|{display_label:<2}       |",
            "|         |",
            f"|    {suit_icon}    |",
            "|         |",
            f"|       {display_label:>2}|",
            "+---------+",
        ]

    def _short_rank_label(self, card: Card) -> str:
        """Return a short label for card ranks."""
        if card.is_joker:
            return "JOKER"
        if card.rank.value <= 10:
            return str(card.rank.value)
        return {
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }[card.rank]
