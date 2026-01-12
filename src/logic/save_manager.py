"""Persistence helpers for the infinite game session."""
from __future__ import annotations

import json
from pathlib import Path

from models.session import SessionData


class SaveManager:
    """Handles loading and saving session data to disk."""

    def __init__(self, path: Path) -> None:
        """Initialise with a filesystem path.

        Args:
            path: Path to the session file.
        """
        self._path = path

    def exists(self) -> bool:
        """Return True if a saved session exists."""
        return self._path.exists()

    def load(self) -> SessionData | None:
        """Load session data from disk.

        Returns:
            The loaded SessionData, or None if unavailable/corrupt.
        """
        if not self._path.exists():
            return None
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        return SessionData.from_dict(raw)

    def save(self, session: SessionData) -> None:
        """Write the current session to disk.

        Args:
            session: Session data to persist.
        """
        payload = json.dumps(session.to_dict(), indent=2, sort_keys=True)
        self._path.write_text(payload, encoding="utf-8")
