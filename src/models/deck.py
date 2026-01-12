"""Defines model of the deck and how it is used."""
from __future__ import annotations # included for consistency and use of Card

import random # For shuffle
from typing import Optional # Optional typing hints

from models.card import Card, Rank, Suit # Import card model

class DeckEmptyError(RuntimeError):
    """Raised when attempting to deal from an empty deck."""

class Deck:
    """Represents a deck of playing cards"""
    def __init__(
        self,
        cards: Optional[list[Card]] = None,
        *,
        include_jokers: bool = False,
        jokers_count: int = 2,
    ) -> None:
        """Initialize the deck

        Args:
            cards: Optional list of cards to use instead of a standard deck
            include_jokers: Whether to include Jokers in a standard deck.
            jokers_count: Number of Jokers to include when enabled.
        """
        if jokers_count < 0:
            raise ValueError("jokers_count must be 0 or greater.")
        # Note underscores are used as guidance of "soft blocks".
        self._cards = (
            list(cards)
            if cards is not None
            else self._create_standard_deck(
                include_jokers=include_jokers,
                jokers_count=jokers_count,
            )
        )

    def shuffle(self) -> None: # Type hint of none as acts on the actual list of cards
        """Shuffle the deck in place"""
        # Fisher-Yates shuffle is O(n) and in-place.
        random.shuffle(self._cards)

    def deal(self) -> Card:
        """Deal a single card from the deck
        
        Raises:
            DeckEmptyError: If the deck has no cards
        """
        if not self._cards:
            raise DeckEmptyError("Cannot deal from an empty deck.")

        # Removes and returns the last item in the list.
        return self._cards.pop()

    def __len__(self) -> int: # magic method for auto returning integers to print
        """Return the number of remaining cards"""
        return len(self._cards)

    def remaining_cards(self) -> tuple[Card, ...]:
        """Return a snapshot of remaining cards."""
        return tuple(self._cards)

    @staticmethod # no self needed
    def _create_standard_deck(
        *,
        include_jokers: bool,
        jokers_count: int,
    ) -> list[Card]:
        """Create a standard 52-card deck, optionally with Jokers."""
        cards = [
            Card(rank=rank, suit=suit)
            for suit in Suit
            if suit != Suit.JOKER
            for rank in Rank
            if rank != Rank.JOKER
        ]
        if include_jokers:
            cards.extend(
                Card(rank=Rank.JOKER, suit=Suit.JOKER)
                for _ in range(jokers_count)
            )
        return cards


### Notes to self: the shuffle isn't very realistic. Could make a more imperfect shuffle??
