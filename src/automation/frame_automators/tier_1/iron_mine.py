"""
Iron Mine Automator (Frame ID: 1.1)
Handles automation for the Iron Mine frame in WidgetInc.
"""

import time
import sys
from typing import Any, Dict

from ...automation_engine import AutomationEngine
from ..base_automator import BaseAutomator


class IronMineAutomator(BaseAutomator):
    """Automation logic for Iron Mine (Frame 1.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        self.engine = AutomationEngine()
        self.max_automation_time = 600.0  # Maximum time to run automation (for testing)

    def run_automation(self):
        """Click all available miners repeatedly."""
        start_time = time.time()
        miner_buttons = ["miner1", "miner2", "miner3", "miner4"]

        # Get all miner button data
        miners = []
        for miner_name in miner_buttons:
            button_data = self.button_manager.get_button(miner_name)
            miners.append(button_data)

        # Main automation loop
        while self.is_running and not self.should_stop:
            # Stop after 10 minutes
            if time.time() - start_time > 600:
                break

            failed = 0
            for miner in miners:
                # FAILSAFE: Check if we're on the right frame
                if not self.engine.is_button_color_valid(miner):
                    self.trigger_failsafe_stop("Wrong frame detected - miner button not valid")
                    return

                if not self.engine.is_button_inactive(miner):
                    self.engine.click_button(miner)
                    self.safe_sleep(0.05)
                    if not self.engine.is_button_inactive(miner):
                        failed += 1

            # Storage full detection - break immediately
            if failed >= 4:
                self.log_info("Storage full - stopping automation")
                break

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(0.1):
                break
