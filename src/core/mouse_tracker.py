"""
Mouse Tracker - Tracks mouse position and interactions.

This module handles mouse position tracking and provides data to other components.
Following separation of duties: Core (brains) manages mouse tracking.
"""

import logging
import time
from typing import Dict, Tuple, Optional
import pyautogui

try:
    import win32api
    import win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32api not available - click detection will be limited")

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class MouseTracker(QObject):
    """Tracks mouse position and interactions."""

    # Signals
    position_changed = pyqtSignal(tuple)  # (x, y)
    click_detected = pyqtSignal(tuple, str, dict)  # (x, y), button, playable_area_info

    def __init__(self, window_manager=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.window_manager = window_manager

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

        # Start tracking
        self.start_tracking()

    def start_tracking(self):
        """Start mouse tracking."""
        self.logger.info("Starting mouse tracking")
        self.update_timer.start(50)  # 50ms for smooth tracking

    def stop_tracking(self):
        """Stop mouse tracking."""
        self.logger.info("Stopping mouse tracking")
        self.update_timer.stop()

    def _update_position(self):
        """Update mouse position and emit signal if changed."""
        try:
            new_position = pyautogui.position()

            if self.current_position != new_position:
                self.current_position = new_position
                self.position_changed.emit((new_position.x, new_position.y))

            # Check for click events
            self._check_for_clicks(new_position)

        except Exception as e:
            self.logger.error(f"Error updating mouse position: {e}")

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

        # Calculate playable area information
        playable_info = self._get_playable_area_info(x, y)

        # Log click with playable area percentage
        if playable_info.get("inside_playable", False):
            self.logger.info(
                f"Click {button} at ({x}, {y}) - Playable area: {playable_info['x_percent']:.1f}%, {playable_info['y_percent']:.1f}%"
            )
        else:
            self.logger.info(f"Click {button} at ({x}, {y}) - Outside playable area")

        self.click_detected.emit((x, y), button, playable_info)

    def _get_playable_area_info(self, x: int, y: int) -> Dict:
        """Get playable area information for a screen position."""
        if not self.window_manager:
            return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

        try:
            # Get current coordinates from window manager
            coords = self.window_manager.get_all_coordinates()
            if not coords:
                return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

            playable_area = coords.get("playable_area", {})
            if not playable_area:
                return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

            # Check if click is inside playable area
            px = playable_area.get("x", 0)
            py = playable_area.get("y", 0)
            pw = playable_area.get("width", 0)
            ph = playable_area.get("height", 0)

            if px <= x <= px + pw and py <= y <= py + ph:
                # Calculate percentage within playable area
                x_percent = ((x - px) / pw) * 100
                y_percent = ((y - py) / ph) * 100

                return {
                    "inside_playable": True,
                    "x_percent": x_percent,
                    "y_percent": y_percent,
                    "playable_area": playable_area,
                }
            else:
                return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

        except Exception as e:
            self.logger.error(f"Error calculating playable area info: {e}")
            return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

    def get_current_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        try:
            pos = pyautogui.position()
            return (pos.x, pos.y)
        except Exception:
            return (0, 0)

    def get_click_count(self) -> int:
        """Get total click count."""
        return self.click_count

    def get_last_action(self) -> str:
        """Get last recorded action."""
        return self.last_action

    def record_click(self, x: int, y: int, button: str = "left"):
        """Record a click event (legacy method for backwards compatibility)."""
        self._handle_click(x, y, button)

    def get_stats(self) -> Dict:
        """Get mouse tracking statistics."""
        pos = self.get_current_position()

        # Get playable area info for current position
        playable_info = self._get_playable_area_info(pos[0], pos[1])

        stats = {
            "current_position": f"({pos[0]}, {pos[1]})",
            "click_count": self.click_count,
            "last_action": self.last_action,
            "last_click_time": self.last_click_time,
        }

        # Add playable area info if available
        if playable_info.get("inside_playable", False):
            stats["playable_area_percent"] = (
                f"{playable_info['x_percent']:.1f}%, {playable_info['y_percent']:.1f}%"
            )
        else:
            stats["playable_area_percent"] = "Outside playable area"

        return stats
