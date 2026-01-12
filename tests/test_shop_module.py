"""Tests for shop interactions."""
from pathlib import Path

from logic.save_manager import SaveManager
from logic.shop import Shop
from models.session import SessionData


class QueueIO:
    """IO provider returning queued inputs."""

    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.messages = []

    def get_input(self, prompt: str) -> str:
        if not self._inputs:
            return "b"
        return self._inputs.pop(0)

    def show_message(self, message: str, *, instant: bool = False):
        self.messages.append(message)


def test_shop_rejects_purchase_without_balance(tmp_path: Path):
    """Shop should block purchases when funds are insufficient."""
    session = SessionData(balance=100)
    io = QueueIO(["1", "b"])
    shop = Shop()
    shop.open(io, session, SaveManager(tmp_path / "session.json"))
    assert session.upgrades.odds_level == 0
    assert any("afford" in message.lower() for message in io.messages)


def test_shop_allows_purchase_and_deducts_balance(tmp_path: Path):
    """Shop should deduct balance and apply upgrade."""
    session = SessionData(balance=10000)
    io = QueueIO(["2", "b"])
    shop = Shop()
    shop.open(io, session, SaveManager(tmp_path / "session.json"))
    assert session.upgrades.bet_level == 1
    assert session.balance < 10000
