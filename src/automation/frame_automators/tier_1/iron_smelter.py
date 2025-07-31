"""
Iron Smelter Automator (Frame ID: 1.2)
Handles automation for the Iron Smelter frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class IronSmelterAutomator(BaseAutomator):
    """Automation logic for Iron Smelter (Frame 1.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
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
                self.sleep(0.05)
                if load.active():
                    smelt.click()
                    self.sleep(0.1)
                    # Storage full behavior
                    if smelt.active():
                        self.log_storage_error()
                        break
            else:
                self.log_frame_error()

            if not self.sleep(0.1):
                break
