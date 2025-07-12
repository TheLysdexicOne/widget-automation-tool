#!/usr/bin/env python3
"""
Debug script to show checkbox positions for the enhanced overlay
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def debug_checkbox_positions():
    """Debug the checkbox positioning"""
    print("=== Enhanced Overlay Checkbox Position Debug ===")
    print()

    # Simulate the y_offset calculation from draw_expanded()
    print("Checkbox positions in draw_expanded():")
    y_offset = 70
    print(f"Hide Activate Button checkbox: y = {y_offset}")
    y_offset += 25

    print(f"Debug Mode checkbox: y = {y_offset}")
    y_offset += 25

    print("\nDebug mode checkboxes (when enabled):")
    debug_checkboxes = [
        "Enable logging",
        "Enable on-screen debug",
        "Enable disabled buttons",
        "Enable cursor trail",
        "Enable click visuals",
        "Enable cursor tracking",
    ]

    for checkbox in debug_checkboxes:
        print(f"  {checkbox}: y = {y_offset}")
        y_offset += 20

    print(f"\nCursor tracking info starts at: y = {y_offset}")
    print()

    # Simulate the click detection from handle_checkbox_click()
    print("Click detection zones in handle_checkbox_click():")
    checkbox_size = 12
    y_offset = 70

    print(
        f"Hide Activate Button: x=[10, {10+checkbox_size}], y=[{y_offset}, {y_offset+checkbox_size}]"
    )
    y_offset += 25

    print(
        f"Debug Mode: x=[10, {10+checkbox_size}], y=[{y_offset}, {y_offset+checkbox_size}]"
    )
    y_offset += 25

    print("\nDebug mode checkboxes click zones:")
    for checkbox in debug_checkboxes:
        print(
            f"  {checkbox}: x=[20, {20+checkbox_size}], y=[{y_offset}, {y_offset+checkbox_size}]"
        )
        y_offset += 20

    print()
    print("Key fixes applied:")
    print("✓ Changed initial y_offset from 55 to 70")
    print("✓ Changed main checkbox increment from 20 to 25")
    print("✓ Fixed debug checkbox increment to match drawing (20px)")
    print("✓ Debug checkboxes now use correct x position (20px)")
    print()
    print("The checkboxes should now be clickable directly on the checkbox box!")


if __name__ == "__main__":
    debug_checkbox_positions()
