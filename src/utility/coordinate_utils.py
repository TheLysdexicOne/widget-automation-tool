"""
Coordinate conversion utilities for button management.
Handles grid-to-screen conversion and caching for automation efficiency.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional, Tuple

from .window_utils import get_playable_area, grid_to_screen_coordinates

logger = logging.getLogger(__name__)


def convert_buttons_to_screen_coords(buttons: Dict[str, list]) -> Dict[str, Dict[str, Any]]:
    """
    Convert button grid coordinates to screen coordinates.

    Args:
        buttons: Dict of button_name -> [grid_x, grid_y, color]

    Returns:
        Dict of button_name -> {
            "grid": (grid_x, grid_y),
            "screen": (screen_x, screen_y),
            "color": "color_name"
        }
    """
    converted = {}
    playable_area = get_playable_area()

    if not playable_area:
        logger.error("Could not get playable area for coordinate conversion")
        return {}

    for button_name, button_data in buttons.items():
        if len(button_data) != 3:
            logger.error(f"Invalid button data for {button_name}: {button_data}")
            continue

        grid_x, grid_y, color = button_data
        screen_coords = grid_to_screen_coordinates(grid_x, grid_y, playable_area)

        if screen_coords and screen_coords != (0, 0):
            converted[button_name] = {"grid": (grid_x, grid_y), "screen": screen_coords, "color": color}
            logger.debug(f"Button {button_name}: Grid ({grid_x}, {grid_y}) -> Screen {screen_coords}")
        else:
            logger.error(f"Failed to convert coordinates for button {button_name}")

    return converted


def generate_frames_temp_file(frames_data: list, output_path: str = "data/frames_temp.json"):
    """
    Generate frames_temp.json with all screen coordinates calculated.

    Args:
        frames_data: List of frame dictionaries from frames.json
        output_path: Path to save the temporary file
    """
    try:
        frames_with_coords = []
        playable_area = get_playable_area()

        for frame in frames_data:
            frame_copy = frame.copy()

            if "buttons" in frame:
                converted_buttons = convert_buttons_to_screen_coords(frame["buttons"])
                frame_copy["buttons_converted"] = converted_buttons

            frames_with_coords.append(frame_copy)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write temporary file
        temp_data = {"frames": frames_with_coords, "generated_at": time.time(), "playable_area": playable_area}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(temp_data, f, indent=2)

        logger.info(f"Generated frames_temp.json with screen coordinates at {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error generating frames_temp.json: {e}")
        return False


class ButtonManager:
    """Manages button coordinates for automation frames."""

    def __init__(self, frame_data: Dict[str, Any]):
        self.frame_data = frame_data
        self.frame_id = frame_data.get("id", "unknown")
        self.buttons = {}
        self._convert_buttons()

    def _convert_buttons(self):
        """Convert all button coordinates for this frame."""
        if "buttons" not in self.frame_data:
            logger.warning(f"No buttons defined for frame {self.frame_id}")
            return

        self.buttons = convert_buttons_to_screen_coords(self.frame_data["buttons"])

        if not self.buttons:
            logger.error(f"Failed to convert any buttons for frame {self.frame_id}")
        else:
            logger.info(f"Converted {len(self.buttons)} buttons for frame {self.frame_id}")

    def get_button(self, button_name: str) -> Optional[Dict[str, Any]]:
        """Get button data by name."""
        return self.buttons.get(button_name)

    def get_button_screen_coords(self, button_name: str) -> Optional[Tuple[int, int]]:
        """Get screen coordinates for a button."""
        button = self.get_button(button_name)
        return button["screen"] if button else None

    def get_button_grid_coords(self, button_name: str) -> Optional[Tuple[int, int]]:
        """Get grid coordinates for a button."""
        button = self.get_button(button_name)
        return button["grid"] if button else None

    def get_button_color(self, button_name: str) -> Optional[str]:
        """Get button color."""
        button = self.get_button(button_name)
        return button["color"] if button else None

    def get_all_buttons(self) -> Dict[str, Dict[str, Any]]:
        """Get all converted button data."""
        return self.buttons.copy()

    def has_button(self, button_name: str) -> bool:
        """Check if button exists and has valid coordinates."""
        return button_name in self.buttons

    def get_button_names(self) -> list:
        """Get list of all button names."""
        return list(self.buttons.keys())
