"""Settings menu for visual adjustments."""
from __future__ import annotations

from interfaces.infinite_io_provider import InfiniteIOProvider
from models.session import SessionData


class SettingsMenu:
    """Handles settings toggles for the CLI."""

    def open(self, io_provider: InfiniteIOProvider, session: SessionData) -> None:
        """Run the settings loop.

        Args:
            io_provider: IO provider for rendering.
            session: Session data to mutate.
        """
        session.visited_settings = True
        while True:
            io_provider.show_message("", instant=True)
            io_provider.show_message("=== VISUAL SETTINGS ===", instant=True)
            io_provider.show_message(
                f"1) Card art: {'ON' if session.visual.show_card_art else 'OFF'}",
                instant=True,
            )
            io_provider.show_message(
                f"2) Typewriter effect: {'ON' if session.visual.typewriter else 'OFF'}",
                instant=True,
            )
            io_provider.show_message(
                f"3) Side missions: {'ON' if session.side_missions_enabled else 'OFF'}",
                instant=True,
            )
            io_provider.show_message(
                f"4) Calibration: {'ON' if session.calibration_enabled else 'OFF'}",
                instant=True,
            )
            io_provider.show_message("B) Back to mission", instant=True)

            choice = io_provider.get_input("Select an option: ").strip().lower()
            if choice in {"b", "back", "exit"}:
                break
            if choice == "1":
                session.visual.show_card_art = not session.visual.show_card_art
                io_provider.apply_visual_settings(session.visual)
                continue
            if choice == "2":
                session.visual.typewriter = not session.visual.typewriter
                io_provider.apply_visual_settings(session.visual)
                continue
            if choice == "3":
                session.side_missions_enabled = not session.side_missions_enabled
                continue
            if choice == "4":
                session.calibration_enabled = not session.calibration_enabled
                continue
            io_provider.show_message("Unknown selection.", instant=True)
