"""
Copper Mine Automator (Frame ID: 4.1)
Handles automation for the Copper Mine frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class CopperMineAutomator(BaseAutomator):
    """Automation logic for Copper Mine (Frame 4.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        miners = [
            self.create_button("miner1"),
            self.create_button("miner2"),
            self.create_button("miner3"),
            self.create_button("miner4"),
        ]

        # Main automation loop
        while self.should_continue:
            for miner in miners:
                if self.should_continue and miner.active():
                    miner.click()

            if not self.sleep(0.05):
                break
