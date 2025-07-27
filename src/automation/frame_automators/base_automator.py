"""
Base Automator Class
Provides common functionality for all frame automations.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from utility.coordinate_utils import ButtonManager
from automation.automation_engine import AutomationEngine


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
        self.engine = AutomationEngine()

        # Automation state
        self.is_running = False
        self.should_stop = False

        # UI callback for failsafe/emergency stop
        self.ui_callback = None

    @abstractmethod
    def run_automation(self):
        """
        Run the actual automation logic for this frame.
        This method contains the frame-specific automation logic.
        """
        pass

    def start_automation(self) -> bool:
        """Start the automation process for this frame."""
        if self.is_running:
            self.log_info(f"{self.frame_name} automation is already running")
            return False

        self.log_info(f"Starting {self.frame_name} automation")
        self.is_running = True
        self.should_stop = False

        # Run the automation directly (controller handles threading)
        self.run_automation()
        return True

    def stop_automation(self) -> bool:
        """Stop the automation process for this frame."""
        if not self.is_running:
            self.log_info(f"{self.frame_name} automation not running")
            return True

        self.log_info(f"Stopping {self.frame_name} automation")
        self.is_running = False
        self.should_stop = True
        return True
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

    def check_button_failsafe(self, button_data: list, button_name: str) -> bool:
        """
        Check if button is valid and trigger failsafe if not.
        """
        if not self.engine.is_button_color_valid(button_data):
            failsafe_reason = (
                f"{button_name} at screen ({button_data[0]}, {button_data[1]}) is not a valid {button_data[2]} button"
            )
            self.trigger_failsafe_stop(failsafe_reason)
            return False
        return True
