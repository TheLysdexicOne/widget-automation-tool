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

    def run_automation(self):
        """Load then smelt repeatedly."""
        start_time = time.time()

        # Get button data
        load_button = self.button_manager.get_button("load")
        smelt_button = self.button_manager.get_button("smelt")

        # Main automation loop
        while self.is_running and not self.should_stop:
            # Stop after 5 minutes
            if time.time() - start_time > 300:
                break

            # FAILSAFE: Check if we're on the right frame
            if not self.engine.is_button_color_valid(load_button):
                self.trigger_failsafe_stop("Wrong frame detected - load button not valid")
                return

            # Check if Load button is available (not inactive)
            if not self.engine.is_button_inactive(load_button):
                # Click load button
                self.engine.click_button(load_button)
                self.safe_sleep(0.05)  # 50ms delay

                # If Load button is still active, click Smelt button
                if not self.engine.is_button_inactive(load_button):
                    self.engine.click_button(smelt_button)

                    # Wait until smelt button becomes active again
                    while self.is_running and not self.should_stop:
                        if not self.engine.is_button_inactive(smelt_button):
                            break
                        if not self.safe_sleep(0.1):
                            break

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(0.1):
                break
