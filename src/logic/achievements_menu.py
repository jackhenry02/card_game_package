"""Achievements menu for the infinite game."""
from __future__ import annotations

from interfaces.infinite_io_provider import InfiniteIOProvider
from models.achievements import AchievementCatalog
from models.session import SessionData


class AchievementsMenu:
    """Displays unlocked achievements."""

    def open(self, io_provider: InfiniteIOProvider, session: SessionData) -> None:
        """Render the achievements list.

        Args:
            io_provider: IO provider for rendering.
            session: Session data containing achievement state.
        """
        io_provider.show_message("", instant=True)
        io_provider.show_message("=== ACHIEVEMENTS ===", instant=True)
        for achievement in AchievementCatalog.DEFINITIONS:
            unlocked = session.achievements.get(achievement.key, False)
            status = "UNLOCKED" if unlocked else "LOCKED"
            io_provider.show_message(
                f"[{status}] {achievement.name} - {achievement.description}",
                instant=True,
            )
        io_provider.get_input("Press Enter to return...")
