#!/usr/bin/env python3
"""
Test script to verify playable area detection functionality.
This will help validate that the 3:2 ratio detection and pixel sampling work correctly.
"""

import sys

sys.path.append("src")

from console.tabs.monitoring_tab import MonitoringTab
from console.tabs.base_tab import BaseTab


class TestMonitoringTab(MonitoringTab):
    """Test version of MonitoringTab that doesn't require PyQt6 GUI."""

    def __init__(self):
        # Initialize without calling parent __init__ to avoid PyQt6 requirements
        pass

    def test_playable_area_detection(self):
        """Test the playable area detection logic."""
        print("Testing Playable Area Detection...")
        print("=" * 50)

        # Test WidgetInc coordinates
        widget_coords = self._get_widgetinc_coordinates()
        print(f"WidgetInc Window: {widget_coords}")

        if widget_coords["width"] > 0:
            # Test playable area calculation
            playable_coords = self._get_playable_area_coordinates()
            print(f"Playable Area: {playable_coords}")

            # Debug: Check the ratio calculation manually
            window_ratio = widget_coords["width"] / widget_coords["height"]
            target_ratio = 3.0 / 2.0
            print(f"Window Ratio: {window_ratio:.3f}, Target Ratio: {target_ratio:.3f}")
            print(
                f"Window is {'wider' if window_ratio > target_ratio else 'taller' if window_ratio < target_ratio else 'exactly'} than target ratio"
            )

            # Manual calculation for verification
            if window_ratio > target_ratio:
                calc_playable_height = widget_coords["height"]
                calc_playable_width = int(calc_playable_height * target_ratio)
                calc_black_bar_width = (
                    widget_coords["width"] - calc_playable_width
                ) // 2
                print(f"Manual Calculation:")
                print(f"  Playable Height: {calc_playable_height}")
                print(f"  Playable Width: {calc_playable_width}")
                print(f"  Black Bar Width: {calc_black_bar_width}")
                print(f"  Should be at X: {widget_coords['x'] + calc_black_bar_width}")

            # Test playable area info
            playable_info = self._get_playable_area_info()
            if playable_info:
                print(f"Playable Area Details:")
                print(
                    f"  Background Pixel Size: {playable_info['bg_pixel_width']:.2f}x{playable_info['bg_pixel_height']:.2f}px"
                )
                print(
                    f"  Sprite Pixel Size: {playable_info['sprite_pixel_width']:.2f}x{playable_info['sprite_pixel_height']:.2f}px"
                )
                print(
                    f"  Black Borders: L:{playable_info['left_border']} R:{playable_info['right_border']} T:{playable_info['top_border']} B:{playable_info['bottom_border']}"
                )
                print(
                    f"  Aspect Ratio: {playable_info['aspect_ratio']:.3f} (Target: 1.500)"
                )

            # Test mouse tracking
            print(f"\nMouse Position Tests:")
            print(f"  Exact Coordinates: {self._get_current_mouse_position()}")
            print(f"  % Inside WidgetInc: {self._get_mouse_percentage_widget()}")
            print(f"  % Inside Playable: {self._get_mouse_percentage_playable()}")

        else:
            print("WidgetInc.exe not found or not running")


if __name__ == "__main__":
    test_tab = TestMonitoringTab()
    test_tab.test_playable_area_detection()
