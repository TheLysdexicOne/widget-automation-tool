"""
Iron Mine Automator (Frame ID: 1.1)
Handles automation for the Iron Mine frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ...automation_engine import AutomationEngine
from ..base_automator import BaseAutomator


class IronMineAutomator(BaseAutomator):
    """Automation logic for Iron Mine (Frame 1.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        self.engine = AutomationEngine()
        self.max_automation_time = 600.0  # Maximum time to run automation (for testing)

    def start_automation(self) -> bool:
        """Start Iron Mine automation."""
        if self.is_running:
            self.log_info("Iron Mine automation is already running")
            return False

        self.log_info("Starting Iron Mine automation")
        self.is_running = True
        self.should_stop = False

        # Run the automation directly (controller handles threading)
        self._run_automation()
        return True

    def _run_automation(self):
        """Internal method that runs the automation loop."""
        # Start timer for max automation time
        start_time = time.time()

        # Get all miner buttons - no coordinate conversion needed!
        miner_buttons = ["miner1", "miner2", "miner3", "miner4"]

        # Validate all buttons have screen coordinates
        for miner_name in miner_buttons:
            if not self.button_manager.has_button(miner_name):
                failsafe_reason = f"Could not get screen coordinates for {miner_name}"
                self.trigger_failsafe_stop(failsafe_reason)
                return False

        try:
            # Main automation loop with simplified button management
            while self.is_running and not self.should_stop:
                # Check if max time exceeded
                if time.time() - start_time > self.max_automation_time:
                    self.log_info(f"Iron Mine automation stopped - max time ({self.max_automation_time}s) reached")
                    break

                # Check each miner using simplified button data
                for miner_name in miner_buttons:
                    button_data = self.button_manager.get_button(miner_name)

                    # Skip if button data is missing
                    if not button_data:
                        self.log_error(f"Missing button data for {miner_name}")
                        continue

                    # FAILSAFE: Check if this is a valid button
                    if not self.engine.is_valid_button_color_screen(button_data):
                        failsafe_reason = f"{miner_name} at screen ({button_data[0]}, {button_data[1]}) is not a valid {button_data[2]} button"
                        self.trigger_failsafe_stop(failsafe_reason)
                        break

                    # Check if button is not inactive
                    if not self.engine.is_button_inactive_screen(button_data):
                        success = self.engine.click_button(button_data, miner_name)
                        if not success:
                            self.log_error(f"Failed to click {miner_name}")

                # If failsafe was triggered, break out of main loop
                if self.should_stop:
                    self.log_info("Iron Mine automation stopped due to failsafe trigger")
                    break

                # Sleep between cycles as per automation.md (1 second)
                if not self.safe_sleep(1.0):
                    break

            self.log_info("Iron Mine automation stopped")
            return True

        except Exception as e:
            self.log_error(f"Error in Iron Mine automation: {e}")
            return False
        finally:
            self.is_running = False

    def stop_automation(self) -> bool:
        """Stop Iron Mine automation."""
        if not self.is_running:
            self.log_info("Iron Mine automation is not running")
            return True

        self.log_info("Stopping Iron Mine automation")
        self.should_stop = True
        self.is_running = False

        self.log_info("Iron Mine automation stopped successfully")
        return True
