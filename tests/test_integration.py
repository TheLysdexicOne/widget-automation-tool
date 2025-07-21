"""
Integration tests for frames functionality
"""

import pytest
import tempfile
from pathlib import Path

from frames.frames_manager import FramesManager


class TestFramesIntegration:
    """Integration tests for the complete frames system"""

    @pytest.fixture
    def temp_base_path(self):
        """Create a temporary base path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_complete_frame_workflow(self, temp_base_path):
        """Test complete frame creation and update workflow"""
        # Initialize frames manager
        frames_manager = FramesManager(temp_base_path)

        # Test adding a frame
        frame_data = {
            "name": "test_frame",
            "item": "test_item",
            "automation": 1,
            "text": [{"text": "sample text", "region": {"x": 10, "y": 10, "width": 100, "height": 50}}],
            "screenshots": [],
        }

        # Add frame
        result = frames_manager.add_frame(frame_data)
        assert result is True

        # Verify frame was added
        frames_list = frames_manager.get_frame_list()
        assert len(frames_list) == 1
        assert frames_list[0]["name"] == "test_frame"

        # Update frame
        updated_data = frame_data.copy()
        updated_data["item"] = "updated_item"
        result = frames_manager.update_frame("test_frame", updated_data)
        assert result is True

        # Verify update
        frames_list = frames_manager.get_frame_list()
        assert frames_list[0]["item"] == "updated_item"

    def test_screenshot_management(self, temp_base_path):
        """Test screenshot save and management"""
        from PIL import Image

        frames_manager = FramesManager(temp_base_path)

        # Create a test image
        test_image = Image.new("RGB", (100, 100), color="red")

        # Save screenshot
        screenshot_uuid = frames_manager.save_screenshot(test_image, "test_frame")
        assert screenshot_uuid is not None
        assert isinstance(screenshot_uuid, str)

        # Verify screenshot file was created
        screenshot_files = list(frames_manager.screenshots_dir.glob("*.png"))
        assert len(screenshot_files) > 0

        # Test deleting screenshot
        result = frames_manager.delete_screenshot(screenshot_uuid)
        assert isinstance(result, bool)

    def test_database_persistence(self, temp_base_path):
        """Test that frames data persists across manager instances"""
        # First manager instance
        frames_manager1 = FramesManager(temp_base_path)

        frame_data = {"name": "persistent_frame", "item": "test_item", "automation": 0, "text": [], "screenshots": []}

        frames_manager1.add_frame(frame_data)

        # Create second manager instance (should load existing data)
        frames_manager2 = FramesManager(temp_base_path)
        frames_list = frames_manager2.get_frame_list()

        assert len(frames_list) == 1
        assert frames_list[0]["name"] == "persistent_frame"

    def test_frame_retrieval(self, temp_base_path):
        """Test frame retrieval by name"""
        frames_manager = FramesManager(temp_base_path)

        frame_data = {"name": "searchable_frame", "item": "test_item", "automation": 1, "text": [], "screenshots": []}

        frames_manager.add_frame(frame_data)

        # Test getting frame by name
        retrieved_frame = frames_manager.get_frame_by_name("searchable_frame")
        assert retrieved_frame is not None
        assert retrieved_frame["name"] == "searchable_frame"

        # Test getting non-existent frame
        missing_frame = frames_manager.get_frame_by_name("non_existent")
        assert missing_frame is None
