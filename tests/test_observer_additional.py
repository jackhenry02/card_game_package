"""Additional tests for deck observers."""
from logic.observer import AICardCounter, DeckWatcher
from models.card import Card, Rank, Suit


class DummyObserver:
    """Observer that records notifications."""

    def __init__(self) -> None:
        self.called = False
        self.snapshot = ()

    def on_deck_updated(self, remaining):
        self.called = True
        self.snapshot = tuple(remaining)


def test_deck_watcher_attach_detach():
    """DeckWatcher should notify attached observers."""
    watcher = DeckWatcher()
    observer = DummyObserver()
    watcher.attach(observer)
    watcher.notify([Card(Rank.TWO, Suit.CLUBS)])
    assert observer.called is True
    watcher.detach(observer)
    observer.called = False
    watcher.notify([])
    assert observer.called is False


def test_ai_card_counter_empty_deck():
    """AI counter should return zero odds for empty decks."""
    counter = AICardCounter()
    counter.on_deck_updated([])
    odds = counter.win_odds(Card(Rank.ACE, Suit.SPADES))
    assert odds.higher == 0.0
    assert odds.lower == 0.0
    assert odds.joker == 0.0
