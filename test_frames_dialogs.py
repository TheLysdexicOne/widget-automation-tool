#!/usr/bin/env python3
"""
Test script for frames dialog functionality.
Tests the Screenshot Manager and Edit Frames dialogs with simulated interactions.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit here, let pytest handle cleanup


@pytest.fixture
def mock_frames_manager():
    """Create a mock FramesManager for testing."""
    from frames.frames_manager import FramesManager

    manager = Mock(spec=FramesManager)
    manager.screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"

    # Mock screenshot data
    manager.get_screenshot_data.return_value = {"is_primary": True, "uuid": "test-uuid-123"}

    # Mock frame list
    manager.get_frame_list.return_value = [
        {
            "id": "1.1",
            "name": "Test Frame",
            "item": "Test Item",
            "automation": 1,
            "screenshots": ["test-uuid-123", "test-uuid-456"],
            "text": [{"text": "Test Region", "region": {"x": 10, "y": 20, "width": 100, "height": 50}}],
        }
    ]

    manager.update_frame.return_value = True
    manager.delete_screenshot.return_value = True

    return manager


@pytest.fixture
def sample_frame_data():
    """Sample frame data for testing."""
    return {
        "id": "1.1",
        "name": "Test Frame",
        "item": "Test Item",
        "automation": 1,
        "screenshots": ["test-uuid-123", "test-uuid-456"],
        "text": [{"text": "Test Region", "region": {"x": 10, "y": 20, "width": 100, "height": 50}}],
    }


class TestScreenshotManagerDialog:
    """Test cases for Screenshot Manager Dialog."""

    def test_screenshot_manager_dialog_init(self, qapp, mock_frames_manager, sample_frame_data):
        """Test Screenshot Manager Dialog initialization."""
        from frames.screenshot_manager import ScreenshotManagerDialog

        # Create parent widget mock
        parent_widget = Mock()
        parent_widget._capture_playable_screenshot = Mock(return_value=None)

        dialog = ScreenshotManagerDialog(sample_frame_data, mock_frames_manager, parent_widget)

        assert dialog.frame_data == sample_frame_data
        assert dialog.frames_manager == mock_frames_manager
        assert dialog.windowTitle() == "Screenshot Manager - Test Frame"
        assert len(dialog.current_screenshots) == 2

    def test_screenshot_manager_primary_selection(self, qapp, mock_frames_manager, sample_frame_data):
        """Test primary screenshot selection functionality."""
        from frames.screenshot_manager import ScreenshotManagerDialog

        parent_widget = Mock()
        dialog = ScreenshotManagerDialog(sample_frame_data, mock_frames_manager, parent_widget)

        # Test primary screenshot identification
        assert dialog.primary_screenshot == "test-uuid-123"  # First screenshot becomes primary

        # Test make primary functionality
        dialog.selected_screenshots.add("test-uuid-456")
        dialog._make_primary()

        assert dialog.primary_screenshot == "test-uuid-456"
        assert len(dialog.selected_screenshots) == 0  # Selection should clear after making primary

    def test_screenshot_manager_deletion_marking(self, qapp, mock_frames_manager, sample_frame_data):
        """Test screenshot deletion marking functionality."""
        from frames.screenshot_manager import ScreenshotManagerDialog

        parent_widget = Mock()
        dialog = ScreenshotManagerDialog(sample_frame_data, mock_frames_manager, parent_widget)

        # Test marking for deletion (non-primary)
        dialog.selected_screenshots.add("test-uuid-456")
        dialog._delete_selected()

        assert "test-uuid-456" in dialog.marked_for_deletion

        # Test can't delete primary
        dialog.selected_screenshots.add("test-uuid-123")
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
            dialog._delete_selected()
            mock_warning.assert_called_once()

        assert "test-uuid-123" not in dialog.marked_for_deletion

    def test_screenshot_manager_save_changes(self, qapp, mock_frames_manager, sample_frame_data):
        """Test save changes functionality."""
        from frames.screenshot_manager import ScreenshotManagerDialog

        parent_widget = Mock()
        dialog = ScreenshotManagerDialog(sample_frame_data, mock_frames_manager, parent_widget)

        # Mark screenshot for deletion
        dialog.marked_for_deletion.add("test-uuid-456")

        # Mock the accept method to avoid actual dialog closing
        dialog.accept = Mock()

        with patch("PyQt6.QtWidgets.QMessageBox.information"):
            dialog._save_changes()

        # Verify frame was updated with remaining screenshots
        mock_frames_manager.update_frame.assert_called_once()
        mock_frames_manager.delete_screenshot.assert_called_once_with("test-uuid-456")


class TestEditFramesDialog:
    """Test cases for Edit Frames Dialog."""

    def test_edit_frames_dialog_init(self, qapp, mock_frames_manager):
        """Test Edit Frames Dialog initialization."""
        from frames.widgets.edit_frames_dialog import EditFramesDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"
        frames_list = mock_frames_manager.get_frame_list()

        dialog = EditFramesDialog(frames_list, screenshots_dir)

        assert dialog.frames_list == frames_list
        assert dialog.screenshots_dir == screenshots_dir
        assert dialog.windowTitle() == "Edit Frames"
        assert dialog.frames_list_widget.count() == 1  # One test frame

    def test_edit_frames_frame_selection(self, qapp, mock_frames_manager):
        """Test frame selection in Edit Frames Dialog."""
        from frames.widgets.edit_frames_dialog import EditFramesDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"
        frames_list = mock_frames_manager.get_frame_list()

        dialog = EditFramesDialog(frames_list, screenshots_dir)

        # Simulate selecting first frame
        first_item = dialog.frames_list_widget.item(0)
        dialog._on_frame_selected(first_item)

        assert dialog.selected_frame is not None
        assert dialog.item_edit.text() == "Test Item"
        assert dialog.frame_edit.text() == "Test Frame"
        assert dialog.automation_checkbox.isChecked() == True
        assert dialog.save_button.isEnabled() == True

    def test_edit_frames_save_changes(self, qapp, mock_frames_manager):
        """Test save changes in Edit Frames Dialog."""
        from frames.widgets.edit_frames_dialog import EditFramesDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"
        frames_list = mock_frames_manager.get_frame_list()

        dialog = EditFramesDialog(frames_list, screenshots_dir)

        # Select frame and modify data
        first_item = dialog.frames_list_widget.item(0)
        dialog._on_frame_selected(first_item)

        dialog.item_edit.setText("Modified Item")
        dialog.frame_edit.setText("Modified Frame")
        dialog.automation_checkbox.setChecked(False)

        # Mock the accept method
        dialog.accept = Mock()

        dialog._save_changes()

        # Verify modified data
        original_name, modified_data, screenshots_to_delete = dialog.get_modified_data()
        assert original_name == "Test Frame"
        assert modified_data["name"] == "Modified Frame"
        assert modified_data["item"] == "Modified Item"
        assert modified_data["automation"] == 0


class TestEditFrameDialog:
    """Test cases for Edit Frame Dialog (single frame editor)."""

    def test_edit_frame_dialog_init(self, qapp, sample_frame_data):
        """Test Edit Frame Dialog initialization."""
        from frames.widgets.edit_frame_dialog import EditFrameDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"

        dialog = EditFrameDialog(sample_frame_data, screenshots_dir)

        assert dialog.frame_data == sample_frame_data
        assert dialog.windowTitle() == "Edit Frame: Test Frame"
        assert dialog.item_edit.text() == "Test Item"
        assert dialog.frame_edit.text() == "Test Frame"
        assert dialog.automation_checkbox.isChecked() == True

    def test_edit_frame_dialog_text_regions(self, qapp, sample_frame_data):
        """Test text regions handling in Edit Frame Dialog."""
        from frames.widgets.edit_frame_dialog import EditFrameDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"

        dialog = EditFrameDialog(sample_frame_data, screenshots_dir)

        # Check that text region was loaded
        assert len(dialog.regions) == 3  # Always creates 3 region slots
        assert dialog.regions[0]["text_edit"].text() == "Test Region"
        assert "10" in dialog.regions[0]["coord_label"].text()  # Contains x coordinate

    def test_edit_frame_dialog_save_changes(self, qapp, sample_frame_data):
        """Test save changes in Edit Frame Dialog."""
        from frames.widgets.edit_frame_dialog import EditFrameDialog

        screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"

        dialog = EditFrameDialog(sample_frame_data, screenshots_dir)

        # Modify data
        dialog.item_edit.setText("New Item")
        dialog.frame_edit.setText("New Frame")
        dialog.automation_checkbox.setChecked(False)

        # Mock the accept method
        dialog.accept = Mock()

        dialog._save_changes()

        # Verify modified data
        modified_data, screenshots_to_delete = dialog.get_modified_data()
        assert modified_data["name"] == "New Frame"
        assert modified_data["item"] == "New Item"
        assert modified_data["automation"] == 0
        assert len(modified_data["text"]) == 1  # One text region with data


def test_dialog_integration(qapp, mock_frames_manager, sample_frame_data):
    """Integration test for dialog workflows."""
    print("🧪 Testing Dialog Integration")

    # Test Screenshot Manager workflow
    from frames.screenshot_manager import ScreenshotManagerDialog

    parent_widget = Mock()
    screenshot_dialog = ScreenshotManagerDialog(sample_frame_data, mock_frames_manager, parent_widget)

    # Simulate user workflow
    screenshot_dialog.selected_screenshots.add("test-uuid-456")
    screenshot_dialog._make_primary()
    assert screenshot_dialog.primary_screenshot == "test-uuid-456"

    # Test Edit Frames workflow
    from frames.widgets.edit_frames_dialog import EditFramesDialog

    screenshots_dir = Path(__file__).parent / "assets" / "backgrounds"
    frames_list = mock_frames_manager.get_frame_list()

    edit_dialog = EditFramesDialog(frames_list, screenshots_dir)
    first_item = edit_dialog.frames_list_widget.item(0)
    edit_dialog._on_frame_selected(first_item)

    assert edit_dialog.selected_frame is not None

    print("✅ Dialog integration test passed!")


if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v", "--tb=short"])
