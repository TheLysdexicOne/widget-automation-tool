"""
Test grid coordinate system for automation.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utility.window_utils import calculate_pixel_size, grid_to_screen_coordinates


class TestGridCoordinates:
    """Test the grid coordinate system."""

    def test_grid_to_screen_basic(self):
        """Test basic grid to screen conversion."""
        # Mock playable area (300x200 pixels)
        playable_area = {"x": 100, "y": 50, "width": 300, "height": 200}

        # Grid (0,0) should be at top-left corner (center of first cell)
        screen_x, screen_y = grid_to_screen_coordinates(0, 0, playable_area)

        # Calculate expected values
        pixel_size = calculate_pixel_size(300, 200)  # min(300/192, 200/128) = min(1.56, 1.56) = 1.56
        expected_x = 100 + (0.5 * pixel_size)  # Center of first cell
        expected_y = 50 + (0.5 * pixel_size)

        assert screen_x == int(expected_x)
        assert screen_y == int(expected_y)

    def test_grid_to_screen_center(self):
        """Test grid center coordinates."""
        playable_area = {
            "x": 0,
            "y": 0,
            "width": 192,  # Exact grid size
            "height": 128,
        }

        # Grid (96,64) should be center of screen
        screen_x, screen_y = grid_to_screen_coordinates(96, 64, playable_area)

        # With exact grid size, pixel_size = 1.0
        # Center should be at (96.5, 64.5) -> (96, 64) when converted to int
        assert screen_x == 96
        assert screen_y == 64

    def test_grid_clamping(self):
        """Test that coordinates are clamped to valid range."""
        playable_area = {"x": 0, "y": 0, "width": 192, "height": 128}

        # Test coordinates beyond grid bounds
        screen_x, screen_y = grid_to_screen_coordinates(999, 999, playable_area)

        # Should clamp to (191, 127) which is the max valid grid coordinate
        # Center of cell (191, 127) should be at (191.5, 127.5) -> (191, 127)
        assert screen_x == 191
        assert screen_y == 127

    def test_empty_playable_area(self):
        """Test handling of empty playable area."""
        # Pass an explicitly empty playable area instead of None
        empty_area = {"x": 0, "y": 0, "width": 0, "height": 0}
        screen_x, screen_y = grid_to_screen_coordinates(50, 50, empty_area)
        assert screen_x == 0
        assert screen_y == 0

    def test_pixel_size_calculation(self):
        """Test pixel size calculation for different aspect ratios."""
        # Square aspect ratio (1:1) - height constrains
        pixel_size = calculate_pixel_size(300, 200)
        expected = min(300 / 192, 200 / 128)  # min(1.56, 1.56) = 1.56
        assert abs(pixel_size - expected) < 0.01

        # Wide aspect ratio - height constrains
        pixel_size = calculate_pixel_size(400, 200)
        expected = min(400 / 192, 200 / 128)  # min(2.08, 1.56) = 1.56
        assert abs(pixel_size - expected) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
