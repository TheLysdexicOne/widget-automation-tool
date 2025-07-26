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
            # Main automation loop with button manager
            while self.is_running and not self.should_stop:
                # Check if max time exceeded
                if time.time() - start_time > self.max_automation_time:
                    self.log_info(f"Iron Mine automation stopped - max time ({self.max_automation_time}s) reached")
                    break

                # Check each miner using button manager
                for miner_name in miner_buttons:
                    grid_coords = self.button_manager.get_button_grid_coords(miner_name)
                    screen_coords = self.button_manager.get_button_screen_coords(miner_name)
                    color = self.button_manager.get_button_color(miner_name)

                    # Skip if any coordinate data is missing
                    if not grid_coords or not screen_coords or not color:
                        self.log_error(f"Missing coordinate data for {miner_name}")
                        continue

                    # FAILSAFE: Check if this is a valid button
                    if not self.engine.is_valid_button_color(grid_coords[0], grid_coords[1], color):
                        failsafe_reason = f"{miner_name} at grid {grid_coords} is not a valid {color} button"
                        self.trigger_failsafe_stop(failsafe_reason)
                        break

                    # Check if button is not inactive
                    if not self.engine.is_button_inactive(grid_coords[0], grid_coords[1], color):
                        success = self.engine.click_at(screen_coords[0], screen_coords[1])
                        if not success:
                            self.log_error(f"Failed to click {miner_name} at screen {screen_coords}")

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
