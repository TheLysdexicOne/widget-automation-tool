"""
Iron Mine Automator (Frame ID: 1.1)
Handles automation for the Iron Mine frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class IronMineAutomator(BaseAutomator):
    """Automation logic for Iron Mine (Frame 1.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button engines for clean syntax
        miner_buttons = ["miner1", "miner2", "miner3", "miner4"]
        miners = [self.create_button(name) for name in miner_buttons]

        # Main automation loop
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
