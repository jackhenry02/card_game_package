"""Black-market shop for upgrades in the infinite game."""
from __future__ import annotations

from dataclasses import dataclass

from interfaces.infinite_io_provider import InfiniteIOProvider
from logic.save_manager import SaveManager
from models.session import SessionData


@dataclass(frozen=True)
class ShopItem:
    """Represents a purchasable shop item."""

    key: str
    name: str
    description: str
    base_cost: int
    max_level: int | None = None


class Shop:
    """Handles shop interactions and purchases."""

    _ODDS_ITEM = ShopItem(
        key="1",
        name="Odds Augmenter",
        description="Doubles payout multiplier per level.",
        base_cost=4000,
        max_level=7,
    )
    _BET_ITEM = ShopItem(
        key="2",
        name="Bet Amplifier",
        description="Doubles your base stake per level.",
        base_cost=3000,
        max_level=7,
    )
    _AI_ITEM = ShopItem(
        key="3",
        name="AI Card Counter",
        description="Reveals exact win percentages.",
        base_cost=30000,
        max_level=1,
    )
    _JOKER_ITEM = ShopItem(
        key="4",
        name="Double Jokers",
        description="Doubles joker count per deck.",
        base_cost=60000,
        max_level=1,
    )

    def open(
        self,
        io_provider: InfiniteIOProvider,
        session: SessionData,
        save_manager: SaveManager,
    ) -> None:
        """Run the shop loop.

        Args:
            io_provider: IO provider for rendering.
            session: Session data to mutate.
            save_manager: Save manager for persistence.
        """
        session.visited_shop = True
        while True:
            io_provider.show_message("", instant=True)
            io_provider.show_message("=== BLACK MARKET TERMINAL ===", instant=True)
            io_provider.show_message(
                f"Balance: {session.balance} credits",
                instant=True,
            )
            self._show_item(io_provider, session, self._ODDS_ITEM, session.upgrades.odds_level)
            self._show_item(io_provider, session, self._BET_ITEM, session.upgrades.bet_level)
            self._show_item(io_provider, session, self._AI_ITEM, 1 if session.upgrades.ai_counter else 0)
            self._show_item(io_provider, session, self._JOKER_ITEM, session.upgrades.joker_level)
            io_provider.show_message("B) Back to mission", instant=True)

            choice = io_provider.get_input("What would you like to buy? ").strip().lower()
            if choice in {"b", "back", "exit"}:
                break
            if choice in {self._ODDS_ITEM.key, "odds", "augmenter"}:
                self._attempt_level_purchase(
                    io_provider,
                    session,
                    self._ODDS_ITEM,
                    "odds_level",
                )
            elif choice in {self._BET_ITEM.key, "bet", "stake"}:
                self._attempt_level_purchase(
                    io_provider,
                    session,
                    self._BET_ITEM,
                    "bet_level",
                )
            elif choice in {self._AI_ITEM.key, "ai", "counter"}:
                self._attempt_toggle_purchase(
                    io_provider,
                    session,
                    self._AI_ITEM,
                    "ai_counter",
                )
            elif choice in {self._JOKER_ITEM.key, "joker", "jokers"}:
                self._attempt_level_purchase(
                    io_provider,
                    session,
                    self._JOKER_ITEM,
                    "joker_level",
                )
            else:
                io_provider.show_message("Unknown selection.", instant=True)
                continue

            save_manager.save(session)

    def _show_item(
        self,
        io_provider: InfiniteIOProvider,
        session: SessionData,
        item: ShopItem,
        level: int,
    ) -> None:
        """Display a shop item line with cost and status."""
        if item.max_level is not None and level >= item.max_level:
            status = "MAX"
            cost_label = "N/A"
        else:
            status = f"Lv {level}"
            cost_label = str(self._next_cost(item, level))
        io_provider.show_message(
            f"{item.key}) {item.name} [{status}] - {item.description} "
            f"(Cost: {cost_label})",
            instant=True,
        )

    def _next_cost(self, item: ShopItem, level: int) -> int:
        """Calculate the next cost for a level-based upgrade."""
        return int(item.base_cost * (2 ** level))

    def _attempt_level_purchase(
        self,
        io_provider: InfiniteIOProvider,
        session: SessionData,
        item: ShopItem,
        attribute: str,
    ) -> None:
        """Handle purchasing a level-based upgrade."""
        current_level = int(getattr(session.upgrades, attribute))
        if item.max_level is not None and current_level >= item.max_level:
            io_provider.show_message("Upgrade already at max level.", instant=True)
            return
        cost = self._next_cost(item, current_level)
        if session.balance < cost:
            io_provider.show_message("You cant afford that, pick something else.", instant=True)
            return
        session.balance -= cost
        setattr(session.upgrades, attribute, current_level + 1)
        io_provider.show_message("Purchase confirmed.", instant=True)

    def _attempt_toggle_purchase(
        self,
        io_provider: InfiniteIOProvider,
        session: SessionData,
        item: ShopItem,
        attribute: str,
    ) -> None:
        """Handle purchasing a boolean upgrade."""
        current = bool(getattr(session.upgrades, attribute))
        if current:
            io_provider.show_message("Upgrade already installed.", instant=True)
            return
        cost = item.base_cost
        if session.balance < cost:
            io_provider.show_message("You cant afford that, pick something else.", instant=True)
            return
        session.balance -= cost
        setattr(session.upgrades, attribute, True)
        io_provider.show_message("Purchase confirmed.", instant=True)
