"""
Automation Engine
Common automation utilities and patterns for frame automators.
"""

import logging
import time

import pyautogui


class AutomationEngine:
    """Provides common automation utilities for frame automators."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AutomationEngine")

        # Configure pyautogui for safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small delay between actions

    def click_at(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        """Click at specified coordinates."""
        try:
            pyautogui.click(x, y, button=button, duration=duration)
            self.logger.debug(f"Clicked at ({x}, {y}) with {button} button")
            return True
        except Exception as e:
            self.logger.error(f"Failed to click at ({x}, {y}): {e}")
            return False

    def safe_sleep(self, duration: float, check_stop_callback=None) -> bool:
        """
        Sleep for given duration while optionally checking for stop signal.
        Returns True if sleep completed normally, False if interrupted.
        """
        end_time = time.time() + duration
        while time.time() < end_time:
            if check_stop_callback and check_stop_callback():
                return False
            time.sleep(0.1)  # Check every 100ms
        return True

    def click_button(self, button_data: list, button_name: str = "button") -> bool:
        """Click a button using simplified button data format."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data for {button_name}: {button_data}")
            return False

        screen_x, screen_y, color = button_data

        try:
            pyautogui.click(screen_x, screen_y)
            self.logger.info(f"Clicked {color} {button_name} at ({screen_x}, {screen_y})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to click {color} {button_name} at ({screen_x}, {screen_y}): {e}")
            return False

    def is_button_color_valid(self, button_data: list) -> bool:
        """Check if a button is any valid state of the expected color."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data: {button_data}")
            return False

        screen_x, screen_y, button_color = button_data

        # Define button state colors
        button_colors = {
            "red": {"default": (199, 35, 21), "focus": (251, 36, 18), "inactive": (57, 23, 20)},
            "blue": {"default": (21, 87, 199), "focus": (18, 104, 251), "inactive": (20, 34, 57)},
            "green": {"default": (17, 162, 40), "focus": (15, 204, 45), "inactive": (16, 46, 22)},
            "yellow": {"default": (242, 151, 0), "focus": (198, 125, 0), "inactive": (60, 39, 8)},
        }

        if button_color not in button_colors:
            self.logger.error(f"Invalid button color '{button_color}'")
            return False

        actual_color = pyautogui.pixel(screen_x, screen_y)

        # Check if button matches any of the three states
        tolerance = 5
        for state, expected_color in button_colors[button_color].items():
            color_match = all(abs(actual_color[i] - expected_color[i]) <= tolerance for i in range(3))
            if color_match:
                return True

        self.logger.warning(
            f"Button at ({screen_x}, {screen_y}) is not a valid {button_color} button. Got: {actual_color}"
        )
        return False

    def is_button_inactive(self, button_data: list) -> bool:
        """Check if a button is in inactive state."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data: {button_data}")
            return False

        screen_x, screen_y, button_color = button_data

        # Define button inactive colors
        inactive_colors = {"red": (57, 23, 20), "blue": (20, 34, 57), "green": (16, 46, 22), "yellow": (60, 39, 8)}

        if button_color not in inactive_colors:
            self.logger.error(f"Invalid button color '{button_color}'")
            return False

        actual_color = pyautogui.pixel(screen_x, screen_y)
        expected_color = inactive_colors[button_color]
        tolerance = 5

        return all(abs(actual_color[i] - expected_color[i]) <= tolerance for i in range(3))
