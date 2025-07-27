"""
Coordinate conversion utilities for button management.
Handles grid-to-screen conversion and caching for automation efficiency.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .window_utils import grid_to_screen_coordinates

logger = logging.getLogger(__name__)


def generate_db_cache():
    """Generate frames.json with screen coordinates from frames_database.json."""
    frames_file = Path(__file__).parent.parent.parent / "config" / "database" / "frames_database.json"
    frames_cache = Path(__file__).parent.parent.parent / "config" / "database" / "frames.json"

    with open(frames_file, "r") as f:
        frames_data = json.load(f)

    frames_with_coords = []

    for frame in frames_data["frames"]:
        frame_copy = frame.copy()

        if "buttons" in frame:
            converted = {}
            for button_name, button_data in frame["buttons"].items():
                if len(button_data) != 3:
                    logger.error(f"Invalid button data for {button_name}: {button_data}")
                    sys.exit("Exiting due to invalid database")

                grid_x, grid_y, color = button_data
                screen_x, screen_y = grid_to_screen_coordinates(grid_x, grid_y)
                converted[button_name] = [screen_x, screen_y, color]

            frame_copy["buttons"] = converted

        frames_with_coords.append(frame_copy)

    frames_cache.parent.mkdir(exist_ok=True)
    with open(frames_cache, "w") as f:
        json.dump({"frames": frames_with_coords}, f, indent=2)

    logger.info(f"Generated coordinate cache at {frames_cache}")


class ButtonManager:
    """Simple button manager that loads from cache."""

    def __init__(self, frame_data: Dict[str, Any]):
        self.frame_id = frame_data.get("id", "unknown")
        self.buttons = frame_data.get("buttons", {})
        self.logger = logging.getLogger(f"{__name__}.ButtonManager")

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
