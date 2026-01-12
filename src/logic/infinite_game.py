"""Infinite higher/lower game engine with espionage theme."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
import time

from interfaces.infinite_io_provider import InfiniteIOProvider
from logic.command_interpreter import CommandContext, CommandInterpreter, CommandResult
from logic.command_interpreter import AchievementsCommand, ExitCommand, HelpCommand
from logic.command_interpreter import SaveCommand, SettingsCommand, ShopCommand
from logic.achievements_menu import AchievementsMenu
from logic.game_state import GameState
from logic.observer import AICardCounter, DeckWatcher, WinOdds
from logic.save_manager import SaveManager
from logic.settings_menu import SettingsMenu
from logic.side_missions import (
    SideMissionDefinition,
    SideMissionManager,
    SideMissionState,
    SideMissionType,
)
from logic.shop import Shop
from models.card import Card, Rank, Suit
from models.deck import Deck
from models.achievements import AchievementCatalog
from models.session import SessionData
from computer_vision.calibration import scan_card


class InvalidPredictionError(ValueError):
    """Raised when a prediction string is invalid."""


class Prediction(Enum):
    """Possible higher/lower predictions."""

    HIGHER = "higher"
    LOWER = "lower"

    @classmethod
    def input_from_player(cls, raw_prediction: str) -> Prediction:
        """Parse raw input into a Prediction.

        Args:
            raw_prediction: Raw input string.

        Raises:
            InvalidPredictionError: If the input is invalid.
        """
        aliases = {
            "h": cls.HIGHER,
            "hi": cls.HIGHER,
            "high": cls.HIGHER,
            "higher": cls.HIGHER,
            "l": cls.LOWER,
            "lo": cls.LOWER,
            "low": cls.LOWER,
            "lower": cls.LOWER,
        }
        normalized = raw_prediction.strip().lower()
        if normalized in aliases:
            return aliases[normalized]
        fuzzy_match = cls._fuzzy_match(normalized)
        if fuzzy_match is not None:
            return aliases[fuzzy_match]
        raise InvalidPredictionError(
            "Invalid prediction. Use higher (h) or lower (l)."
        )

    @classmethod
    def _fuzzy_match(cls, word: str) -> str | None:
        """Return the closest fuzzy match for a prediction string."""
        fuzzy_targets = ["high", "higher", "low", "lower"]
        max_distance = 1
        for target in fuzzy_targets:
            distance = cls._levenshtein(word, target)
            if distance <= max_distance:
                return target
        return None

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        """Return the Levenshtein distance between two strings."""
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)

        previous_row = list(range(len(b) + 1))
        for i, a_char in enumerate(a, 1):
            current_row = [i]
            for j, b_char in enumerate(b, 1):
                insert = current_row[j - 1] + 1
                delete = previous_row[j] + 1
                replace = previous_row[j - 1] + (a_char != b_char)
                current_row.append(min(insert, delete, replace))
            previous_row = current_row
        return previous_row[-1]


@dataclass(frozen=True)
class PayoutTable:
    """Payout information for the current round."""

    stake: int
    higher: int | None
    lower: int | None


class InfiniteGame:
    """Core game loop for the infinite espionage card game."""

    _HOUSE_EDGE = 0.06
    _FINAL_CREDITS = 100_000_000
    _BASE_JOKERS = 2
    _SIDE_MISSION_INTERVAL = 15

    def __init__(
        self,
        io_provider: InfiniteIOProvider,
        save_manager: SaveManager,
        session: SessionData,
        *,
        resume: bool = False,
    ) -> None:
        """Initialise the game with injected dependencies.

        Args:
            io_provider: IO provider for user interaction.
            save_manager: Persistence manager.
            session: Session data for the run.
            resume: Whether this run is a resumed session.
        """
        self._io = io_provider
        self._save_manager = save_manager
        self._session = session
        self._resume = resume
        self._state = GameState.STARTUP
        self._deck: Deck | None = None
        self._current_card: Card | None = None
        self._deck_watcher = DeckWatcher()
        self._ai_counter = AICardCounter()
        self._deck_watcher.attach(self._ai_counter)
        self._shop = Shop()
        self._settings_menu = SettingsMenu()
        self._achievements_menu = AchievementsMenu()
        self._side_mission_manager = SideMissionManager()
        self._active_side_mission: SideMissionState | None = None
        self._rounds_completed = 0
        self._pending_side_mission: SideMissionDefinition | None = None
        self._achievement_names = {
            definition.key: definition.name
            for definition in AchievementCatalog.DEFINITIONS
        }
        self._command_context = CommandContext(
            io_provider=self._io,
            session=self._session,
            save_manager=self._save_manager,
        )
        self._command_interpreter = CommandInterpreter(
            {
                "shop": ShopCommand(),
                "store": ShopCommand(),
                "settings": SettingsCommand(),
                "achievements": AchievementsCommand(),
                "achieve": AchievementsCommand(),
                "save": SaveCommand(),
                "exit": ExitCommand(),
                "quit": ExitCommand(),
                "help": HelpCommand(),
            }
        )

    def run(self) -> None:
        """Run the main game loop."""
        self._io.apply_visual_settings(self._session.visual)
        while self._state != GameState.TERMINATED:
            if self._state == GameState.STARTUP:
                self._handle_startup()
            elif self._state == GameState.DEALING:
                self._handle_dealing()
            elif self._state == GameState.SHOPPING:
                self._shop.open(self._io, self._session, self._save_manager)
                self._check_shop_achievement()
                self._state = GameState.DEALING
            elif self._state == GameState.SETTINGS:
                self._settings_menu.open(self._io, self._session)
                self._save_manager.save(self._session)
                self._state = GameState.DEALING
            elif self._state == GameState.ACHIEVEMENTS:
                self._achievements_menu.open(self._io, self._session)
                self._state = GameState.DEALING

    def _handle_startup(self) -> None:
        """Display the introduction and prepare the first deck."""
        self._io.clear_screen()
        if not self._resume:
            self._show_intro_story()
        else:
            self._io.show_message("> SESSION RESTORED.", instant=True)
        self._show_rules()
        self._check_shop_achievement()
        self._check_credit_achievements()
        self._prime_new_deck(initial=True)
        self._current_card = self._deal_starting_card()
        self._state = GameState.DEALING

    def _handle_dealing(self) -> None:
        """Run continuous rounds until the state changes."""
        while self._state == GameState.DEALING:
            if self._session.balance <= 0:
                self._io.show_message(
                    "[SYSTEM] Balance depleted. Better luck next time.",
                    instant=True,
                )
                self._state = GameState.TERMINATED
                return
            if self._session.balance < self._stake_amount():
                self._io.show_message("[SYSTEM] Funds depleted. Mission terminated.")
                self._io.show_message("We will get 'em next time...")
                self._state = GameState.TERMINATED
                return
            if self._pending_side_mission is not None and self._active_side_mission is None:
                self._offer_side_mission()
                if self._state != GameState.DEALING:
                    return

            if self._deck is None or len(self._deck) == 0:
                self._prime_new_deck(initial=False)
                self._current_card = self._deal_starting_card()

            if self._current_card is None:
                self._current_card = self._deal_starting_card()

            self._run_round()

    def _run_round(self) -> None:
        """Handle a single higher/lower round."""
        current_card = self._current_card
        if current_card is None:
            return

        side_mission = self._active_side_mission
        blind_active = side_mission is not None and side_mission.is_blind()
        reverse_active = side_mission is not None and side_mission.is_reverse()

        self._io.show_message("", instant=True)
        self._io.show_message("=" * 46, instant=True)
        self._io.show_message(
            f"Balance: {self._session.balance} | "
            f"Extracted: {self._session.total_credits}",
            instant=True,
        )
        if side_mission is not None:
            self._io.show_message(
                f"Side mission: {side_mission.definition.title}",
                instant=True,
            )
        self._io.show_message("-" * 46, instant=True)
        if blind_active:
            self._io.show_message("Current card: [HIDDEN]", instant=True)
        else:
            self._io.show_message("Current card:", instant=True)
            self._io.display_card(current_card)

        exact_odds = self._ai_counter.win_odds(current_card)
        payout_table = self._build_payouts(exact_odds)
        self._display_odds(exact_odds, payout_table, blind=blind_active)

        prediction = self._prompt_prediction(payout_table)
        if prediction is None:
            return

        win_probability = self._win_probability(exact_odds, prediction, reverse_active)
        self._session.balance -= payout_table.stake
        next_card = self._deal_card()
        self._io.show_message("Next card:", instant=True)
        self._io.display_card(next_card)

        if next_card.is_joker:
            self._io.show_message("Joker breach! Auto-win.", instant=True)
            payout = self._payout_for_prediction(prediction, payout_table)
            if payout is not None:
                payout = self._apply_bonus_multiplier(payout)
                self._apply_win(payout, payout_table.stake)
            self._update_side_mission_after_round(win=True)
            self._after_round(win=True, win_probability=win_probability)
            self._check_final_extraction()
            self._current_card = self._deal_starting_card()
            self._check_deck_depleted()
            return

        win = self._is_prediction_correct(
            current_card,
            next_card,
            prediction,
            reverse=reverse_active,
        )
        if win:
            payout = self._payout_for_prediction(prediction, payout_table)
            if payout is None:
                self._io.show_message("No payout available for that call.", instant=True)
            else:
                payout = self._apply_bonus_multiplier(payout)
                self._apply_win(payout, payout_table.stake)
        else:
            self._apply_loss(payout_table.stake)

        self._update_side_mission_after_round(win=win)
        self._after_round(win=win, win_probability=win_probability)
        if self._session.balance <= 0:
            self._io.show_message(
                "[SYSTEM] Balance depleted. Better luck next time.",
                instant=True,
            )
            self._state = GameState.TERMINATED
            return
        self._check_final_extraction()
        self._check_deck_depleted(next_card)

    def _prompt_prediction(self, payout_table: PayoutTable) -> Prediction | None:
        """Ask for the player's prediction, handling commands.

        Args:
            payout_table: Available payouts for the round.

        Returns:
            Parsed Prediction, or None if a command interrupted the round.
        """
        while True:
            raw_input = self._io.get_input("Higher or lower? [H/L] > ")
            command_result = self._command_interpreter.interpret(
                raw_input, self._command_context
            )
            if command_result is not None:
                if self._apply_command_result(command_result):
                    return None
                continue

            try:
                prediction = Prediction.input_from_player(raw_input)
            except InvalidPredictionError as exc:
                self._io.show_message(str(exc), instant=True)
                continue

            if self._payout_for_prediction(prediction, payout_table) is None:
                self._io.show_message(
                    "No winning outcomes for that call.",
                    instant=True,
                )
                continue
            return prediction

    def _apply_command_result(self, result: CommandResult) -> bool:
        """Apply a command result and return True if round is interrupted."""
        if result.should_exit:
            self._state = GameState.TERMINATED
            return True
        if result.next_state is not None:
            self._state = result.next_state
            return True
        return False

    def _build_payouts(self, odds: WinOdds) -> PayoutTable:
        """Build payout values for higher/lower predictions."""
        stake = self._stake_amount()
        higher = self._calculate_payout(stake, odds.higher)
        lower = self._calculate_payout(stake, odds.lower)
        return PayoutTable(stake=stake, higher=higher, lower=lower)

    def _calculate_payout(self, stake: int, probability: float) -> int | None:
        """Calculate the total payout for a given probability."""
        if probability <= 0:
            return None
        multiplier = (1 / probability) * (1 - self._HOUSE_EDGE)
        multiplier *= self._session.upgrades.odds_multiplier()
        payout = int(round(stake * multiplier))
        return max(stake, payout)

    def _payout_for_prediction(
        self, prediction: Prediction, payout_table: PayoutTable
    ) -> int | None:
        """Return payout value for a prediction."""
        if prediction == Prediction.HIGHER:
            return payout_table.higher
        return payout_table.lower

    def _display_odds(
        self,
        exact: WinOdds,
        payout_table: PayoutTable,
        *,
        blind: bool,
    ) -> None:
        """Display odds and payouts before a prediction."""
        if blind:
            self._io.show_message(
                "Blind round active. Odds are classified.",
                instant=True,
            )
            self._io.show_message(
                f"Stake: {payout_table.stake}",
                instant=True,
            )
            return
        if self._session.upgrades.ai_counter:
            self._io.show_message("Odds:", instant=True)
            self._io.show_message("AI Counter:", instant=True)
            self._show_odds_line("Higher", exact.higher)
            self._show_odds_line("Lower", exact.lower)
            if exact.joker > 0:
                self._show_odds_line("Joker auto-win", exact.joker)
            self._io.show_message(
                f"Stake: {payout_table.stake}",
                instant=True,
            )
            higher_label = self._payout_label(payout_table.higher)
            lower_label = self._payout_label(payout_table.lower)
            self._io.show_message(
                f"Payout if Higher: {higher_label} | Payout if Lower: {lower_label}",
                instant=True,
            )
            return
        self._io.show_message(
            "Odds: [LOCKED] Install the AI Card Counter to reveal.",
            instant=True,
        )
        self._io.show_message(
            f"Stake: {payout_table.stake} | Payout: [LOCKED]",
            instant=True,
        )

    def _show_odds_line(self, label: str, probability: float) -> None:
        """Display a formatted odds line."""
        if probability <= 0:
            self._io.show_message(f"{label}: N/A", instant=True)
            return
        percent = probability * 100
        self._io.show_message(f"{label}: {percent:.1f}%", instant=True)

    def _payout_label(self, payout: int | None) -> str:
        """Return a string label for payout values."""
        return "N/A" if payout is None else str(payout)

    def _estimate_odds(self, current_card: Card) -> WinOdds:
        """Estimate odds using rank-only probabilities."""
        if current_card.is_joker:
            return WinOdds(higher=0.0, lower=0.0, joker=0.0)
        position = current_card.rank.value - 1
        higher = max(0, 13 - position) / 13
        lower = max(0, position - 1) / 13
        return WinOdds(higher=higher, lower=lower, joker=0.0)

    def _is_prediction_correct(
        self,
        current_card: Card,
        next_card: Card,
        prediction: Prediction,
        *,
        reverse: bool,
    ) -> bool:
        """Return True if the prediction matches the next card."""
        if next_card.rank == current_card.rank:
            return False
        correct = (
            next_card.rank > current_card.rank
            if prediction == Prediction.HIGHER
            else next_card.rank < current_card.rank
        )
        return not correct if reverse else correct

    @staticmethod
    def _win_probability(
        odds: WinOdds, prediction: Prediction, reverse: bool
    ) -> float:
        """Return the win probability for a prediction."""
        if prediction == Prediction.HIGHER:
            return odds.lower if reverse else odds.higher
        return odds.higher if reverse else odds.lower

    def _apply_bonus_multiplier(self, payout: int) -> int:
        """Apply side-mission bonus multiplier when available."""
        if self._active_side_mission is None:
            return payout
        multiplier = self._active_side_mission.definition.bonus_multiplier
        if multiplier <= 1:
            return payout
        return payout * multiplier

    def _apply_win(self, payout: int, stake: int) -> None:
        """Apply winnings to the session."""
        self._session.balance += payout
        profit = payout - stake
        if profit > 0:
            self._session.total_credits += profit
        self._io.show_message(
            f"WIN +{profit} | Balance: {self._session.balance}",
            instant=True,
        )

    def _apply_loss(self, stake: int) -> None:
        """Apply a loss to the session."""
        self._io.show_message(
            f"LOSS -{stake} | Balance: {self._session.balance}",
            instant=True,
        )

    def _stake_amount(self) -> int:
        """Return the current stake amount."""
        return int(self._session.base_bet * self._session.upgrades.bet_multiplier())

    def _deal_card(self) -> Card:
        """Deal a card from the current deck."""
        if self._deck is None:
            raise RuntimeError("Deck is not initialised.")
        card = self._deck.deal()
        self._deck_watcher.notify(self._deck.remaining_cards())
        return card

    def _deal_starting_card(self) -> Card:
        """Deal a non-joker card to start a round."""
        while True:
            if self._deck is None or len(self._deck) == 0:
                self._prime_new_deck(initial=False)
            card = self._deal_card()
            if not card.is_joker:
                return card
            self._io.show_message(
                "Joker intercepted. Cycling buffer...",
                instant=True,
            )

    def _prime_new_deck(self, *, initial: bool) -> None:
        """Create and shuffle a fresh deck."""
        if not initial:
            self._show_reshuffle_sequence()
            self._record_deck_completion()
        jokers = self._BASE_JOKERS * self._session.upgrades.joker_multiplier()
        self._deck = Deck(include_jokers=True, jokers_count=jokers)
        self._deck.shuffle()
        self._deck_watcher.notify(self._deck.remaining_cards())
        self._handle_calibration()
        if not initial:
            self._remind_optional_menus()

    def _check_deck_depleted(self, next_card: Card | None = None) -> None:
        """Handle deck depletion after a round."""
        if self._deck is None or len(self._deck) == 0:
            self._prime_new_deck(initial=False)
            self._current_card = self._deal_starting_card()
            return
        if next_card is not None:
            self._current_card = next_card

    def _remind_optional_menus(self) -> None:
        """Remind the player about shop and settings."""
        if not self._session.visited_shop or not self._session.visited_settings:
            self._io.show_message(
                "Reminder: type 'shop' or 'settings' to upgrade your rig.",
                instant=True,
            )

    def _check_final_extraction(self) -> None:
        """Trigger the final extraction sequence if threshold is met."""
        if self._session.total_credits < self._FINAL_CREDITS:
            return
        self._final_extraction()
        self._state = GameState.TERMINATED

    def _final_extraction(self) -> None:
        """Play the final extraction cut scene."""
        self._io.clear_screen()
        lines = [
            "> Incoming secure channel...",
            "> [REDACTED]: Operator... do you see that spike?",
            "> That's it. One hundred million extracted.",
            "> Evil Corp's vault just flatlined.",
            "",
            "> You did what we couldn't. The money trail is severed.",
            "> Stand down, old friend. You've earned the shadows.",
            "",
            "> Mission status: COMPLETE.",
        ]
        for line in lines:
            self._io.show_message(line, speed=0.08)
        purge_art = [
            "===================================",
            "           SYSTEM PURGE            ",
            "===================================",
        ]
        for line in purge_art:
            self._io.show_message(line, instant=True)

    def _show_intro_story(self) -> None:
        """Display the espionage intro story."""
        story = [
            "> Incoming encrypted message...",
            "> Decrypting...",
            "",
            "\"Hey old friend. I know you're out of the game, but we need you.",
            " Evil Corp. Ring any bells? They're up to something catastrophic.",
            " We can't touch them legally - too well connected.",
            "",
            " But we found an opening. Their online casino has a card game called Higher or Lower.",
            " Our analysts found an exploit in the RNG.",
            " We've already patched your terminal with the algorithm.",
            "",
            " Your mission: Play Higher or Lower to drain them dry!",
            " Every dollar you take is a dollar they can't use for... whatever they're planning.",
            "",
            " The cards are in your favor now, operator.",
            " Good luck.",
            " - [REDACTED]\"",
            "",
        ]
        for line in story:
            self._io.show_message(line)
            time.sleep(0.5)
        title_art = [
            " _______   _______    ______   ______  __    __ ",
            "/       \ /       \  /      \ /      |/  \  /  |",
            "$$$$$$$  |$$$$$$$  |/$$$$$$  |$$$$$$/ $$  \ $$ |",
            "$$ |  $$ |$$ |__$$ |$$ |__$$ |  $$ |  $$$  \$$ |",
            "$$ |  $$ |$$    $$< $$    $$ |  $$ |  $$$$  $$ |",
            "$$ |  $$ |$$$$$$$  |$$$$$$$$ |  $$ |  $$ $$ $$ |",
            "$$ |__$$ |$$ |  $$ |$$ |  $$ | _$$ |_ $$ |$$$$ |",
            "$$    $$/ $$ |  $$ |$$ |  $$ |/ $$   |$$ | $$$ |",
            "$$$$$$$/  $$/   $$/ $$/   $$/ $$$$$$/ $$/   $$/ ",
            "                                                ",
            "                                                ",
            "                                                ",
            " ________  __    __  ________                   ",
            "/        |/  |  /  |/        |                  ",
            "$$$$$$$$/ $$ |  $$ |$$$$$$$$/                   ",
            "   $$ |   $$ |__$$ |$$ |__                      ",
            "   $$ |   $$    $$ |$$    |                     ",
            "   $$ |   $$$$$$$$ |$$$$$/                      ",
            "   $$ |   $$ |  $$ |$$ |_____                   ",
            "   $$ |   $$ |  $$ |$$       |                  ",
            "   $$/    $$/   $$/ $$$$$$$$/                   ",
            "                                                ",
            "                                                ",
            "                                                ",
            " __     __   ______   __    __  __     ________ ",
            "/  |   /  | /      \ /  |  /  |/  |   /        |",
            "$$ |   $$ |/$$$$$$  |$$ |  $$ |$$ |   $$$$$$$$/ ",
            "$$ |   $$ |$$ |__$$ |$$ |  $$ |$$ |      $$ |   ",
            "$$  \ /$$/ $$    $$ |$$ |  $$ |$$ |      $$ |   ",
            " $$  /$$/  $$$$$$$$ |$$ |  $$ |$$ |      $$ |   ",
            "  $$ $$/   $$ |  $$ |$$ \__$$ |$$ |_____ $$ |   ",
            "   $$$/    $$ |  $$ |$$    $$/ $$       |$$ |   ",
            "    $/     $$/   $$/  $$$$$$/  $$$$$$$$/ $$/    ",
            "                                                ",
            "                                                ",
            "                                                ",
            "",
            "DRAIN THE VAULT: INFINITE CARD COUNTER",
        ]
        for line in title_art:
            self._io.show_message(line, instant=True)
        system_lines = [
            "",
            "> SYSTEM INITIALIZED...",
            "> ACCESS GRANTED TO CASINO_CORE_V4.2",
            "> MISSION: DRAIN THE VAULT",
            "> INFO: Play higher or lower until you have drained the vault of Evil Corp.",
            "",
        ]
        for line in system_lines:
            self._io.show_message(line)

    def _show_rules(self) -> None:
        """Display the quick rules overview."""
        rules = [
            "HOW TO PLAY:",
            "- Predict higher or lower each round.",
            "- Equal ranks count as a loss.",
            "- Jokers trigger an automatic win.",
            "- Each round auto-stakes your base bet (upgraded via the shop).",
            "- Payouts scale with the odds and any Odds Augmenter upgrades.",
            "- Side missions trigger every 15 rounds (toggle in settings).",
            "- Calibration may be required between decks (toggle in settings).",
            "- Type 'shop' at any prompt to buy upgrades.",
            "- Type 'settings' at any prompt to toggle visuals, missions, and calibration",
            "- Type 'achievements' to view unlocked badges.",
            "- Type 'save' to write your session.",
            "- Type 'exit' to save and leave immediately.",
            "- Type 'help' to show all command shortcuts.",
            "NOTE: Every deck requires you to recalibrate. You will need a real physical deck.",
            "If this calibration with the camera is not working, toggle it off, or pay to skip.",
            "",
        ]
        for line in rules:
            self._io.show_message(line, instant=True)

    def _show_reshuffle_sequence(self) -> None:
        """Display the reshuffle sequence with typewriter effect."""
        lines = [
            "",
            "> DECK DEPLETED.",
            "> FORCING BUFFER RESET...",
            "> SHUFFLING NEW 52-CARD BLOCK.",
            "> ODDS RECALIBRATING...",
        ]
        for line in lines:
            self._io.show_message(line)

    def _handle_calibration(self) -> None:
        """Require a recalibration scan or outsourcing fee per deck."""
        if not self._session.calibration_enabled:
            return
        self._save_manager.save(self._session)
        if self._deck is None:
            return
        target_card = self._calibration_target_card()
        if target_card is None:
            return
        target_label = self._card_label_for_scanner(target_card)
        target_display = self._card_label_for_display(target_card)
        self._io.show_message(
            "[CALIBRATION] Recalibration required for this deck.",
            instant=True,
        )
        self._io.show_message(
            f"[CALIBRATION] Target card: {target_display}",
            instant=True,
        )
        while True:
            choice = self._io.get_input(
                "Scan card or pay to outsource [scan/pay] > "
            ).strip().lower()
            if choice in {"scan", "s"}:
                self._io.show_message(
                    "Please show the card requested up the camera.",
                    instant=True,
                )
                self._io.show_message(
                    "Launching scanner... Press 'q' to quit.",
                    instant=True,
                )
                try:
                    detected = scan_card(target_label=target_label)
                except RuntimeError as exc:
                    self._io.show_message(
                        "Calibration skipped: cant connect to the camera.",
                        instant=True,
                    )
                    self._io.show_message(str(exc), instant=True)
                    return
                if detected:
                    self._io.show_message(
                        f"Calibration locked on: {detected}",
                        instant=True,
                    )
                    return
                self._io.show_message(
                    "Scanner closed. Try again or pay to outsource.",
                    instant=True,
                )
                continue
            if choice in {"pay", "p", "outsource"}:
                fee = max(1, int(round(self._session.balance * 0.10)))
                self._session.balance = max(0, self._session.balance - fee)
                self._io.show_message(
                    f"Outsourced calibration. Fee deducted: {fee}.",
                    instant=True,
                )
                return
            self._io.show_message("Type 'scan' or 'pay' to continue.", instant=True)

    def _after_round(self, *, win: bool, win_probability: float) -> None:
        """Update counters and achievements after a round."""
        self._rounds_completed += 1
        if win:
            self._session.win_streak += 1
            self._session.max_win_streak = max(
                self._session.max_win_streak, self._session.win_streak
            )
            if self._session.win_streak >= 5:
                self._unlock_achievement("win_streak_5")
            if self._session.win_streak >= 10:
                self._unlock_achievement("win_streak_10")
            if win_probability < 0.10:
                self._unlock_achievement("statistical_anomaly")
        else:
            self._session.win_streak = 0
        self._check_credit_achievements()
        self._maybe_schedule_side_mission()

    def _maybe_schedule_side_mission(self) -> None:
        """Queue a side mission every interval."""
        if not self._session.side_missions_enabled:
            return
        if self._active_side_mission is not None or self._pending_side_mission is not None:
            return
        if self._rounds_completed == 0:
            return
        if self._rounds_completed % self._SIDE_MISSION_INTERVAL != 0:
            return
        self._pending_side_mission = self._side_mission_manager.random_definition()

    def _offer_side_mission(self) -> None:
        """Offer a queued side mission to the player."""
        if self._pending_side_mission is None:
            return
        if not self._session.side_missions_enabled:
            self._pending_side_mission = None
            return
        definition = self._pending_side_mission
        self._pending_side_mission = None

        self._io.show_message("", instant=True)
        self._io.show_message("=== SIDE MISSION ===", instant=True)
        self._io.show_message(definition.title, instant=True)
        for line in definition.description:
            self._io.show_message(f"- {line}", instant=True)
        if definition.skip_penalty_ratio is not None:
            percent = int(definition.skip_penalty_ratio * 100)
            self._io.show_message(
                f"Skip penalty: {percent}% of balance.",
                instant=True,
            )
        else:
            self._io.show_message("Skip this mission to forfeit the bonus.", instant=True)

        while True:
            raw_input = self._io.get_input("Accept mission? [Y/skip] > ").strip().lower()
            command_result = self._command_interpreter.interpret(
                raw_input, self._command_context
            )
            if command_result is not None:
                if self._apply_command_result(command_result):
                    self._pending_side_mission = definition
                    return
                continue
            if raw_input in {"", "y", "yes", "accept"}:
                self._active_side_mission = self._side_mission_manager.start(definition)
                self._io.show_message("Mission accepted.", instant=True)
                return
            if raw_input in {"skip", "s", "n", "no"}:
                self._apply_side_mission_skip(definition)
                return
            self._io.show_message("Type 'y' to accept or 'skip' to skip.", instant=True)

    def _apply_side_mission_skip(self, definition: SideMissionDefinition) -> None:
        """Apply skip consequences for a side mission."""
        if definition.skip_penalty_ratio is not None:
            fee = max(1, int(round(self._session.balance * definition.skip_penalty_ratio)))
            self._session.balance = max(0, self._session.balance - fee)
            self._io.show_message(
                f"Skip fee paid: {fee}. Mission aborted.",
                instant=True,
            )
            return
        self._io.show_message("Mission skipped. Bonus forfeited.", instant=True)

    def _update_side_mission_after_round(self, *, win: bool) -> None:
        """Advance or clear the current side mission after a round."""
        if self._active_side_mission is None:
            return
        mission = self._active_side_mission
        definition = mission.definition

        if definition.kind == SideMissionType.DOUBLE_OR_NOTHING:
            if win:
                mission.wins_in_row += 1
                if mission.wins_in_row >= definition.wins_required:
                    self._double_balance_reward()
                    mission.completed = True
                    mission.active = False
            else:
                mission.failed = True
                mission.active = False
        elif definition.kind == SideMissionType.BIG_MONEY:
            if win:
                mission.completed = True
            else:
                mission.failed = True
            mission.active = False
        elif definition.kind == SideMissionType.LUCKY_SEVEN:
            if win:
                mission.rounds_left -= 1
                if mission.rounds_left <= 0:
                    mission.completed = True
                    mission.active = False
            else:
                mission.failed = True
                mission.active = False
        elif definition.kind == SideMissionType.GONE_BLIND:
            mission.rounds_left -= 1
            if mission.rounds_left <= 0:
                mission.completed = True
                mission.active = False
        elif definition.kind == SideMissionType.REVERSE_PSYCHOLOGY:
            if win:
                mission.rounds_left -= 1
                if mission.rounds_left <= 0:
                    mission.completed = True
                    mission.active = False
            else:
                mission.failed = True
                mission.active = False

        if not mission.active:
            if mission.completed:
                self._unlock_achievement("shadow_operator")
                self._io.show_message("Side mission complete.", instant=True)
            else:
                self._io.show_message("Side mission ended.", instant=True)
            self._active_side_mission = None

    def _double_balance_reward(self) -> None:
        """Double the player's balance as a reward."""
        before = self._session.balance
        self._session.balance *= 2
        self._session.total_credits += before
        self._io.show_message(
            f"Double or Nothing success! Balance doubled to {self._session.balance}.",
            instant=True,
        )

    def _check_credit_achievements(self) -> None:
        """Unlock achievements tied to credits."""
        if self._session.total_credits >= 1_000_000:
            self._unlock_achievement("high_roller")
        if self._session.total_credits >= 100_000_000:
            self._unlock_achievement("vault_breaker")

    def _record_deck_completion(self) -> None:
        """Record deck completion and related achievements."""
        self._session.decks_completed += 1
        if self._session.decks_completed >= 1:
            self._unlock_achievement("first_deck")
        if self._session.decks_completed >= 5:
            self._unlock_achievement("long_haul")

    def _check_shop_achievement(self) -> None:
        """Unlock achievements tied to the shop."""
        if any(
            [
                self._session.upgrades.odds_level > 0,
                self._session.upgrades.bet_level > 0,
                self._session.upgrades.ai_counter,
                self._session.upgrades.joker_level > 0,
            ]
        ):
            self._unlock_achievement("first_purchase")
        if (
            self._session.upgrades.odds_level >= 7
            and self._session.upgrades.bet_level >= 7
            and self._session.upgrades.ai_counter
            and self._session.upgrades.joker_level >= 1
        ):
            self._unlock_achievement("market_manipulator")

    def _unlock_achievement(self, key: str) -> None:
        """Unlock an achievement and notify the player."""
        if self._session.achievements.get(key):
            return
        self._session.achievements[key] = True
        name = self._achievement_names.get(key, key)
        self._io.show_message(
            f"[ACHIEVEMENT UNLOCKED] {name}",
            instant=True,
        )
        self._save_manager.save(self._session)

    def _calibration_target_card(self) -> Card | None:
        """Pick a non-joker card to use for calibration."""
        if self._deck is None:
            return None
        candidates = [card for card in self._deck.remaining_cards() if not card.is_joker]
        if not candidates:
            return None
        return random.choice(candidates)

    def _card_label_for_scanner(self, card: Card) -> str:
        """Return the scanner label for a card (e.g., 4H, QS)."""
        rank_label = self._rank_label(card.rank)
        suit_label = {
            Suit.HEARTS: "H",
            Suit.DIAMONDS: "D",
            Suit.CLUBS: "C",
            Suit.SPADES: "S",
        }.get(card.suit, "J")
        return f"{rank_label}{suit_label}"

    @staticmethod
    def _card_label_for_display(card: Card) -> str:
        """Return the human-readable card label."""
        return str(card)

    @staticmethod
    def _rank_label(rank: Rank) -> str:
        """Return the scanner rank label."""
        if rank.value <= 10:
            return str(rank.value)
        return {
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }[rank]
