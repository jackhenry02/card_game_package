# Full Documentation

This document provides a structured overview of the codebase. I grouped the
modules by responsibility so it is easier to reason about the design choices
and how the system fits together.

## Entry Points

### main.py

Overview
- Purpose: The entrypoint for the infinite game. Handles save detection,
  resume flow, and replay logic.
- Scope: Orchestrates startup and replay; does not implement gameplay.

Design decisions
- Keep restart logic here so the engine can focus on gameplay only.

Walkthrough
1. Insert `src/` into `sys.path` for module imports.
2. Create `SpyCLI` and `SaveManager`.
3. If `session.json` exists, ask the player if they want to resume.
4. Start `InfiniteGame` with the resolved session and resume flag.
5. After the run, save state and ask "Play again?"
6. If replaying, create a fresh session but keep visual toggles so the player
   does not lose display preferences.

Why it matters
- Centralized replay logic prevents hidden state leaks and makes the game
  restart cleanly after each run.

How it is used
- Run the game with:
  - `python main.py`

## Model Files

### card.py

Overview
- Purpose: Represent a playing card with rank and suit.
- Scope: Immutable card model with ordering support.

Key pieces
- `Suit` enum:
  - Standard suits plus a JOKER value.
  - `label()` returns a readable string.
- `Rank` IntEnum:
  - 2-14 with Ace high, plus `JOKER=0`.
  - `label()` returns display text.
- `Card` dataclass (frozen):
  - Implements `__eq__` and `__lt__` for rank-based comparisons.
  - `is_joker` property simplifies joker checks.
  - `__str__` for readable output.

Design decisions
- Use `@total_ordering` to minimize comparison boilerplate.
- Make cards immutable to prevent accidental mutation.

### deck.py

Overview
- Purpose: Represent a deck of cards with shuffle and deal behavior.
- Scope: Supports standard decks plus optional jokers.

Key elements
- `DeckEmptyError`: custom exception when dealing from an empty deck.
- `Deck`:
  - `shuffle()`: in-place shuffle.
  - `deal()`: pop a card, raising if empty.
  - `remaining_cards()`: snapshot for odds or observers.
  - `_create_standard_deck()`: builds a 52-card deck with optional jokers.

Design decisions
- Keep deck logic self-contained so engines can inject custom decks for tests.
- Provide `remaining_cards()` for dynamic odds and AI counter support.

### achievements.py

Overview
- Purpose: Central registry for all achievements.
- Scope: Immutable definitions and helpers for default state.

Structure
- `AchievementDefinition`: frozen dataclass with key, name, description.
- `AchievementCatalog.DEFINITIONS`: tuple of all achievements.
- `default_state()`: returns all keys set to False.
- `merge_state(stored)`: merges saved data with any new definitions.

Design decisions
- Use a catalog to avoid hard-coding strings across the game.
- Merge logic protects old saves when new achievements are added.

### session.py

Overview
- Purpose: Store all persistent session state for the infinite game.
- Scope: Data-only models with explicit JSON serialization helpers.

Why this file exists
- The game needs to persist progress between runs. A dedicated session model
  keeps save/load logic simple and central.
- Using dataclasses keeps the data structure explicit and easy to extend.

Classes and fields
1. `VisualSettings`
   - `show_card_art`: Toggle ASCII card rendering.
   - `typewriter`: Toggle typewriter effect.
   - These are separated from gameplay settings so UI changes do not affect
     gameplay logic.

2. `UpgradeState`
   - `odds_level`: Levels that increase payout multiplier.
   - `bet_level`: Levels that increase stake amount.
   - `ai_counter`: Unlocks odds display.
   - `joker_level`: Controls how many jokers per deck.
   - Methods:
     - `odds_multiplier()`: Returns `2 ** odds_level`.
     - `bet_multiplier()`: Returns `2 ** bet_level`.
     - `joker_multiplier()`: Returns `2 ** joker_level`.
   - Multipliers are expressed as powers of two to make upgrade effects clear
     and predictable.

3. `SessionData`
   - Core economy:
     - `balance`: Current bankroll for the run.
     - `total_credits`: Lifetime extracted profit, used for ending and
       achievements.
     - `base_bet`: Default stake before upgrades.
   - Progress tracking:
     - `decks_completed`: Deck cycles finished.
     - `win_streak`: Current consecutive wins.
     - `max_win_streak`: Best streak achieved.
   - Feature toggles:
     - `side_missions_enabled`
     - `calibration_enabled`
   - UI state:
     - `visual` (VisualSettings)
   - Upgrades:
     - `upgrades` (UpgradeState)
   - Achievements:
     - `achievements`: Dict of achievement keys to bool.
   - Convenience flags:
     - `visited_shop`, `visited_settings` used to show reminders.

Serialization design
- `to_dict()` returns a plain Python dictionary for JSON persistence.
- `from_dict()` builds a safe, normalized `SessionData` instance and supplies
  defaults if keys are missing.
- `AchievementCatalog.merge_state()` keeps old saves compatible by merging the
  saved state with any new achievements that were added later.

Why this design
- Avoids tightly coupling persistence to game logic.
- Keeps upgrades and settings grouped logically.
- Supports forward compatibility for future features.

How it is used
- Loaded by `SaveManager` and passed into `InfiniteGame`.
- Mutated during play, then saved back to disk at key checkpoints.

## Logic Files

### achievements_menu.py

Overview
- Purpose: Show a read-only list of achievements and their status.
- Scope: Display logic only; unlocking is handled elsewhere.

Flow
1. Print section title.
2. Iterate over `AchievementCatalog.DEFINITIONS`.
3. Show each achievement as LOCKED or UNLOCKED.
4. Wait for Enter before returning.

Design decisions
- Keep the menu passive so it does not mutate session state.
- Use the catalog for a single source of truth.

### command_interpreter.py

Overview
- Purpose: Intercept and route text commands during gameplay.
- Scope: Command definitions and the interpreter that maps strings to actions.

Core concepts
- Command Pattern:
  - Each command implements `execute()` and returns a `CommandResult`.
  - Game logic simply checks for a result and acts on it.

Key pieces
1. `CommandContext`
   - Bundles shared services needed by commands:
     - IO provider
     - Session data
     - Save manager

2. `CommandResult`
   - `handled`: indicates if the input matched a command.
   - `next_state`: optional state transition (shop/settings/achievements).
   - `should_exit`: used to terminate the game loop.

3. `CommandInterpreter`
   - `interpret(raw_input, context)`:
     - Normalizes the input.
     - Looks up a command handler.
     - Executes it if found.

4. Command implementations
   - `ShopCommand`, `SettingsCommand`, `AchievementsCommand`
     - Transition the game to a submenu state.
   - `SaveCommand`
     - Persists the current session.
   - `ExitCommand`
     - Saves and requests termination.
   - `HelpCommand`
     - Prints available shortcuts.

Design decisions
- Use small command classes instead of if/elif logic in the engine.
- Commands are pure and operate only through the context.

Extending it
- Add a new class implementing `execute()`.
- Register the command in `InfiniteGame`'s interpreter map.

### game_state.py

Overview
- Purpose: Enumerate the states used by the infinite game loop.
- Scope: Defines the finite set of phases the engine can be in.

States
- STARTUP: introduction and initial deck.
- DEALING: main gameplay loop.
- SHOPPING: shop submenu.
- SETTINGS: settings submenu.
- ACHIEVEMENTS: achievements submenu.
- TERMINATED: end of game.

Why this exists
- Explicit states keep the main loop readable and safe.
- Adding new menus or screens is a straightforward enum expansion.

### infinite_game.py

Overview
- Purpose: The primary infinite higher/lower game engine.
- Scope: Game loop, side missions, calibration gating, achievements, payouts.
- Pattern usage: State, Command, Observer.

Key components
1. Game constants
   - `_HOUSE_EDGE`, `_FINAL_CREDITS`, `_BASE_JOKERS`,
     `_SIDE_MISSION_INTERVAL` tune economy and pacing.

2. `Prediction` enum
   - Encapsulates higher/lower inputs.
   - Validates user input and normalizes aliases.

3. `PayoutTable`
   - Holds stake and payout values for the current round.

Main loop
- `run()` executes a state machine:
  - STARTUP: shows intro, rules, initial deck.
  - DEALING: core loop for rounds.
  - SHOPPING/SETTINGS/ACHIEVEMENTS: suspend gameplay and return.
  - TERMINATED: exit loop.

Round flow (simplified)
1. Show HUD and current card (unless a blind mission hides it).
2. Compute odds via the AI counter (if unlocked).
3. Show odds only when AI counter is active.
4. Ask for prediction; allow command interception.
5. Deal next card, evaluate win/loss (reverse missions invert logic).
6. Apply payout, update stats, unlock achievements, update side missions.

Side missions
- Scheduled every N rounds.
- `SideMissionState` controls blind rounds, reverse logic, and bonuses.
- Skippable missions either forfeit rewards or apply penalties.

Calibration
- Runs once per deck (if enabled).
- Saves before prompting.
- Chooses a target card label (e.g., "4H", "QS") and waits until it is scanned.
- Uses `scan_card()` from `computer_vision.calibration`.
- Allows outsourcing for 10% of balance.

Achievements
- Stored in session.
- Triggered on milestones (streaks, credits, deck count, shop completion).
- Menu available via the `achievements` command.

Design decisions
- Keep IO abstracted behind `InfiniteIOProvider`.
- Keep mission definitions and observers separated into their own modules.
- Avoid tight coupling to CV logic; calibration is optional and isolated.

Extensibility notes
- Adding a new side mission is a data-only change in `side_missions.py`,
  plus resolution logic in `_update_side_mission_after_round`.
- Additional commands can be added to the interpreter mapping.

### observer.py

Overview
- Purpose: Observer pattern helpers plus the AI card counter.
- Scope: Track deck composition and compute odds.

Components
1. `WinOdds`
   - Holds higher, lower, and joker probabilities.

2. `DeckObserver` and `DeckWatcher`
   - `DeckWatcher` notifies observers whenever the deck changes.
   - Keeps the engine decoupled from any specific observer implementation.

3. `AICardCounter`
   - Tracks rank counts and joker count.
   - `win_odds(current_card)` computes exact probabilities based on remaining
     cards, including joker auto-win effects.

Design decisions
- Counting cards with `Counter` is fast and readable.
- Observer pattern allows new analytical tools to subscribe without modifying
  the core engine.

### save_manager.py

Overview
- Purpose: Read/write `SessionData` to disk as JSON.
- Scope: Small persistence wrapper with safe loading.

Key methods
- `exists()`: check if the save file is present.
- `load()`: parse JSON and build `SessionData`; returns None on failure.
- `save()`: serialize session to JSON with indentation and sorted keys.

Design decisions
- Keep persistence isolated from game logic for testability.
- Fail safely on corrupt or missing files.

### settings_menu.py

Overview
- Purpose: Toggle visual and optional mechanics during gameplay.
- Scope: Simple CLI loop that mutates session flags.

Settings managed
- Card art: show/hide ASCII card rendering.
- Typewriter effect: enable/disable animated output.
- Side missions: toggle mission system.
- Calibration: toggle deck-by-deck scan requirement.

Design decisions
- Settings are stored in `SessionData` so they persist across runs.
- Visual settings are applied immediately via `apply_visual_settings()`.

Why this matters
- Lets players tune the experience (fast pace vs cinematic).
- Keeps gameplay logic unaffected by UI preferences.

### shop.py

Overview
- Purpose: Handle the black-market shop flow and upgrades.
- Scope: Input loop, pricing rules, and upgrade mutations.

Shop items
- Odds Augmenter: doubles payout multiplier per level.
- Bet Amplifier: doubles stake per level.
- AI Card Counter: unlocks odds display.
- Double Jokers: increases joker count per deck.

Design decisions
- `ShopItem` is a frozen dataclass so definitions are immutable.
- Cost scales exponentially with level (base_cost * 2**level).
- Level caps prevent runaway multipliers.

Flow summary
1. Show current balance and item list.
2. Accept user choice.
3. Validate affordability and level caps.
4. Apply upgrade and deduct credits.
5. Save session after purchases.

Why it works this way
- Pricing and caps keep upgrades meaningful without infinite acceleration.
- Centralized menu logic keeps the game loop lean.

### side_missions.py

Overview
- Purpose: Define all side missions and track their runtime state.
- Scope: Data definitions only. Mission resolution happens in `infinite_game.py`.

Design choices
- Separate immutable mission definitions from mutable mission state.
- Use an enum for mission identifiers to avoid stringly-typed logic.
- Keep a single manager class to randomize selection.

Key types
1. `SideMissionType` (Enum)
   - Enumerates each supported mission:
     - `DOUBLE_OR_NOTHING`
     - `BIG_MONEY`
     - `LUCKY_SEVEN`
     - `GONE_BLIND`
     - `REVERSE_PSYCHOLOGY`

2. `SideMissionDefinition` (dataclass, frozen)
   - Immutable configuration for a mission.
   - Fields:
     - `kind`: The enum identifier.
     - `title`: Player-facing name.
     - `description`: Tuple of instruction lines.
     - `rounds`: Number of rounds the mission lasts.
     - `wins_required`: Number of consecutive wins required.
     - `bonus_multiplier`: Payout multiplier applied to wins.
     - `reverse_logic`: If True, incorrect guesses count as wins.
     - `blind_rounds`: If > 0, card and odds are hidden.
     - `skip_penalty_ratio`: Optional balance penalty for skipping.
   - This structure makes missions easy to add or modify without touching the
     game loop.

3. `SideMissionState` (dataclass)
   - Mutable state for an active mission.
   - Tracks progress and completion:
     - `rounds_left`, `wins_in_row`, `active`, `completed`, `failed`.
   - Helper methods:
     - `is_blind()` checks if the mission hides the current card.
     - `is_reverse()` checks if the mission reverses win logic.

4. `SideMissionManager`
   - Holds the list of mission definitions.
   - `random_definition()` returns a random mission.
   - `start()` wraps a definition into a `SideMissionState`, converting
     `rounds` or `wins_required` into the runtime counter.

How it is used
- `InfiniteGame` schedules a mission every N rounds and offers it to the
  player.
- When accepted, the mission state is stored and updated after each round.

## Interface Files

### infinite_io_provider.py

Overview
- Purpose: Define the IO contract for the infinite game.
- Scope: Abstract interface with messaging, input, and display methods.

Why this exists
- The engine should not care if the UI is a CLI, GUI, or camera input.
- Using an abstract interface enables dependency injection and testing.

Methods
- `show_message(message, instant=False, speed=None)`: output with optional
  typewriter control.
- `display_card(card)`: render a card.
- `get_input(prompt)`: collect user input.
- `clear_screen()`: clear terminal.
- `apply_visual_settings(settings)`: update UI toggles.

Design decisions
- Keep the interface minimal but expressive.
- Allow optional speed override for cinematic sequences.


## Computer Vision Files

### calibration.py

Overview
- Purpose: Provide a reusable function to scan a physical card using the
  YOLO model and webcam.
- Scope: Standalone helper that returns a stable card label or None.

How it works
1. Imports `cv2` and `YOLO` inside the function to keep imports optional.
2. Opens the webcam and runs inference per frame.
3. Uses a deque to stabilize detections over time.
4. Returns when a stable label matches the target (if provided).
5. Exits cleanly on q/Q/ESC and releases camera resources.

Design decisions
- Local imports avoid forcing CV dependencies on all users.
- Stability thresholds reduce flicker and false positives.

## UI Files

### spy_cli.py

Overview
- Purpose: Espionage-themed CLI for the infinite game.
- Scope: Rendering, ANSI styling, and typewriter effects.

Key features
- Card art reuses the classic ASCII template.
- Suit-based colorization and styled system messages.
- Configurable visual toggles via `apply_visual_settings()`.

Design decisions
- Keep all stylistic choices inside the UI layer.
- Allow instant output for fast-paced gameplay.
