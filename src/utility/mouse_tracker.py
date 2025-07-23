"""
Mouse Tracker Utility - Real-time Mouse Position Tracking

Tracks mouse position and provides detailed information about:
- Exact screen coordinates
- Window percentages
- Playable area percentages
- Pixel art grid location

Based on the mouse tracker from .old.complicated but simplified for current architecture.
"""

import logging
import time
from typing import Dict, Tuple, Optional, Callable
import pyautogui

try:
    import win32api
    import win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .window_utils import (
    calculate_playable_area_percentages,
    calculate_pixel_art_grid_position,
    PIXEL_ART_GRID_WIDTH,
    PIXEL_ART_GRID_HEIGHT,
)


class MouseTracker(QObject):
    """Tracks mouse position and provides detailed location information."""

    # Signals
    position_changed = pyqtSignal(dict)  # Emits detailed position information
    click_detected = pyqtSignal(tuple, str, dict)  # (x, y), button, position_info

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Mouse state
        self.current_position = None
        self.click_count = 0
        self.last_click_time = 0
        self.last_action = "None"

        # Mouse button state tracking
        self.left_button_was_down = False
        self.right_button_was_down = False
        self.middle_button_was_down = False

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)

        # Callbacks for getting current window/playable area info
        self.get_window_coords_callback: Optional[Callable] = None
        self.get_playable_coords_callback: Optional[Callable] = None

    def set_coordinate_callbacks(
        self, window_callback: Callable, playable_callback: Callable
    ):
        """Set callbacks to get current window and playable area coordinates."""
        self.get_window_coords_callback = window_callback
        self.get_playable_coords_callback = playable_callback

    def start_tracking(self, update_interval: int = 50):
        """Start mouse tracking."""
        self.logger.info(f"Starting mouse tracking (update every {update_interval}ms)")
        self.update_timer.start(update_interval)

    def stop_tracking(self):
        """Stop mouse tracking."""
        self.logger.info("Stopping mouse tracking")
        self.update_timer.stop()

    def _update_position(self):
        """Update mouse position and emit detailed information if changed."""
        try:
            new_position = pyautogui.position()

            if self.current_position != new_position:
                self.current_position = new_position

                # Calculate detailed position information
                position_info = self._calculate_position_info(
                    new_position.x, new_position.y
                )

                # Emit position change with detailed info
                self.position_changed.emit(position_info)

            # Check for click events
            self._check_for_clicks(new_position)

        except Exception as e:
            self.logger.error(f"Error updating mouse position: {e}")

    def _calculate_position_info(self, x: int, y: int) -> Dict:
        """Calculate comprehensive position information for given coordinates."""
        try:
            info = {
                "screen_x": x,
                "screen_y": y,
                "timestamp": time.time(),
            }

            # Get window coordinates if callback available
            window_coords = {}
            if self.get_window_coords_callback:
                window_coords = self.get_window_coords_callback()

            # Get playable area coordinates if callback available
            playable_coords = {}
            if self.get_playable_coords_callback:
                playable_coords = self.get_playable_coords_callback()

            # Calculate window percentages if window coords available
            if (
                window_coords
                and window_coords.get("client_width")
                and window_coords.get("client_height")
            ):
                client_x = window_coords.get("client_x", 0)
                client_y = window_coords.get("client_y", 0)
                client_width = window_coords["client_width"]
                client_height = window_coords["client_height"]

                if (
                    client_x <= x <= client_x + client_width
                    and client_y <= y <= client_y + client_height
                ):
                    window_x_percent = ((x - client_x) / client_width) * 100
                    window_y_percent = ((y - client_y) / client_height) * 100

                    info.update(
                        {
                            "inside_window": True,
                            "window_x_percent": window_x_percent,
                            "window_y_percent": window_y_percent,
                            "window_coords": window_coords,
                        }
                    )
                else:
                    info.update(
                        {
                            "inside_window": False,
                            "window_x_percent": 0.0,
                            "window_y_percent": 0.0,
                        }
                    )

            # Calculate playable area percentages and grid position
            if playable_coords:
                # Basic playable area percentages
                playable_info = calculate_playable_area_percentages(
                    x, y, playable_coords
                )
                info.update(playable_info)

                # Pixel art grid position
                grid_info = calculate_pixel_art_grid_position(x, y, playable_coords)
                info.update(
                    {
                        "grid_position": {
                            "x": grid_info.get("grid_x", 0),
                            "y": grid_info.get("grid_y", 0),
                        },
                        "pixel_size": grid_info.get("pixel_size", 0.0),
                        "grid_dimensions": grid_info.get(
                            "grid_dimensions",
                            {
                                "width": PIXEL_ART_GRID_WIDTH,
                                "height": PIXEL_ART_GRID_HEIGHT,
                            },
                        ),
                    }
                )

            return info

        except Exception as e:
            self.logger.error(f"Error calculating position info: {e}")
            return {
                "screen_x": x,
                "screen_y": y,
                "timestamp": time.time(),
                "inside_playable": False,
                "inside_window": False,
            }

    def _check_for_clicks(self, position):
        """Check for mouse click events."""
        if not WIN32_AVAILABLE:
            return

        try:
            # Check button states
            left_down = win32api.GetKeyState(win32con.VK_LBUTTON) < 0
            right_down = win32api.GetKeyState(win32con.VK_RBUTTON) < 0
            middle_down = win32api.GetKeyState(win32con.VK_MBUTTON) < 0

            # Detect left click
            if left_down and not self.left_button_was_down:
                self._handle_click(position.x, position.y, "left")

            # Detect right click
            if right_down and not self.right_button_was_down:
                self._handle_click(position.x, position.y, "right")

            # Detect middle click
            if middle_down and not self.middle_button_was_down:
                self._handle_click(position.x, position.y, "middle")

            # Update button states
            self.left_button_was_down = left_down
            self.right_button_was_down = right_down
            self.middle_button_was_down = middle_down

        except Exception as e:
            self.logger.error(f"Error checking for clicks: {e}")

    def _handle_click(self, x: int, y: int, button: str):
        """Handle a detected click event."""
        self.click_count += 1
        self.last_click_time = time.time()
        self.last_action = f"Click {button} at ({x}, {y})"

        # Calculate detailed position information for the click
        position_info = self._calculate_position_info(x, y)

        # Log clicks in playable area (reduce noise)
        if position_info.get("inside_playable", False):
            grid_pos = position_info.get("grid_position", {})
            self.logger.info(
                f"Click {self.click_count}: {button} at grid ({grid_pos.get('x', 0)}, {grid_pos.get('y', 0)}) "
                f"[{position_info.get('x_percent', 0):.1f}%, {position_info.get('y_percent', 0):.1f}%]"
            )

        # Emit click signal with position info
        self.click_detected.emit((x, y), button, position_info)

    def get_current_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        try:
            pos = pyautogui.position()
            return (pos.x, pos.y)
        except Exception:
            return (0, 0)

    def get_current_position_info(self) -> Dict:
        """Get detailed information about current mouse position."""
        pos = self.get_current_position()
        return self._calculate_position_info(pos[0], pos[1])

    def get_click_count(self) -> int:
        """Get total click count."""
        return self.click_count

    def get_last_action(self) -> str:
        """Get last recorded action."""
        return self.last_action

    def get_stats(self) -> Dict:
        """Get comprehensive mouse tracking statistics."""
        current_info = self.get_current_position_info()

        stats = {
            "current_position": f"({current_info['screen_x']}, {current_info['screen_y']})",
            "click_count": self.click_count,
            "last_action": self.last_action,
            "last_click_time": self.last_click_time,
            "inside_playable": current_info.get("inside_playable", False),
            "inside_window": current_info.get("inside_window", False),
        }

        # Add playable area info if available
        if current_info.get("inside_playable", False):
            grid_pos = current_info.get("grid_position", {})
            stats.update(
                {
                    "playable_percent": f"{current_info.get('x_percent', 0):.1f}%, {current_info.get('y_percent', 0):.1f}%",
                    "grid_position": f"({grid_pos.get('x', 0)}, {grid_pos.get('y', 0)})",
                    "pixel_size": f"{current_info.get('pixel_size', 0):.2f}px",
                }
            )

        # Add window info if available
        if current_info.get("inside_window", False):
            stats["window_percent"] = (
                f"{current_info.get('window_x_percent', 0):.1f}%, {current_info.get('window_y_percent', 0):.1f}%"
            )

        return stats
