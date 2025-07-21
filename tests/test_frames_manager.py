"""
Tests for frames data manager functionality
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from frames.frames_manager import FramesManager


class TestFramesManager:
    """Test the FramesManager class"""

    @pytest.fixture
    def temp_base_path(self):
        """Create a temporary base path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def frames_manager(self, temp_base_path):
        """Create a FramesManager instance for testing"""
        return FramesManager(temp_base_path)

    def test_init(self, frames_manager):
        """Test FramesManager initialization"""
        assert frames_manager is not None
        assert frames_manager.screenshots_dir.exists()

    def test_get_frame_list_empty(self, frames_manager):
        """Test getting frame list when empty"""
        with patch.object(frames_manager, "_load_frames_database", return_value={}):
            result = frames_manager.get_frame_list()
            assert result == []

    def test_get_frame_list_with_data(self, frames_manager):
        """Test getting frame list with data"""
        frames_manager.frames_data = {"frames": [{"name": "test_frame", "item": "test_item", "automation": 1}]}
        result = frames_manager.get_frame_list()
        assert len(result) == 1
        assert result[0]["name"] == "test_frame"

    def test_update_frame(self, frames_manager):
        """Test updating a frame"""
        original_data = {"frames": [{"name": "test_frame", "item": "test_item", "automation": 1}]}
        updated_frame_data = {"frames": [{"name": "test_frame", "item": "new_item", "automation": 1}]}

        with patch.object(frames_manager, "_load_frames_database", return_value=original_data):
            with patch.object(frames_manager, "_save_frames_database") as mock_save:
                result = frames_manager.update_frame("test_frame", updated_frame_data)
                assert result is True
                mock_save.assert_called_once()

    def test_save_screenshot(self, frames_manager, temp_base_path):
        """Test saving a screenshot"""
        from PIL import Image

        # Create a test image
        test_image = Image.new("RGB", (100, 100), color="red")

        result = frames_manager.save_screenshot(test_image, "test_frame")
        assert result is not None
        assert isinstance(result, str)

        # Check that a file was created
        screenshot_files = list(frames_manager.screenshots_dir.glob("*.png"))
        assert len(screenshot_files) > 0
