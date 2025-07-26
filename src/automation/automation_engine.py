"""
Automation Engine
Common automation utilities and patterns for frame automators.
"""

import logging
import time
from typing import Optional, Tuple

import pyautogui

from utility.window_utils import grid_to_screen_coordinates


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

    def find_image_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """Find image on screen and return center coordinates."""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                self.logger.debug(f"Found image {image_path} at {center}")
                return (center.x, center.y)
            else:
                self.logger.debug(f"Image {image_path} not found on screen")
                return None
        except Exception as e:
            self.logger.error(f"Error finding image {image_path}: {e}")
            return None

    def wait_for_image(
        self, image_path: str, timeout: float = 10.0, confidence: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        """Wait for image to appear on screen within timeout."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.find_image_on_screen(image_path, confidence)
            if location:
                return location
            time.sleep(0.5)  # Check every 500ms

        self.logger.debug(f"Timeout waiting for image {image_path}")
        return None

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

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        try:
            size = pyautogui.size()
            return (size.width, size.height)
        except Exception as e:
            self.logger.error(f"Error getting screen size: {e}")
            return (1920, 1080)

    def take_screenshot(self, filename: Optional[str] = None) -> bool:
        """Take a screenshot and optionally save to file."""
        try:
            screenshot = pyautogui.screenshot()
            if filename:
                screenshot.save(filename)
                self.logger.debug(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return False

    def get_grid_click_position(self, grid_x: int, grid_y: int) -> Optional[Tuple[int, int]]:
        """
        Get screen coordinates for clicking at grid position.

        Args:
            grid_x: Grid X coordinate (0-191 for 192-wide grid)
            grid_y: Grid Y coordinate (0-127 for 128-tall grid)

        Returns:
            Tuple of (screen_x, screen_y) or None if playable area not found
        """
        try:
            # Use the optimized grid_to_screen_coordinates that auto-detects playable area
            screen_coords = grid_to_screen_coordinates(grid_x, grid_y)

            if screen_coords == (0, 0):
                self.logger.error(f"Invalid screen coordinates for grid ({grid_x}, {grid_y})")
                return None

            self.logger.debug(f"Grid ({grid_x}, {grid_y}) -> Screen {screen_coords}")
            return screen_coords

        except Exception as e:
            self.logger.error(f"Error getting grid click position ({grid_x}, {grid_y}): {e}")
            return None

    def click_grid(self, grid_x: int, grid_y: int, button: str = "left", duration: float = 0.1) -> bool:
        """
        Click at grid coordinates.

        Args:
            grid_x: Grid X coordinate (0-191 for 192-wide grid)
            grid_y: Grid Y coordinate (0-127 for 128-tall grid)
            button: Mouse button to click ('left', 'right', 'middle')
            duration: Duration of click in seconds

        Returns:
            True if click succeeded, False otherwise
        """
        screen_coords = self.get_grid_click_position(grid_x, grid_y)
        if not screen_coords:
            self.logger.error(f"Could not get screen coordinates for grid ({grid_x}, {grid_y})")
            return False

        self.logger.info(f"Clicking grid ({grid_x}, {grid_y}) -> screen coordinates {screen_coords}")
        return self.click_at(screen_coords[0], screen_coords[1], button, duration)

    def get_pixel_color(self, grid_x: int, grid_y: int) -> Optional[Tuple[int, int, int]]:
        """
        Get the RGB color of a pixel at grid coordinates.

        Args:
            grid_x: Grid X coordinate (0-191)
            grid_y: Grid Y coordinate (0-127)

        Returns:
            RGB tuple (r, g, b) or None if failed
        """
        screen_coords = self.get_grid_click_position(grid_x, grid_y)
        if not screen_coords:
            return None

        try:
            # Get pixel color at screen coordinates
            pixel_color = pyautogui.pixel(screen_coords[0], screen_coords[1])
            self.logger.debug(f"Pixel color at grid ({grid_x}, {grid_y}): {pixel_color}")
            return pixel_color
        except Exception as e:
            self.logger.error(f"Error getting pixel color at grid ({grid_x}, {grid_y}): {e}")
            return None

    def is_button_state(self, grid_x: int, grid_y: int, button_color: str, state: str) -> bool:
        """
        Check if a button at grid coordinates matches the expected state.

        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            button_color: Button color ('red', 'blue', 'green', 'yellow')
            state: Button state ('default', 'focus', 'inactive')

        Returns:
            True if button matches state, False otherwise
        """
        # Define button state colors from automation.md
        button_colors = {
            "red": {
                "default": (199, 35, 21),  # #c72315
                "focus": (251, 36, 18),  # #fb2412
                "inactive": (57, 23, 20),  # #391714
            },
            "blue": {
                "default": (21, 87, 199),  # #1557c7
                "focus": (18, 104, 251),  # #1268fb
                "inactive": (20, 34, 57),  # #142239
            },
            "green": {
                "default": (17, 162, 40),  # #11a228
                "focus": (15, 204, 45),  # #0fcc2d
                "inactive": (16, 46, 22),  # #102e16
            },
            "yellow": {
                "default": (242, 151, 0),  # #f29700
                "focus": (198, 125, 0),  # #c67d00
                "inactive": (60, 39, 8),  # #3c2708
            },
        }

        if button_color not in button_colors or state not in button_colors[button_color]:
            self.logger.error(f"Invalid button color '{button_color}' or state '{state}'")
            return False

        expected_color = button_colors[button_color][state]
        actual_color = self.get_pixel_color(grid_x, grid_y)

        if not actual_color:
            return False

        # Allow for slight color variations (tolerance of 5 per RGB component)
        tolerance = 5
        color_match = all(abs(actual_color[i] - expected_color[i]) <= tolerance for i in range(3))

        self.logger.debug(
            f"Button state check at ({grid_x}, {grid_y}): expected {expected_color}, got {actual_color}, match: {color_match}"
        )

        return color_match

    def is_button_inactive(self, grid_x: int, grid_y: int, button_color: str) -> bool:
        """
        Check if a button is in inactive state (not clickable).

        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            button_color: Button color ('red', 'blue', 'green', 'yellow')

        Returns:
            True if button is inactive, False if clickable
        """
        return self.is_button_state(grid_x, grid_y, button_color, "inactive")

    def is_valid_button_color(self, grid_x: int, grid_y: int, button_color: str) -> bool:
        """
        Check if a button at grid coordinates is any valid state of the expected color.
        This is used as a failsafe to ensure we're looking at the right button type.

        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            button_color: Expected button color ('red', 'blue', 'green', 'yellow')

        Returns:
            True if button matches any state of the expected color, False otherwise
        """
        # Check if button matches any of the three states (default, focus, inactive)
        for state in ["default", "focus", "inactive"]:
            if self.is_button_state(grid_x, grid_y, button_color, state):
                self.logger.debug(f"Button at ({grid_x}, {grid_y}) is valid {button_color} ({state} state)")
                return True

        # If we get here, the button doesn't match any expected state
        actual_color = self.get_pixel_color(grid_x, grid_y)
        self.logger.warning(
            f"Button at ({grid_x}, {grid_y}) is not a valid {button_color} button. "
            f"Expected any {button_color} state, got color: {actual_color}"
        )
        return False
