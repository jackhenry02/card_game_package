"""Additional tests for SaveManager."""
from pathlib import Path

from logic.save_manager import SaveManager
from models.session import SessionData


def test_save_manager_exists(tmp_path: Path):
    """exists() should reflect file presence."""
    path = tmp_path / "session.json"
    manager = SaveManager(path)
    assert manager.exists() is False
    manager.save(SessionData())
    assert manager.exists() is True


def test_save_manager_load_invalid(tmp_path: Path):
    """Invalid JSON should return None."""
    path = tmp_path / "session.json"
    path.write_text("not-json", encoding="utf-8")
    manager = SaveManager(path)
    assert manager.load() is None
