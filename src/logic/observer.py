"""Observer helpers for deck updates and AI card counter."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from models.card import Card, Rank


@dataclass(frozen=True)
class WinOdds:
    """Represents win probabilities for higher/lower plus joker odds."""

    higher: float
    lower: float
    joker: float


class DeckObserver:
    """Observer interface for deck updates."""

    def on_deck_updated(self, remaining: Sequence[Card]) -> None:
        """React to a deck update.

        Args:
            remaining: Remaining cards in the deck.
        """
        raise NotImplementedError


class DeckWatcher:
    """Subject for notifying observers about deck changes."""

    def __init__(self) -> None:
        """Initialise the watcher with no observers."""
        self._observers: list[DeckObserver] = []

    def attach(self, observer: DeckObserver) -> None:
        """Attach an observer.

        Args:
            observer: Observer to register.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: DeckObserver) -> None:
        """Detach an observer.

        Args:
            observer: Observer to remove.
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, remaining: Sequence[Card]) -> None:
        """Notify observers of a deck update.

        Args:
            remaining: Remaining cards in the deck.
        """
        snapshot = tuple(remaining)
        for observer in self._observers:
            observer.on_deck_updated(snapshot)


class AICardCounter(DeckObserver):
    """Tracks remaining cards and calculates exact odds."""

    def __init__(self) -> None:
        """Initialise counts for the card counter."""
        self._rank_counts: Counter[Rank] = Counter()
        self._joker_count = 0
        self._total = 0

    def on_deck_updated(self, remaining: Sequence[Card]) -> None:
        """Update card counts based on the remaining deck.

        Args:
            remaining: Remaining cards in the deck.
        """
        self._rank_counts = Counter(
            card.rank for card in remaining if not card.is_joker
        )
        self._joker_count = sum(1 for card in remaining if card.is_joker)
        self._total = len(remaining)

    def win_odds(self, current_card: Card) -> WinOdds:
        """Calculate win odds for higher/lower predictions.

        Args:
            current_card: The current card in play.

        Returns:
            WinOdds with higher, lower, and joker probabilities.
        """
        if self._total == 0 or current_card.is_joker:
            return WinOdds(higher=0.0, lower=0.0, joker=0.0)

        higher_count = sum(
            count
            for rank, count in self._rank_counts.items()
            if rank > current_card.rank
        )
        lower_count = sum(
            count
            for rank, count in self._rank_counts.items()
            if rank < current_card.rank
        )
        joker_prob = self._joker_count / self._total if self._total else 0.0
        higher_prob = (higher_count / self._total) + joker_prob
        lower_prob = (lower_count / self._total) + joker_prob
        return WinOdds(
            higher=higher_prob,
            lower=lower_prob,
            joker=joker_prob,
        )
