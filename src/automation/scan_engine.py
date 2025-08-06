"""
Scan Engine
Handles color detection and scanning operations for automation.
"""

import logging
import time
import pyautogui


class ScanEngine:
    """Provides color detection and scanning capabilities for automation."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tolerance = 5  # Default color tolerance

    def pixel_watcher(
        self, coords: tuple, expected_color: tuple, timeout: float = 30.0, check_interval: float = 0.1
    ) -> bool:
        """
        Wait for a pixel to change from its expected color.

        Args:
            coords: (x, y) screen coordinates to monitor
            expected_color: RGB tuple of the color we're waiting to change from
            timeout: Maximum time to wait in seconds (default 30)
            check_interval: How often to check the pixel in seconds (default 0.1)

        Returns:
            True if pixel changed, False if timeout reached
        """
        x, y = coords
        start_time = time.time()

        self.logger.debug(f"Watching pixel at ({x}, {y}) for change from {expected_color}")

        while time.time() - start_time < timeout:
            current_color = pyautogui.pixel(x, y)

            # Check if color has changed beyond tolerance
            color_changed = any(abs(current_color[i] - expected_color[i]) > self.tolerance for i in range(3))

            if color_changed:
                self.logger.debug(f"Pixel at ({x}, {y}) changed from {expected_color} to {current_color}")
                return True

            time.sleep(check_interval)

        self.logger.warning(f"Pixel watcher timed out after {timeout}s - no change detected")
        return False

    def wait_for_color(
        self, coords: tuple, target_color: tuple, timeout: float = 30.0, check_interval: float = 0.1
    ) -> bool:
        """
        Wait for a pixel to match a specific target color.

        Args:
            coords: (x, y) screen coordinates to monitor
            target_color: RGB tuple of the color we're waiting for
            timeout: Maximum time to wait in seconds (default 30)
            check_interval: How often to check the pixel in seconds (default 0.1)

        Returns:
            True if target color found, False if timeout reached
        """
        x, y = coords
        start_time = time.time()

        self.logger.debug(f"Waiting for pixel at ({x}, {y}) to become {target_color}")

        while time.time() - start_time < timeout:
            current_color = pyautogui.pixel(x, y)

            # Check if color matches target within tolerance
            color_match = all(abs(current_color[i] - target_color[i]) <= self.tolerance for i in range(3))

            if color_match:
                self.logger.debug(f"Pixel at ({x}, {y}) reached target color {target_color}")
                return True

            time.sleep(check_interval)

        self.logger.warning(f"Color wait timed out after {timeout}s - target color {target_color} not found")
        return False
