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

    def run_automation(self):
        """Click create button repeatedly."""
        start_time = time.time()

        # Get create button data
        create_button = self.button_manager.get_button("create")

        # Main automation loop
        while self.is_running and not self.should_stop:
            # Stop after 5 minutes
            if time.time() - start_time > 300:
                break

            # FAILSAFE: Check if we're on the right frame
            if not self.engine.is_button_color_valid(create_button):
                self.trigger_failsafe_stop("Wrong frame detected - create button not valid")
                return

            # Check if Create button is available (not inactive)
            if not self.engine.is_button_inactive(create_button):
                self.engine.click_button(create_button)

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(0.5):
                break
