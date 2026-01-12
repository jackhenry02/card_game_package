"""Pytest coverage for infinite-game support modules."""
from __future__ import annotations

from pathlib import Path

from logic.infinite_game import InfiniteGame
from logic.observer import AICardCounter
from logic.save_manager import SaveManager
from logic.side_missions import SideMissionManager, SideMissionType
from models.achievements import AchievementCatalog
from models.card import Card, Rank, Suit
from models.deck import Deck
from models.session import SessionData, VisualSettings


class DummyIO:
    """Minimal IO provider for non-interactive tests."""

    def show_message(
        self,
        message: str,
        *,
        instant: bool = False,
        speed: float | None = None,
    ) -> None:
        return None

    def display_card(self, card: Card) -> None:
        return None

    def get_input(self, prompt: str) -> str:
        return ""

    def clear_screen(self) -> None:
        return None

    def apply_visual_settings(self, settings: VisualSettings) -> None:
        return None


def test_achievement_catalog_defaults():
    """Catalog should declare all achievements as locked by default."""
    defaults = AchievementCatalog.default_state()
    assert defaults
    for definition in AchievementCatalog.DEFINITIONS:
        assert defaults[definition.key] is False


def test_session_serialization_roundtrip():
    """Session data should survive to_dict/from_dict roundtrip."""
    session = SessionData(
        balance=1200,
        total_credits=4500,
        base_bet=300,
        decks_completed=2,
        win_streak=4,
        max_win_streak=7,
    )
    session.upgrades.odds_level = 2
    session.upgrades.ai_counter = True
    session.visual.show_card_art = False
    session.side_missions_enabled = False
    session.calibration_enabled = False
    session.achievements["first_deck"] = True

    payload = session.to_dict()
    restored = SessionData.from_dict(payload)

    assert restored.balance == 1200
    assert restored.total_credits == 4500
    assert restored.base_bet == 300
    assert restored.decks_completed == 2
    assert restored.win_streak == 4
    assert restored.max_win_streak == 7
    assert restored.upgrades.odds_level == 2
    assert restored.upgrades.ai_counter is True
    assert restored.visual.show_card_art is False
    assert restored.side_missions_enabled is False
    assert restored.calibration_enabled is False
    assert restored.achievements["first_deck"] is True


def test_save_manager_roundtrip(tmp_path: Path):
    """SaveManager should persist and reload session data."""
    path = tmp_path / "session.json"
    manager = SaveManager(path)
    session = SessionData(balance=777, total_credits=999)
    manager.save(session)

    loaded = manager.load()
    assert loaded is not None
    assert loaded.balance == 777
    assert loaded.total_credits == 999


def test_side_mission_round_counts():
    """Side missions should initialize rounds from definition."""
    manager = SideMissionManager()
    mission = manager.random_definition()
    state = manager.start(mission)
    expected = mission.rounds or mission.wins_required
    assert state.rounds_left == expected


def test_ai_card_counter_odds_include_jokers():
    """AI counter should include jokers in win odds."""
    counter = AICardCounter()
    current = Card(Rank.FIVE, Suit.CLUBS)
    remaining = [
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.JOKER, Suit.JOKER),
    ]
    counter.on_deck_updated(remaining)
    odds = counter.win_odds(current)
    assert odds.joker == 1 / 3
    assert odds.higher >= odds.lower


def test_calibration_target_label():
    """Calibration label should match rank+initial format (e.g., QS)."""
    io = DummyIO()
    session = SessionData()
    manager = SaveManager(Path("session.json"))
    game = InfiniteGame(io_provider=io, save_manager=manager, session=session)
    card = Card(Rank.QUEEN, Suit.SPADES)
    label = game._card_label_for_scanner(card)
    assert label == "QS"


def test_calibration_target_non_joker():
    """Calibration target should never be a joker."""
    io = DummyIO()
    session = SessionData()
    manager = SaveManager(Path("session.json"))
    game = InfiniteGame(io_provider=io, save_manager=manager, session=session)
    deck = Deck(cards=[Card(Rank.NINE, Suit.HEARTS)])
    game._deck = deck
    target = game._calibration_target_card()
    assert target is not None
    assert target.is_joker is False


def test_side_mission_types_present():
    """Ensure all expected side missions exist."""
    types = {mission.kind for mission in SideMissionManager()._DEFINITIONS}
    assert SideMissionType.DOUBLE_OR_NOTHING in types
    assert SideMissionType.BIG_MONEY in types
    assert SideMissionType.LUCKY_SEVEN in types
    assert SideMissionType.GONE_BLIND in types
    assert SideMissionType.REVERSE_PSYCHOLOGY in types
