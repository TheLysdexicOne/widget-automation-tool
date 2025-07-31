"""
Coordinate conversion utilities for button management.
Handles grid-to-screen conversion and caching for automation efficiency.
"""

import logging
import sys
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("CoordinateUtils")


class ButtonManager:
    """Simple button manager that loads from cache."""

    def __init__(self, frame_data: Dict[str, Any]):
        self.frame_id = frame_data.get("id", "unknown")
        self.buttons = frame_data.get("buttons", {})
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_button(self, button_name: str) -> list:
        """Get button as [screen_x, screen_y, color]."""
        button = self.buttons.get(button_name)
        if not button:
            self.logger.error(f"Missing button data for {button_name} in frame {self.frame_id}")
            sys.exit("Exiting due to missing button data")
        return button

    def has_button(self, button_name: str) -> bool:
        """Check if button exists."""
        exists = button_name in self.buttons
        if not exists:
            self.logger.warning(f"Button {button_name} not found in frame {self.frame_id}")
        return exists

    def get_button_screen_coords(self, button_name: str) -> Optional[Tuple[int, int]]:
        """Get screen coordinates for a button."""
        button = self.get_button(button_name)
        return (button[0], button[1]) if button else None

    def get_button_color(self, button_name: str) -> Optional[str]:
        """Get button color."""
        button = self.get_button(button_name)
        return button[2] if button else None

    def get_all_buttons(self) -> Dict[str, list]:
        """Get all converted button data."""
        return self.buttons.copy()

    def get_button_names(self) -> list:
        """Get list of all button names."""
        return list(self.buttons.keys())
