"""
Simple smoke tests for basic functionality
"""

import pytest
import tempfile
from pathlib import Path

from frames.frames_manager import FramesManager


def test_frames_manager_initialization():
    """Test that FramesManager can be initialized successfully"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = FramesManager(temp_path)

        assert manager is not None
        assert manager.base_path == temp_path
        assert manager.screenshots_dir.exists()
        assert manager.frames_db_path.parent.exists()


def test_screenshot_directory_creation():
    """Test that screenshot directory is created properly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = FramesManager(temp_path)

        # Directory should be created during initialization
        expected_dir = temp_path / "assets" / "screenshots"
        assert expected_dir.exists()
        assert expected_dir == manager.screenshots_dir


def test_frames_database_path():
    """Test that frames database path is set correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = FramesManager(temp_path)

        expected_path = temp_path / "src" / "config" / "frames_database.json"
        assert expected_path == manager.frames_db_path
        assert expected_path.parent.exists()  # Directory should be created


def test_empty_frames_list():
    """Test getting empty frames list on new installation"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = FramesManager(temp_path)

        frames_list = manager.get_frame_list()
        assert isinstance(frames_list, list)
        assert len(frames_list) == 0  # Should be empty for new installation


def test_get_screenshot_data_method():
    """Test that get_screenshot_data method exists and works"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = FramesManager(temp_path)

        # Test the method exists and returns expected structure
        result = manager.get_screenshot_data("dummy_uuid")
        assert isinstance(result, dict)
        assert "is_primary" in result


@pytest.mark.skipif(True, reason="Requires PyQt6 application context")
def test_import_widgets():
    """Test that widget imports work correctly"""
    try:
        from frames.screenshot_manager import ScreenshotManagerDialog
        from frames.widgets.edit_frames_dialog import EditFramesDialog, ScreenshotGalleryWidget

        # If we get here without import errors, the imports are working
        assert ScreenshotManagerDialog is not None
        assert EditFramesDialog is not None
        assert ScreenshotGalleryWidget is not None
    except ImportError as e:
        pytest.fail(f"Widget imports failed: {e}")


def test_project_structure():
    """Test that the expected project structure exists"""
    project_root = Path(__file__).parent.parent

    # Check for key directories and files
    expected_paths = [
        project_root / "src" / "frames" / "data_manager.py",
        project_root / "src" / "frames" / "menu_system.py",
        project_root / "src" / "frames" / "widgets" / "screenshot_manager_dialog.py",
        project_root / "src" / "frames" / "widgets" / "edit_frames_dialog.py",
        project_root / "tests",
        project_root / ".vscode" / "settings.json",
    ]

    for path in expected_paths:
        assert path.exists(), f"Expected path does not exist: {path}"
