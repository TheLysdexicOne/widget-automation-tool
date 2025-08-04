"""
Button Engine
Handles individual button automation and state validation.
"""

import logging
import sys
import pyautogui


class ButtonEngine:
    """Represents a single button with all its automation capabilities."""

    pyautogui.PAUSE = 0

    def __init__(self, button_data: list, name: str = "button", custom_colors: dict = {}):
        if len(button_data) != 3:
            logging.getLogger(f"{__name__}.ButtonEngine").error(f"Invalid button data for {name}: {button_data}")
            sys.exit("Exiting due to invalid button data")

        self.x, self.y, self.color = button_data
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)

        # Define button state colors
        self.button_colors = {
            "red": {"default": (199, 35, 21), "focus": (251, 36, 18), "inactive": (57, 23, 20)},
            "blue": {"default": (21, 87, 199), "focus": (18, 104, 251), "inactive": (20, 34, 57)},
            "green": {"default": (17, 162, 40), "focus": (15, 204, 45), "inactive": (16, 46, 22)},
            "yellow": {"default": (242, 151, 0), "focus": (198, 125, 0), "inactive": (60, 39, 8)},
        }

        # Allow custom colors to override or add to button_colors
        if custom_colors:
            for color, states in custom_colors.items():
                if color in self.button_colors:
                    self.button_colors[color].update(states)
                else:
                    self.button_colors[color] = states

        if self.color not in self.button_colors:
            self.logger.error(f"Invalid button color '{self.color}'")
            sys.exit("Exiting due to invalid button color")

        self.tolerance = 5

    def active(self) -> bool:
        """Check if button is in active state (default or focus)."""
        actual_color = pyautogui.pixel(self.x, self.y)

        # Check if button matches default or focus state
        for state in ["default", "focus"]:
            expected_color = self.button_colors[self.color][state]
            color_match = all(abs(actual_color[i] - expected_color[i]) <= self.tolerance for i in range(3))
            if color_match:
                return True
        return False

    def inactive(self) -> bool:
        """Check if button is in inactive state."""
        actual_color = pyautogui.pixel(self.x, self.y)
        expected_color = self.button_colors[self.color]["inactive"]

        color_match = all(abs(actual_color[i] - expected_color[i]) <= self.tolerance for i in range(3))
        return color_match

    def click(self, retries: int = 3, ignore: bool = False) -> bool:
        """Click this button with safety validation and retries.
        Set ignore=True to skip validation and always click.
        """
        for attempt in range(retries):
            if ignore or self.active():
                try:
                    pyautogui.click(self.x, self.y)
                    self.logger.debug(f"Clicked {self.color} {self.name} at ({self.x}, {self.y})")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to click {self.color} {self.name} at ({self.x}, {self.y}): {e}")
                    return False

            if attempt < retries - 1:
                self.logger.debug(f"Button {self.name} not in valid state, attempt {attempt + 1}, retrying...")
                import time

                time.sleep(0.1)
            else:
                self.logger.error(f"Button {self.name} not in valid state for clicking after {retries} attempts")
                sys.exit("Safety stop - button not valid")

        return False

    def hold_click(self, duration: float = 0.5) -> bool:
        """Hold click this button for specified duration with safety validation."""
        if not self.active():
            self.logger.error(f"Button {self.name} not in valid state for hold clicking")
            sys.exit("Safety stop - button not valid")

        try:
            pyautogui.mouseDown(self.x, self.y)
            self.logger.debug(f"Started holding {self.color} {self.name} at ({self.x}, {self.y}) for {duration}s")

            import time

            time.sleep(duration)

            pyautogui.mouseUp()
            self.logger.debug(f"Released hold on {self.color} {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to hold click {self.color} {self.name} at ({self.x}, {self.y}): {e}")
            # Ensure mouse is released on error
            try:
                pyautogui.mouseUp()
            except Exception:
                pass
            return False
