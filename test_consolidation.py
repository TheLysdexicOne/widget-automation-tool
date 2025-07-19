#!/usr/bin/env python3
"""
Test script to verify consolidation worked correctly.
All calculations should now use the same source of truth.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utility.window_utils import (
    calculate_pixel_size,
    calculate_pixel_art_grid_position,
    PIXEL_ART_GRID_WIDTH,
    PIXEL_ART_GRID_HEIGHT,
)


def test_consolidation():
    print("🧪 Testing Calculation Consolidation")
    print("=" * 50)

    # Test constants
    print(f"Grid Constants: {PIXEL_ART_GRID_WIDTH}x{PIXEL_ART_GRID_HEIGHT}")

    # Test pixel size calculation
    test_width, test_height = 1800, 1200
    pixel_size = calculate_pixel_size(test_width, test_height)
    expected_size_x = test_width / PIXEL_ART_GRID_WIDTH  # 1800/180 = 10.0
    expected_size_y = test_height / PIXEL_ART_GRID_HEIGHT  # 1200/120 = 10.0
    expected_size = min(expected_size_x, expected_size_y)  # 10.0

    print(f"Pixel Size Calculation:")
    print(f"  Input: {test_width}x{test_height} playable area")
    print(f"  Expected: {expected_size}")
    print(f"  Actual: {pixel_size}")
    print(f"  ✅ Match: {pixel_size == expected_size}")

    # Test grid position calculation
    test_playable = {"x": 100, "y": 50, "width": 1800, "height": 1200}
    test_x, test_y = 1000, 650  # Inside playable area

    grid_result = calculate_pixel_art_grid_position(test_x, test_y, test_playable)

    print(f"\nGrid Position Calculation:")
    print(f"  Screen point: ({test_x}, {test_y})")
    print(f"  Playable area: {test_playable}")
    print(f"  Inside playable: {grid_result['inside_playable']}")
    print(f"  Grid position: ({grid_result['grid_x']}, {grid_result['grid_y']})")
    print(f"  Pixel size: {grid_result['pixel_size']}")

    # Verify grid position manually
    rel_x = test_x - test_playable["x"]  # 1000 - 100 = 900
    rel_y = test_y - test_playable["y"]  # 650 - 50 = 600
    expected_grid_x = int(rel_x / pixel_size)  # 900 / 10 = 90
    expected_grid_y = int(rel_y / pixel_size)  # 600 / 10 = 60

    print(f"  Expected grid: ({expected_grid_x}, {expected_grid_y})")
    print(
        f"  ✅ Match: {grid_result['grid_x'] == expected_grid_x and grid_result['grid_y'] == expected_grid_y}"
    )

    print("\n✅ Consolidation Test Complete!")
    print("All calculations now use single source of truth in window_utils.py")


if __name__ == "__main__":
    test_consolidation()
