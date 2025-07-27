"""
Widget Factory Automator (Frame ID: 1.3)
Handles automation for the Widget Factory frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ..base_automator import BaseAutomator


class WidgetFactoryAutomator(BaseAutomator):
    """Automation logic for Widget Factory (Frame 1.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        """Click create button repeatedly."""
        start_time = time.time()

        # Get create button data
        create_button = self.button_manager.get_button("create")

        # Main automation loop
        while self.is_running and not self.should_stop:
            # Stop after configured time limit
            if time.time() - start_time > self.max_run_time:
                break

            # Check if Create button is available (not inactive)
            if not self.engine.is_button_inactive(create_button):
                self.engine.click_button(create_button)  # Built-in safety validation

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(self.factory_delay):
                break
