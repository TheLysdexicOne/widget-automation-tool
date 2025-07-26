"""
Widget Factory Automator (Frame ID: 1.3)
Handles automation for the Widget Factory frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ...automation_engine import AutomationEngine
from ..base_automator import BaseAutomator


class WidgetFactoryAutomator(BaseAutomator):
    """Automation logic for Widget Factory (Frame 1.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        self.engine = AutomationEngine()
        self.max_run_time = 300  # 5 minutes max

    def is_automation_available(self) -> bool:
        """Check if Widget Factory automation is available."""
        # Implemented with blue button automation
        return True

    def start_automation(self) -> bool:
        """Start Widget Factory automation."""
        if self.is_running:
            self.log_info("Widget Factory automation is already running")
            return False

        self.log_info("Starting Widget Factory automation")
        self.is_running = True
        self.should_stop = False

        # Run the automation directly (controller handles threading)
        self._run_automation()
        return True

    def stop_automation(self) -> bool:
        """Stop Widget Factory automation."""
        if not self.is_running:
            self.log_info("Widget Factory automation not running")
            return True

        self.log_info("Stopping Widget Factory automation")
        self.is_running = False
        self.should_stop = True
        return True

    def _run_automation(self):
        """Internal method that runs the automation loop."""
        self.log_info("Widget Factory automation started")
        start_time = time.time()

        # Get create button data from button manager
        if not self.button_manager.has_button("create"):
            failsafe_reason = "Could not get coordinates for create button"
            self.trigger_failsafe_stop(failsafe_reason)
            return False

        # Get button data once
        create_grid = self.button_manager.get_button_grid_coords("create")
        create_screen = self.button_manager.get_button_screen_coords("create")
        create_color = self.button_manager.get_button_color("create")

        # Validate button data
        if not all([create_grid, create_screen, create_color]):
            failsafe_reason = "Missing create button coordinate or color data"
            self.trigger_failsafe_stop(failsafe_reason)
            return False

        # Type assertions for safety (we've already validated above)
        assert create_grid is not None and create_screen is not None and create_color is not None

        try:
            while self.is_running and not self.should_stop and (time.time() - start_time) < self.max_run_time:
                # FAILSAFE: Check if Create button is a valid button
                if not self.engine.is_valid_button_color(create_grid[0], create_grid[1], create_color):
                    failsafe_reason = f"Create button at grid {create_grid} is not a {create_color} button"
                    self.trigger_failsafe_stop(failsafe_reason)
                    break

                # Check if Create button is available (not inactive)
                if not self.engine.is_button_inactive(create_grid[0], create_grid[1], create_color):
                    # Click create button using button manager coordinates
                    create_success = self.engine.click_at(create_screen[0], create_screen[1])
                    if not create_success:
                        self.log_error("Failed to click Create button")

                # Use safe_sleep as per automation.md (0.5s)
                if not self.safe_sleep(0.5):
                    break

        except Exception as e:
            self.log_error(f"Error in Widget Factory automation: {e}")
        finally:
            self.is_running = False
            self.log_info("Widget Factory automation completed")
