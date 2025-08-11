"""
Helium Extractor Automator (Frame ID: 9.1)
Handles automation for the Helium Extractor frame in WidgetInc.
"""

import pyautogui

import random

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class HeliumExtractorAutomator(BaseAutomator):
    """Automation logic for Helium Extractor (Frame 9.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        click_box = self.frame_data["bbox"]["click_box"]

        # Main automation loop
        while self.should_continue:
            # Randomly click within the click box
            x = random.randint(click_box[0], click_box[2])
            y = random.randint(click_box[1], click_box[3])
            self.click(x, y)

            if not self.sleep(0.01):
                break
