"""Defines model of the card for the game"""
from __future__ import annotations # Needed for error detection. Needs to be first

from enum import Enum, IntEnum # will be using these to make the card values
from dataclasses import dataclass # Used for classes that store data
from functools import total_ordering # Used to 'fill in' missing comparators

class Suit(Enum):
    """Enumeration of card suits"""

    CLUBS = "Clubs ♣"
    DIAMONDS = "Diamonds ♦"
    HEARTS = "Hearts ♥"
    SPADES = "Spades ♠"
    JOKER = "Joker"

    def label(self) -> str:
        """Return a readable label for the suit"""
        return self.value

class Rank(IntEnum):
    """Enumeration of card ranks with numeric values. Ace-high"""

    JOKER = 0
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def label(self) -> str:
        """Return a readable label for the rank"""
        if self == Rank.JOKER:
            return "Joker"
        if self <= Rank.TEN:
            return str(int(self))
        return self.name.title()

@total_ordering
@dataclass(frozen=True)
class Card:
    """Frozen playing card class with rank comparisons"""

    rank: Rank # effectively in the __init__ due to dataclass decorator
    suit: Suit

    # Using magic methods for automatic use/recognition

    def __eq__(self, other: object) -> bool:
        """Return True when card ranks are equal"""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank
    
    def __lt__(self, other: object) -> bool:
        """Return True when this card rank is lower than the other"""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank < other.rank

    def __str__(self) -> str:
        """Return a readable card label"""
        if self.is_joker:
            return "Joker"
        return f"{self.rank.label()} of {self.suit.label()}"

    @property
    def is_joker(self) -> bool:
        """Return True if the card is a Joker."""
        return self.rank == Rank.JOKER or self.suit == Suit.JOKER

    
