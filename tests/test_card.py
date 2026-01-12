"""pytest tests for the card class"""
from models.card import Card, Rank, Suit


def test_card_comparison_by_rank():
    """Simple card comparison check with cards of different suits"""
    low = Card(rank=Rank.FIVE, suit=Suit.CLUBS)
    high = Card(rank=Rank.JACK, suit=Suit.HEARTS)

    assert low < high
    assert high > low


def test_card_equality_by_rank():
    """Check that cards of the same rank are equal"""
    card_a = Card(rank=Rank.ACE, suit=Suit.SPADES)
    card_b = Card(rank=Rank.ACE, suit=Suit.HEARTS)

    assert card_a == card_b


def test_joker_card_label_and_flag():
    """Check that jokers report their label and flag."""
    joker = Card(rank=Rank.JOKER, suit=Suit.JOKER)
    assert joker.is_joker
    assert str(joker) == "Joker"
