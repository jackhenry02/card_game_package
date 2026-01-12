"""Entry point for the infinite espionage card game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from logic.infinite_game import InfiniteGame
from logic.save_manager import SaveManager
from models.session import SessionData
from ui.spy_cli import SpyCLI


def main() -> None:
    """Run the infinite card game."""
    io_provider = SpyCLI()
    save_manager = SaveManager(ROOT / "session.json")
    session: SessionData | None = None
    resume = False

    if save_manager.exists():
        io_provider.show_message(
            "Saved session detected. Resume? (y/n)",
            instant=True,
        )
        choice = io_provider.get_input("> ").strip().lower()
        if choice in {"y", "yes"}:
            session = save_manager.load()
            if session is None:
                io_provider.show_message(
                    "Save file corrupt. Starting fresh.",
                    instant=True,
                )
            else:
                resume = True

    if session is None:
        session = SessionData()

    while True:
        io_provider.apply_visual_settings(session.visual)
        game = InfiniteGame(
            io_provider=io_provider,
            save_manager=save_manager,
            session=session,
            resume=resume,
        )
        game.run()
        save_manager.save(session)

        io_provider.show_message("Play again? (y/n)", instant=True)
        choice = io_provider.get_input("> ").strip().lower()
        if choice not in {"y", "yes"}:
            break
        resume = False
        new_session = SessionData()
        new_session.visual = session.visual
        new_session.side_missions_enabled = session.side_missions_enabled
        new_session.calibration_enabled = session.calibration_enabled
        session = new_session


if __name__ == "__main__":
    main()
