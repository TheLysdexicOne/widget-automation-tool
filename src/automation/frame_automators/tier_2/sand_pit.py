"""
Sand Pit Automator (Frame ID: 2.1)
Handles automation for the Sand Pit frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class SandPitAutomator(BaseAutomator):
    """Automation logic for Sand Pit (Frame 2.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button engines for clean syntax
        excavate = self.create_button("excavate")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            if excavate.active():
                excavate.click()
                self.sleep(2)
                if not excavate.inactive():
                    self.log_storage_error()
                    break
            else:
                self.log_frame_error()
                break
            # Wait for miners to become inactive, then cycle delay
            while self.should_continue and not excavate.active():
                if not self.sleep(0.2):
                    return
