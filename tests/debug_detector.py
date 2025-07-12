#!/usr/bin/env python3
"""
Debug test for MinigameDetector
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from minigame_detector import MinigameDetector
from widget_inc_manager import WidgetIncManager


def test_detector():
    print("Testing MinigameDetector...")

    # Test widget manager
    widget_manager = WidgetIncManager()
    print(f"Widget manager created: {widget_manager}")

    # Test detector
    detector = MinigameDetector(widget_manager)
    print(f"Detector created: {detector}")

    # Test find window
    found = widget_manager.find_widget_inc_window()
    print(f"Found window: {found}")
    print(f"Window object: {widget_manager.window}")

    # Test detection
    try:
        result = detector.detect_current_minigame()
        print(f"Detection result: {result}")
    except Exception as e:
        print(f"Detection error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_detector()
