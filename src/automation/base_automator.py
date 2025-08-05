"""
Base Automator Class
Provides common functionality for all frame automations.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict
import pyautogui

from utility.button_manager import ButtonManager
from automation.scan_engine import ScanEngine
from automation.automation_engine import AutomationEngine


class BaseAutomator(ABC):
    """Base class for all frame automators."""

    def __init__(self, frame_data: Dict[str, Any]):
        self.frame_data = frame_data
        self.frame_id = frame_data.get("id", "unknown")
        self.frame_name = frame_data.get("name", "Unknown")
        self.item = frame_data.get("item", "Unknown Item")

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)

        # Disable pyautogui safety delay for faster automation
        pyautogui.PAUSE = 0

        # Button management
        self.button_manager = ButtonManager(frame_data)
        self.engine = AutomationEngine()
        self.scan = ScanEngine()

        # Automation state
        self.is_running = False
        self.should_stop = False

        # Default timeout for automations (can be overridden by subclasses)
        self.max_run_time = 300  # 5 minutes default

        # Standard timing constants for consistent behavior
        self.click_delay = 0.05  # 50ms delay after clicks
        self.cycle_delay = 0.1  # 100ms delay between cycles
        self.factory_delay = 0.5  # 500ms delay for factory operations

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

        # Ensure mouse button is released when stopping
        self.cleanup_mouse_state()

        return True

    def cleanup_mouse_state(self):
        """Ensure mouse button is released - safety cleanup for automations that use mouse operations."""
        try:
            pyautogui.mouseUp()
            self.log_debug("Mouse button released during cleanup")
        except Exception as e:
            self.log_debug(f"Error during mouse cleanup: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            "frame_id": self.frame_id,
            "frame_name": self.frame_name,
            "is_running": self.is_running,
            "should_stop": self.should_stop,
        }

    @property
    def should_continue(self) -> bool:
        """Check if automation should continue running."""
        return self.is_running and not self.should_stop

    def sleep(self, duration: float) -> bool:
        """
        Sleep for given duration while checking for stop signal.
        Returns True if sleep completed normally, False if interrupted.
        """
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.should_stop:
                return False
            time.sleep(0.01)  # Check every 100ms
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

        # Ensure mouse button is released during failsafe
        self.cleanup_mouse_state()

        # Notify UI to re-enable buttons
        if self.ui_callback:
            try:
                self.ui_callback("failsafe_stop", self.frame_id, reason)
            except Exception as e:
                self.log_error(f"Error calling UI callback: {e}")

    def check_button_failsafe(self, button_data: list, button_name: str) -> bool:
        """Check if button is valid and trigger failsafe if not."""
        return self.engine.failsafe_color_validation(
            button_data, button_name, trigger_failsafe_callback=self.trigger_failsafe_stop
        )

    def create_button(self, button_name: str):
        """Create a button engine for the given button name."""
        return self.engine.create_button(self.button_manager.get_button(button_name), button_name)

    """
    Predefined Logging Messages
    """

    def log_storage_error(self):
        self.should_stop = True
        self.cleanup_mouse_state()
        self.log_info("Stopping. Storage is likely full or resources are missing.")

    def log_frame_error(self):
        self.should_stop = True
        self.cleanup_mouse_state()
        self.log_info("Stopping. Frame validation failed or frame is not active.")

    def log_timeout_error(self):
        self.should_stop = True
        self.cleanup_mouse_state()
        self.log_info("Stopping. Waiting for action timed out.")

    """
    Repeated Automations
    """

    def ore_miner(self):
        # For all miners in frame_data["buttons"]
        miner_buttons = [name for name in self.frame_data["buttons"] if "miner" in name]
        start_time = time.time()
        miners = [self.create_button(name) for name in miner_buttons]
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            failed = 0
            for miner in miners:
                if miner.active():
                    miner.click()
                    self.sleep(0.1)
                    if miner.active():
                        failed += 1
                else:
                    failed += 1

            # Storage full behavior - stop automation completely
            if failed >= 4:
                self.log_storage_error()
                break

            # Wait for miners to become inactive, then cycle delay
            while self.should_continue and miners[0].inactive():
                if not self.sleep(0.2):
                    return
            self.sleep(0.2)

    def smelter_cycle(self):
        """Load then smelt repeatedly with storage full detection via button behavior."""
        start_time = time.time()

        # Create button engines for clean syntax
        load = self.create_button("load")
        smelt = self.create_button("smelt")

        # Main automation loop
        while self.should_continue:
            # Start Timer
            if time.time() - start_time > self.max_run_time:
                break

            if load.active():
                load.click()
                self.sleep(0.1)
                if load.active():
                    smelt.click()
                    # Storage full behavior
                    if smelt.active():
                        self.log_storage_error()
                        break
                    while self.should_continue and smelt.inactive():
                        self.sleep(0.2)
            else:
                self.log_frame_error()

            while self.should_continue and load.inactive():
                if not self.sleep(0.2):
                    return
