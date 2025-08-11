"""
Plastic Extractor Automator (Frame ID: 4.3)
Handles automation for the Plastic Extractor frame in WidgetInc.
"""

import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class PlasticExtractorAutomator(BaseAutomator):
    """Automation logic for Plastic Extractor (Frame 4.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        extract = self.create_button("extract")
        pressurize = self.create_button("pressurize")

        while self.should_continue:
            for _ in range(35):
                if self.should_continue:
                    pressurize.click()
                    self.sleep(0.01)

            extract.click()
            self.sleep(1)
            while self.should_continue and extract.inactive():
                self.sleep(0.25)
            if not self.sleep(0.1):
                break
