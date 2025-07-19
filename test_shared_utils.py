#!/usr/bin/env python3
"""
Test Script - Verify Shared Target Window Utilities

Quick test to verify that both main overlay and tracker are using
the same shared logic and getting consistent results.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utility.window_utils import find_target_window


def main():
    """Test the shared target window utilities."""
    print("Testing shared target window utilities...")
    print("=" * 50)

    # Test finding the target window
    target_info = find_target_window("WidgetInc.exe")

    if target_info:
        print("✅ TARGET FOUND!")
        print(f"PID: {target_info['pid']}")

        window_info = target_info["window_info"]
        print(f"HWND: {window_info['hwnd']}")
        print(f"Title: {window_info['title']}")
        print(f"Window: {window_info['window_rect']}")
        print(
            f"Client: {window_info['client_width']}x{window_info['client_height']} at ({window_info['client_x']}, {window_info['client_y']})"
        )

        playable = target_info["playable_area"]
        if playable:
            print(
                f"Playable Area: {playable['width']}x{playable['height']} at ({playable['x']}, {playable['y']})"
            )
        else:
            print("Playable Area: Failed to calculate")
    else:
        print("❌ TARGET NOT FOUND")

    print("=" * 50)


if __name__ == "__main__":
    main()
