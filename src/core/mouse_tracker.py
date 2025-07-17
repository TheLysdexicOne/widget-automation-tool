"""
Mouse Tracker - Tracks mouse position and interactions.

This module handles mouse position tracking and provides data to other components.
Following separation of duties: Core (brains) manages mouse tracking.
"""

import logging
import time
from typing import Dict, Tuple, Optional
import pyautogui
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class MouseTracker(QObject):
    """Tracks mouse position and interactions."""

    # Signals
    position_changed = pyqtSignal(tuple)  # (x, y)
    click_detected = pyqtSignal(tuple, str)  # (x, y), button

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Mouse state
        self.current_position = None
        self.click_count = 0
        self.last_click_time = 0
        self.last_action = "None"

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

        except Exception as e:
            self.logger.error(f"Error updating mouse position: {e}")

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
        """Record a click event."""
        self.click_count += 1
        self.last_click_time = time.time()
        self.last_action = f"Click {button} at ({x}, {y})"

        self.logger.debug(f"Click recorded: {self.last_action}")
        self.click_detected.emit((x, y), button)

    def get_stats(self) -> Dict:
        """Get mouse tracking statistics."""
        pos = self.get_current_position()

        return {
            "current_position": f"({pos[0]}, {pos[1]})",
            "click_count": self.click_count,
            "last_action": self.last_action,
            "last_click_time": self.last_click_time,
        }
