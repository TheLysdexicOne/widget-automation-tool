"""
Automation Engine
Common automation utilities and patterns for frame automators.
"""

import logging
import time
import sys
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

    def click_button(self, button_data: list, button_name: str = "button") -> bool:
        """Click a button with built-in frame validation for safety."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data for {button_name}: {button_data}")
            sys.exit("Exiting due to invalid button data")

        # SAFETY: Always validate we're on the right frame before clicking
        if not self.failsafe_color_validation(button_data, button_name):
            self.logger.error(
                f"Frame validation failed - {button_name} button not valid. Stopping automation for safety."
            )
            sys.exit("Exiting due to wrong frame - safety stop")

        screen_x, screen_y, color = button_data

        try:
            pyautogui.click(screen_x, screen_y)
            self.logger.debug(f"Clicked {color} {button_name} at ({screen_x}, {screen_y})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to click {color} {button_name} at ({screen_x}, {screen_y}): {e}")
            return False

    def failsafe_color_validation(
        self,
        button_data: list,
        button_name: str = "button",
        trigger_failsafe_callback=None,
        expected_color: str | None = None,
    ) -> bool:
        """
        Validate button color with optional failsafe triggering.

        Args:
            button_data: [screen_x, screen_y, color] format
            button_name: Name for logging/error messages
            trigger_failsafe_callback: Optional callback to trigger failsafe stop
            expected_color: Optional override for expected color (uses button_data[2] if None)

        Returns:
            True if button color is valid, False if not
        """
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data for {button_name}: {button_data}")
            sys.exit("Exiting due to invalid button data")

        screen_x, screen_y, button_color = button_data
        check_color = expected_color or button_color

        # Define button state colors
        button_colors = {
            "red": {"default": (199, 35, 21), "focus": (251, 36, 18), "inactive": (57, 23, 20)},
            "blue": {"default": (21, 87, 199), "focus": (18, 104, 251), "inactive": (20, 34, 57)},
            "green": {"default": (17, 162, 40), "focus": (15, 204, 45), "inactive": (16, 46, 22)},
            "yellow": {"default": (242, 151, 0), "focus": (198, 125, 0), "inactive": (60, 39, 8)},
        }

        if check_color not in button_colors:
            self.logger.error(f"Invalid button color '{check_color}'")
            sys.exit("Exiting due to invalid button color")

        actual_color = pyautogui.pixel(screen_x, screen_y)
        tolerance = 5

        # Check if button matches any of the three states
        for state, expected_rgb in button_colors[check_color].items():
            color_match = all(abs(actual_color[i] - expected_rgb[i]) <= tolerance for i in range(3))
            if color_match:
                return True

        # Color validation failed
        if trigger_failsafe_callback:
            failsafe_reason = f"{button_name} at screen ({screen_x}, {screen_y}) is not a valid {check_color} button"
            trigger_failsafe_callback(failsafe_reason)
        else:
            self.logger.warning(
                f"Button at ({screen_x}, {screen_y}) is not a valid {check_color} button. Got: {actual_color}"
            )

        return False

    def button_inactive(self, button_data: list) -> bool:
        """Check if a button is in inactive state."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data: {button_data}")
            sys.exit("Exiting due to invalid button data")

        screen_x, screen_y, button_color = button_data

        # Define button inactive colors
        inactive_colors = {
            "red": (57, 23, 20),
            "blue": (20, 34, 57),
            "green": (16, 46, 22),
            "yellow": (60, 39, 8),
        }

        if button_color not in inactive_colors:
            self.logger.error(f"Invalid button color '{button_color}'")
            sys.exit("Exiting due to invalid button color")

        actual_color = pyautogui.pixel(screen_x, screen_y)
        expected_color = inactive_colors[button_color]
        tolerance = 5

        # Check if button matches inactive state
        color_match = all(abs(actual_color[i] - expected_color[i]) <= tolerance for i in range(3))
        return color_match

    def button_active(self, button_data: list) -> bool:
        """Check if a button is in active state (default or focus)."""
        if len(button_data) != 3:
            self.logger.error(f"Invalid button data: {button_data}")
            sys.exit("Exiting due to invalid button data")

        screen_x, screen_y, button_color = button_data

        # Define button state colors
        button_colors = {
            "red": {"default": (199, 35, 21), "focus": (251, 36, 18)},
            "blue": {"default": (21, 87, 199), "focus": (18, 104, 251)},
            "green": {"default": (17, 162, 40), "focus": (15, 204, 45)},
            "yellow": {"default": (242, 151, 0), "focus": (198, 125, 0)},
        }

        if button_color not in button_colors:
            self.logger.error(f"Invalid button color '{button_color}'")
            sys.exit("Exiting due to invalid button color")

        actual_color = pyautogui.pixel(screen_x, screen_y)
        tolerance = 5

        # Check if button matches default or focus state
        for state, expected_color in button_colors[button_color].items():
            color_match = all(abs(actual_color[i] - expected_color[i]) <= tolerance for i in range(3))
            if color_match:
                return True

        return False
