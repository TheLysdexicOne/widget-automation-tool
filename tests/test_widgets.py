"""
Tests for frames widgets functionality
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from frames.screenshot_manager import ScreenshotManagerDialog
from frames.widgets.edit_frames_dialog import EditFramesDialog, ScreenshotGalleryWidget
from frames.frames_manager import FramesManager


class TestScreenshotManagerDialog:
    """Test the ScreenshotManagerDialog class"""

    @pytest.fixture
    def temp_base_path(self):
        """Create a temporary base path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def frames_manager(self, temp_base_path):
        """Create a mock frames manager for testing"""
        manager = FramesManager(temp_base_path)
        return manager

    @pytest.fixture
    def sample_frame_data(self):
        """Create sample frame data for testing"""
        return {
            "name": "test_frame",
            "item": "test_item",
            "automation": 1,
            "screenshots": ["uuid1", "uuid2", "uuid3"],
            "text": [],
        }

    @pytest.fixture
    def parent_widget(self):
        """Create a mock parent widget"""
        mock_parent = Mock()
        mock_parent._capture_playable_screenshot = Mock(return_value=None)
        return mock_parent

    def test_dialog_creation(self, qapp, sample_frame_data, frames_manager, parent_widget):
        """Test creating the screenshot manager dialog"""
        dialog = ScreenshotManagerDialog(sample_frame_data, frames_manager, parent_widget)

        assert dialog is not None
        assert dialog.frame_data == sample_frame_data
        assert dialog.frames_manager == frames_manager
        assert len(dialog.current_screenshots) == 3

    def test_primary_screenshot_detection(self, qapp, sample_frame_data, frames_manager, parent_widget):
        """Test primary screenshot detection"""

        # Mock get_screenshot_data to return primary flag for uuid2
        def mock_get_screenshot_data(uuid):
            if uuid == "uuid2":
                return {"is_primary": True}
            return {"is_primary": False}

        frames_manager.get_screenshot_data = Mock(side_effect=mock_get_screenshot_data)

        dialog = ScreenshotManagerDialog(sample_frame_data, frames_manager, parent_widget)

        assert dialog.primary_screenshot == "uuid2"

    def test_make_primary(self, qapp, sample_frame_data, frames_manager, parent_widget):
        """Test making a screenshot primary"""
        dialog = ScreenshotManagerDialog(sample_frame_data, frames_manager, parent_widget)

        # Select a screenshot and make it primary
        dialog.selected_screenshots.add("uuid3")
        dialog._make_primary()

        assert dialog.primary_screenshot == "uuid3"
        assert len(dialog.selected_screenshots) == 0

    def test_delete_selected(self, qapp, sample_frame_data, frames_manager, parent_widget):
        """Test marking screenshots for deletion"""
        dialog = ScreenshotManagerDialog(sample_frame_data, frames_manager, parent_widget)

        # Select screenshots for deletion
        dialog.selected_screenshots.add("uuid2")
        dialog._delete_selected()

        assert "uuid2" in dialog.marked_for_deletion


class TestEditFramesDialog:
    """Test the EditFramesDialog class"""

    @pytest.fixture
    def temp_base_path(self):
        """Create a temporary base path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_frames_list(self):
        """Create sample frames list for testing"""
        return [
            {
                "id": "1.1",
                "name": "frame1",
                "item": "item1",
                "automation": 1,
                "screenshots": ["uuid1"],
                "text": [{"text": "test text", "region": {"x": 10, "y": 10, "width": 100, "height": 50}}],
            },
            {
                "id": "1.2",
                "name": "frame2",
                "item": "item2",
                "automation": 0,
                "screenshots": ["uuid2", "uuid3"],
                "text": [],
            },
        ]

    def test_dialog_creation(self, qapp, sample_frames_list, temp_base_path):
        """Test creating the edit frames dialog"""
        screenshots_dir = temp_base_path / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

        dialog = EditFramesDialog(sample_frames_list, screenshots_dir)

        assert dialog is not None
        assert dialog.frames_list == sample_frames_list
        assert dialog.screenshots_dir == screenshots_dir

    def test_frame_sorting(self, qapp, sample_frames_list, temp_base_path):
        """Test that frames are sorted by tier ID"""
        screenshots_dir = temp_base_path / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

        # Add frame with higher ID to test sorting
        sample_frames_list.append(
            {"id": "2.1", "name": "frame3", "item": "item3", "automation": 0, "screenshots": [], "text": []}
        )

        dialog = EditFramesDialog(sample_frames_list, screenshots_dir)

        # Check that frames list widget has items in correct order
        assert dialog.frames_list_widget.count() == 3
        item0 = dialog.frames_list_widget.item(0)
        item1 = dialog.frames_list_widget.item(1)
        item2 = dialog.frames_list_widget.item(2)

        if item0:
            assert "1.1" in item0.text()
        if item1:
            assert "1.2" in item1.text()
        if item2:
            assert "2.1" in item2.text()


class TestScreenshotGalleryWidget:
    """Test the ScreenshotGalleryWidget class"""

    @pytest.fixture
    def temp_screenshots_dir(self):
        """Create a temporary screenshots directory with test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshots_dir = Path(temp_dir)

            # Create dummy screenshot files
            (screenshots_dir / "screenshot_uuid1_123.png").touch()
            (screenshots_dir / "screenshot_uuid2_456.png").touch()

            yield screenshots_dir

    def test_widget_creation(self, qapp, temp_screenshots_dir):
        """Test creating the screenshot gallery widget"""
        screenshots = ["uuid1", "uuid2"]

        widget = ScreenshotGalleryWidget(screenshots, temp_screenshots_dir)

        assert widget is not None
        assert widget.screenshots == screenshots
        assert widget.screenshots_dir == temp_screenshots_dir

    def test_empty_screenshots(self, qapp, temp_screenshots_dir):
        """Test widget with no screenshots"""
        widget = ScreenshotGalleryWidget([], temp_screenshots_dir)

        assert widget is not None
        assert len(widget.screenshots) == 0

    def test_mark_for_deletion(self, qapp, temp_screenshots_dir):
        """Test marking screenshots for deletion"""
        screenshots = ["uuid1", "uuid2"]
        widget = ScreenshotGalleryWidget(screenshots, temp_screenshots_dir)

        # Simulate marking for deletion
        widget._on_delete_clicked("uuid1", Mock())

        assert "uuid1" in widget.marked_for_deletion

        # Simulate unmarking for deletion
        widget._on_delete_clicked("uuid1", Mock())

        assert "uuid1" not in widget.marked_for_deletion
