"""Session data models for the infinite game."""
from __future__ import annotations

from dataclasses import dataclass, field

from models.achievements import AchievementCatalog


@dataclass
class VisualSettings:
    """Visual settings toggles for the CLI."""

    show_card_art: bool = True
    typewriter: bool = True


@dataclass
class UpgradeState:
    """Represents the player's upgrade levels."""

    odds_level: int = 0
    bet_level: int = 0
    ai_counter: bool = False
    joker_level: int = 0

    def odds_multiplier(self) -> float:
        """Return the payout multiplier from odds upgrades."""
        return 2 ** self.odds_level

    def bet_multiplier(self) -> int:
        """Return the bet multiplier from bet upgrades."""
        return 2 ** self.bet_level

    def joker_multiplier(self) -> int:
        """Return the joker multiplier from joker upgrades."""
        return 2 ** self.joker_level


@dataclass
class SessionData:
    """Serializable session data for persistence."""

    balance: int = 5000
    total_credits: int = 5000
    base_bet: int = 200
    decks_completed: int = 0
    win_streak: int = 0
    max_win_streak: int = 0
    upgrades: UpgradeState = field(default_factory=UpgradeState)
    visual: VisualSettings = field(default_factory=VisualSettings)
    side_missions_enabled: bool = True
    calibration_enabled: bool = True
    achievements: dict[str, bool] = field(
        default_factory=AchievementCatalog.default_state
    )
    visited_shop: bool = False
    visited_settings: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize the session to a dictionary."""
        return {
            "balance": self.balance,
            "total_credits": self.total_credits,
            "base_bet": self.base_bet,
            "decks_completed": self.decks_completed,
            "win_streak": self.win_streak,
            "max_win_streak": self.max_win_streak,
            "upgrades": {
                "odds_level": self.upgrades.odds_level,
                "bet_level": self.upgrades.bet_level,
                "ai_counter": self.upgrades.ai_counter,
                "joker_level": self.upgrades.joker_level,
            },
            "visual": {
                "show_card_art": self.visual.show_card_art,
                "typewriter": self.visual.typewriter,
            },
            "side_missions_enabled": self.side_missions_enabled,
            "calibration_enabled": self.calibration_enabled,
            "achievements": self.achievements,
            "visited_shop": self.visited_shop,
            "visited_settings": self.visited_settings,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SessionData:
        """Deserialize session data from a dictionary."""
        upgrades_payload = payload.get("upgrades", {}) if isinstance(payload, dict) else {}
        visual_payload = payload.get("visual", {}) if isinstance(payload, dict) else {}
        achievements_payload = (
            payload.get("achievements", {}) if isinstance(payload, dict) else {}
        )
        upgrades = UpgradeState(
            odds_level=int(upgrades_payload.get("odds_level", 0)),
            bet_level=int(upgrades_payload.get("bet_level", 0)),
            ai_counter=bool(upgrades_payload.get("ai_counter", False)),
            joker_level=int(upgrades_payload.get("joker_level", 0)),
        )
        visual = VisualSettings(
            show_card_art=bool(visual_payload.get("show_card_art", True)),
            typewriter=bool(visual_payload.get("typewriter", True)),
        )
        balance = int(payload.get("balance", 5000)) if isinstance(payload, dict) else 5000
        base_bet = int(payload.get("base_bet", 200)) if isinstance(payload, dict) else 200
        total_credits = (
            int(payload.get("total_credits", balance))
            if isinstance(payload, dict)
            else balance
        )
        return cls(
            balance=balance,
            total_credits=total_credits,
            base_bet=base_bet,
            decks_completed=(
                int(payload.get("decks_completed", 0))
                if isinstance(payload, dict)
                else 0
            ),
            win_streak=int(payload.get("win_streak", 0)) if isinstance(payload, dict) else 0,
            max_win_streak=(
                int(payload.get("max_win_streak", 0))
                if isinstance(payload, dict)
                else 0
            ),
            upgrades=upgrades,
            visual=visual,
            side_missions_enabled=bool(payload.get("side_missions_enabled", True)),
            calibration_enabled=bool(payload.get("calibration_enabled", True)),
            achievements=AchievementCatalog.merge_state(
                achievements_payload if isinstance(achievements_payload, dict) else {}
            ),
            visited_shop=bool(payload.get("visited_shop", False)),
            visited_settings=bool(payload.get("visited_settings", False)),
        )
