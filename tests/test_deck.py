"""pytest tests for the deck class"""

from unittest import mock

import pytest

from models.card import Card, Rank, Suit
from models.deck import Deck, DeckEmptyError

@pytest.fixture
def small_deck():
    """A fixture providing a deck with only 2 cards for controlled testing."""
    return Deck(
        [
            Card(rank=Rank.TWO, suit=Suit.CLUBS),
            Card(rank=Rank.THREE, suit=Suit.HEARTS),
        ]
    )


def test_deck_deal_reduces_size(small_deck):
    """Dealing a card reduces the deck size"""
    small_deck.deal()
    assert len(small_deck) == 1


def test_deck_deal_empty_raises():
    """Dealing from an empty deck raises DeckEmptyError"""
    deck = Deck([])
    with pytest.raises(DeckEmptyError):
        deck.deal()


def test_standard_deck_size():
    """Standard deck contains 52 cards"""
    deck = Deck()
    assert len(deck) == 52


def test_deck_with_jokers_size():
    """Deck includes jokers when configured."""
    deck = Deck(include_jokers=True, jokers_count=2)
    assert len(deck) == 54


def test_shuffle_calls_random(small_deck):
    """Shuffle method calls random.shuffle"""
    with mock.patch("models.deck.random.shuffle") as shuffle_mock:
        small_deck.shuffle()
        shuffle_mock.assert_called_once()
