"""
Simple Test Script

A dumb, simple test script that just does what it's told with coordinates.
No complex logic, no calculations, just move mouse and click.
"""

import pyautogui
import time
import sys
import logging

# Disable PyAutoGUI failsafe to prevent interruption during tests
pyautogui.FAILSAFE = False


def test_overlay_click(x, y):
    """
    Simple test: Move mouse to coordinates and click.

    Args:
        x: X coordinate to click
        y: Y coordinate to click
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Received coordinates: ({x}, {y})")
    logger.info(f"Moving mouse to ({x}, {y})")

    pyautogui.moveTo(x, y)
    time.sleep(10.2)

    # Click
    logger.info("Clicking mouse")
    pyautogui.click()

    time.sleep(1)
    logger.info("Test complete")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 3:
        print("Usage: python simple_test.py <x> <y>")
        sys.exit(1)

    try:
        x = int(sys.argv[1])
        y = int(sys.argv[2])
        test_overlay_click(x, y)
    except ValueError:
        print("Error: Coordinates must be integers")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
