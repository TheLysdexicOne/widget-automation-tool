"""
Omega Core Foundry Automator (Frame ID: 12.2)
Handles automation for the Omega Core Foundry frame in WidgetInc.
"""

import pyautogui
import time
import random

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaCoreFoundryAutomator(BaseAutomator):
    """Automation logic for Omega Core Foundry (Frame 12.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pyautogui.PAUSE = 0

        square = self.frame_data["interactions"]["square"]
        triangle = self.frame_data["interactions"]["triangle"]
        diamond = self.frame_data["interactions"]["diamond"]
        circle = self.frame_data["interactions"]["circle"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # Randomly click on the shapes
            shape = random.choice([square, triangle, diamond, circle])
            pyautogui.click(shape[0], shape[1])

            if not self.sleep(0.05):
                break
