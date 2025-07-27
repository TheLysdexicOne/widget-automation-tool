"""
Iron Mine Automator (Frame ID: 1.1)
Handles automation for the Iron Mine frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ..base_automator import BaseAutomator


class IronMineAutomator(BaseAutomator):
    """Automation logic for Iron Mine (Frame 1.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Get all miner button data
        miner_buttons = ["miner1", "miner2", "miner3", "miner4"]
        miners = [self.button_manager.get_button(name) for name in miner_buttons]

        # Main automation loop
        while self.is_running and not self.should_stop:
            if time.time() - start_time > self.max_run_time:
                break
            failed = 0
            for miner in miners:
                if self.engine.button_active(miner):
                    self.engine.click_button(miner)
                    self.safe_sleep(0.1)
                    if self.engine.button_active(miner):
                        failed += 1
                        print(failed)

            # Storage full behavior
            if failed >= 4:
                self.log_info("Button behavior suggests storage is full. Stopping.")
                break
            while self.is_running and not self.should_stop and self.engine.button_inactive(miners[0]):
                self.safe_sleep(0.2)

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(0.1):
                break

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(self.cycle_delay):
                break
