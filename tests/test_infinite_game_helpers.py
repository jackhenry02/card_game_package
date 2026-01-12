"""Tests for helper methods in the infinite game."""
from pathlib import Path

from logic.infinite_game import InfiniteGame, Prediction
from logic.save_manager import SaveManager
from logic.side_missions import SideMissionDefinition, SideMissionState, SideMissionType
from models.card import Card, Rank, Suit
from models.session import SessionData, VisualSettings


class DummyIO:
    """Minimal IO provider for helper tests."""

    def show_message(self, message: str, *, instant: bool = False, speed=None):
        return None

    def display_card(self, card: Card) -> None:
        return None

    def get_input(self, prompt: str) -> str:
        return ""

    def clear_screen(self) -> None:
        return None

    def apply_visual_settings(self, settings: VisualSettings) -> None:
        return None


def make_game(tmp_path: Path) -> InfiniteGame:
    """Helper to build an InfiniteGame instance."""
    return InfiniteGame(
        io_provider=DummyIO(),
        save_manager=SaveManager(tmp_path / "session.json"),
        session=SessionData(),
    )


def test_calculate_payout_handles_zero_probability(tmp_path: Path):
    """Probability <= 0 should yield None payout."""
    game = make_game(tmp_path)
    assert game._calculate_payout(100, 0.0) is None


def test_calculate_payout_never_below_stake(tmp_path: Path):
    """Payout should never be less than the stake."""
    game = make_game(tmp_path)
    payout = game._calculate_payout(100, 0.9)
    assert payout is not None
    assert payout >= 100


def test_prediction_reverse_logic(tmp_path: Path):
    """Reverse logic should invert prediction correctness."""
    game = make_game(tmp_path)
    current = Card(Rank.FIVE, Suit.CLUBS)
    next_card = Card(Rank.SEVEN, Suit.SPADES)
    assert game._is_prediction_correct(
        current,
        next_card,
        Prediction.HIGHER,
        reverse=False,
    )
    assert not game._is_prediction_correct(
        current,
        next_card,
        Prediction.HIGHER,
        reverse=True,
    )


def test_prediction_fuzzy_matching(tmp_path: Path):
    """Fuzzy matching should accept minor typos."""
    _ = make_game(tmp_path)
    assert Prediction.input_from_player("highe") == Prediction.HIGHER
    assert Prediction.input_from_player("lowr") == Prediction.LOWER


def test_apply_bonus_multiplier(tmp_path: Path):
    """Bonus multiplier should increase payouts when active."""
    game = make_game(tmp_path)
    definition = SideMissionDefinition(
        kind=SideMissionType.BIG_MONEY,
        title="BIG MONEY",
        description=(),
        rounds=1,
        bonus_multiplier=5,
    )
    game._active_side_mission = SideMissionState(definition=definition, rounds_left=1)
    assert game._apply_bonus_multiplier(100) == 500
