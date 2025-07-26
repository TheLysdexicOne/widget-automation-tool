"""
Base Automator Class
Provides common functionality for all frame automations.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from utility.coordinate_utils import ButtonManager


class BaseAutomator(ABC):
    """Base class for all frame automators."""

    def __init__(self, frame_data: Dict[str, Any]):
        self.frame_data = frame_data
        self.frame_id = frame_data.get("id", "unknown")
        self.frame_name = frame_data.get("name", "Unknown")
        self.item = frame_data.get("item", "Unknown Item")

        # Setup logging
        safe_name = self.frame_name.encode("ascii", "replace").decode("ascii")
        self.logger = logging.getLogger(f"automation.{safe_name.lower().replace(' ', '_')}")

        # Button management
        self.button_manager = ButtonManager(frame_data)

        # Automation state
        self.is_running = False
        self.should_stop = False

        # UI callback for failsafe/emergency stop
        self.ui_callback = None

    @abstractmethod
    def start_automation(self) -> bool:
        """
        Start the automation process for this frame.
        Returns True if automation started successfully, False otherwise.
        """
        pass

    @abstractmethod
    def stop_automation(self) -> bool:
        """
        Stop the automation process for this frame.
        Returns True if automation stopped successfully, False otherwise.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            "frame_id": self.frame_id,
            "frame_name": self.frame_name,
            "is_running": self.is_running,
            "should_stop": self.should_stop,
        }

    def safe_sleep(self, duration: float) -> bool:
        """
        Sleep for given duration while checking for stop signal.
        Returns True if sleep completed normally, False if interrupted.
        """
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.should_stop:
                return False
            time.sleep(0.1)  # Check every 100ms
        return True

    def log_info(self, message: str):
        """Log info message with emoji-safe encoding."""
        safe_message = message.encode("ascii", "replace").decode("ascii")
        self.logger.info(safe_message)

    def log_debug(self, message: str):
        """Log debug message with emoji-safe encoding."""
        safe_message = message.encode("ascii", "replace").decode("ascii")
        self.logger.debug(safe_message)

    def log_error(self, message: str):
        """Log error message with emoji-safe encoding."""
        safe_message = message.encode("ascii", "replace").decode("ascii")
        self.logger.error(safe_message)

    def set_ui_callback(self, callback):
        """Set the UI callback function for automation events."""
        self.ui_callback = callback

    def trigger_failsafe_stop(self, reason: str):
        """Trigger a failsafe stop and notify the UI."""
        self.should_stop = True
        self.is_running = False
        self.log_error(f"Failsafe triggered: {reason}")

        # Notify UI to re-enable buttons
        if self.ui_callback:
            try:
                self.ui_callback("failsafe_stop", self.frame_id, reason)
            except Exception as e:
                self.log_error(f"Error calling UI callback: {e}")
