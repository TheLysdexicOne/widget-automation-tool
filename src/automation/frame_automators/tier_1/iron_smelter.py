"""
Iron Smelter Automator (Frame ID: 1.2)
Handles automation for the Iron Smelter frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ...automation_engine import AutomationEngine
from ..base_automator import BaseAutomator


class IronSmelterAutomator(BaseAutomator):
    """Automation logic for Iron Smelter (Frame 1.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        self.engine = AutomationEngine()
        self.max_run_time = 300  # 5 minutes max

    def is_automation_available(self) -> bool:
        """Check if Iron Smelter automation is available."""
        # Now implemented with generic automation
        return True

    def start_automation(self) -> bool:
        """Start Iron Smelter automation."""
        if self.is_running:
            self.log_info("Iron Smelter automation is already running")
            return False

        self.log_info("Starting Iron Smelter automation")
        self.is_running = True
        self.should_stop = False

        # Run the automation directly (controller handles threading)
        self._run_automation()
        return True

    def stop_automation(self) -> bool:
        """Stop Iron Smelter automation."""
        if not self.is_running:
            self.log_info("Iron Smelter automation not running")
            return True

        self.log_info("Stopping Iron Smelter automation")
        self.is_running = False
        self.should_stop = True
        return True

    def _run_automation(self):
        """Internal method that runs the automation loop."""
        self.log_info("Iron Smelter automation started")
        start_time = time.time()

        # Get button data from button manager
        if not self.button_manager.has_button("load") or not self.button_manager.has_button("smelt"):
            failsafe_reason = "Could not get coordinates for load and smelt buttons"
            self.trigger_failsafe_stop(failsafe_reason)
            return False

        # Get all button data once
        load_grid = self.button_manager.get_button_grid_coords("load")
        load_screen = self.button_manager.get_button_screen_coords("load")
        load_color = self.button_manager.get_button_color("load")

        smelt_grid = self.button_manager.get_button_grid_coords("smelt")
        smelt_screen = self.button_manager.get_button_screen_coords("smelt")
        smelt_color = self.button_manager.get_button_color("smelt")

        # Validate all button data is available
        if not all([load_grid, load_screen, load_color, smelt_grid, smelt_screen, smelt_color]):
            failsafe_reason = "Missing button coordinate or color data"
            self.trigger_failsafe_stop(failsafe_reason)
            return False

        # Type assertions for safety (we've already validated above)
        assert load_grid is not None and load_screen is not None and load_color is not None
        assert smelt_grid is not None and smelt_screen is not None and smelt_color is not None

        try:
            while self.is_running and not self.should_stop and (time.time() - start_time) < self.max_run_time:
                # Button data already validated and type-asserted above

                # FAILSAFE: Check if Load button is a valid button
                if not self.engine.is_valid_button_color(load_grid[0], load_grid[1], load_color):
                    failsafe_reason = f"Load button at grid {load_grid} is not a {load_color} button"
                    self.trigger_failsafe_stop(failsafe_reason)
                    break

                # Check if Load button is available (not inactive)
                if not self.engine.is_button_inactive(load_grid[0], load_grid[1], load_color):
                    # Click load button using button manager coordinates
                    load_success = self.engine.click_at(load_screen[0], load_screen[1])
                    if load_success:
                        # Wait 50ms as specified in automation.md
                        if not self.safe_sleep(0.05):  # 50ms
                            break

                        # Check if Load button is still not inactive and check Smelt button failsafe
                        if not self.engine.is_button_inactive(load_grid[0], load_grid[1], load_color):
                            # FAILSAFE: Check if Smelt button is a valid button
                            if not self.engine.is_valid_button_color(smelt_grid[0], smelt_grid[1], smelt_color):
                                failsafe_reason = f"Smelt button at grid {smelt_grid} is not a {smelt_color} button"
                                self.trigger_failsafe_stop(failsafe_reason)
                                break

                            # Click smelt button using button manager coordinates
                            smelt_success = self.engine.click_at(smelt_screen[0], smelt_screen[1])
                            if smelt_success:
                                # Wait until smelt button becomes active again (not inactive)
                                while self.is_running and not self.should_stop:
                                    if not self.engine.is_button_inactive(smelt_grid[0], smelt_grid[1], smelt_color):
                                        break
                                    if not self.safe_sleep(0.1):  # Check every 100ms
                                        break

                            else:
                                self.log_error("Failed to click Smelt button")
                    else:
                        self.log_error("Failed to click Load button")

        except Exception as e:
            self.log_error(f"Error in Iron Smelter automation: {e}")
        finally:
            self.is_running = False
            self.log_info("Iron Smelter automation completed")
