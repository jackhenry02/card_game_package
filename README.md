# Drain the Vault: Infinite Card Counter

A fast-paced, espionage-themed "Higher or Lower" card game written in Python
3.10+. The core loop is infinite, upgrade-driven, and designed to be extensible
for a future computer vision input mode.

## Quick start
Use:
```bash
source setup.sh
```
to create a virtual environment and install the requirements. Then run:

```bash
python main.py
```
to run the main game.

## Requirements
- Python 3.10+
- For optional computer vision calibration:
  - `numpy<2`
  - `ultralytics`


## How to play
- Each round you guess higher or lower.
- The game auto-stakes your base bet each round.
- Odds and payouts are hidden until you buy the AI Card Counter.
- Side missions trigger every 15 rounds (can be disabled in settings).
- Calibration using a physical deck can be required between decks (can be disabled in settings).
- Upgrades are available in the shop

## Aim of the game

**Reach 100 million credits and "drain the vault"**

In-game commands (available at any input prompt):
- `shop`: buy upgrades
- `settings`: toggle visuals and side missions
- `achievements`: view unlocked badges
- `save`: save your run
- `exit`: save and quit
- `help`: show commands

## Save data
- Progress is stored in `session.json` in the project root.
- Delete that file to reset the run manually.

## Design decisions 
- Separation of concerns: the game logic is independent from the CLI and could
  be swapped for a GUI or camera input later.
- Command pattern: input like `shop` or `settings` can interrupt the loop
  without polluting core gameplay logic.
- State pattern: explicit states keep the loop readable and easy to extend.
- Observer pattern: the AI Card Counter subscribes to deck updates and can be
  turned on by the player.
- JSON persistence: session state is fully serializable and resilient to new
  fields in future versions.

## YOLO weights source
- The playing card YOLOv8 weights were sourced from:
  - https://github.com/noorkhokhar99/Playing-Cards-Detection-with-YoloV8

## Ideas for improvement
- Add a GUI or web front end to replace the CLI. I could use Pygame to create a 'HUD' of sorts for the AI counter for instance.
- Improve testing.
- Improve aesthetics and pacing of game.
- Add balancing tools for payout curves and mission rewards.
- Improve the calibration functionality to work more seamlessly and robustly.
- Add analytics for player behavior and difficulty tuning.

## Workflow

I orginally coded up the base game, using OOP over functioning programming as this is a game, modelling the cards first, then the deck, then the game logic, then the interface, including ASCII art.

I then added a betting feauture, but was finding it very hard to make the player lose. I tried adding higher costs and worse odds to shorten the game, but it was difficult, slow, and long.

That is when the idea to do the opposite, and make the game easier instead, and make an 'infinite' game, similar to cookie clicker or another idle game. I made it faster paced, added a theme to it, and then just kept adding features until I ran out of time. that is why a lot of the file names are called "infinite_*" as this was added on top.

Hopefully you enjoy it! I have learnt a lot doing this project so hopefully it all makes sense under review, as a lot of it is new to me.