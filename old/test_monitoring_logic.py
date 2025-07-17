#!/usr/bin/env python3
"""
Test script to verify the monitoring tab functionality without Qt.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_playable_area_math():
    """Test playable area calculations mathematically."""
    print("Testing playable area calculations...")

    # Test client area sizes
    test_cases = [
        (2560, 1440),  # 16:9 monitor
        (1920, 1080),  # 16:9 monitor
        (1680, 1050),  # 16:10 monitor
        (1200, 800),  # 3:2 perfect fit
        (600, 900),  # Portrait mode
    ]

    for width, height in test_cases:
        print(f"\nTesting client area: {width}x{height}")

        # Calculate 3:2 aspect ratio
        aspect_ratio = 3.0 / 2.0
        client_aspect = width / height

        if client_aspect > aspect_ratio:
            # Landscape - constrained by height
            playable_height = height
            playable_width = int(height * aspect_ratio)
            playable_x = (width - playable_width) // 2
            playable_y = 0
        else:
            # Portrait or square - constrained by width
            playable_width = width
            playable_height = int(width / aspect_ratio)
            playable_x = 0
            playable_y = (height - playable_height) // 2

        print(f"  Playable area: {playable_width}x{playable_height}")
        print(f"  Position: ({playable_x}, {playable_y})")
        print(f"  Aspect ratio: {playable_width/playable_height:.3f}")

        # Test 192x128 background coordinates
        bg_pixel_width = playable_width / 192
        bg_pixel_height = playable_height / 128

        print(f"  Background pixel size: {bg_pixel_width:.1f}x{bg_pixel_height:.1f}")

        # Check if pixels are square
        if abs(bg_pixel_width - bg_pixel_height) < 0.1:
            print("  ✓ Background pixels are square")
        else:
            print("  ✗ Background pixels are not square")


def test_border_detection():
    """Test border detection logic."""
    print("\nTesting border detection logic...")

    # Test border color
    border_color = (12, 10, 16)  # #0c0a10
    print(f"Border color: RGB{border_color}")

    # Test color matching
    test_colors = [
        (12, 10, 16),  # Exact match
        (11, 9, 15),  # Close match
        (0, 0, 0),  # Black
        (255, 255, 255),  # White
    ]

    for r, g, b in test_colors:
        # Simple color matching (would be more sophisticated in real implementation)
        is_border = (r, g, b) == border_color
        print(f"  RGB({r}, {g}, {b}): {'✓ Border' if is_border else '✗ Not border'}")


if __name__ == "__main__":
    test_playable_area_math()
    test_border_detection()
