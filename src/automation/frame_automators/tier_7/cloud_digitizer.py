"""
Cloud Digitizer Automator (Frame ID: 7.4)
Handles automation for the Cloud Digitizer frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class CloudDigitizerAutomator(BaseAutomator):
    """Automation logic for Cloud Digitizer (Frame 7.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        interactions = self.frame_data["interactions"]
        print("Interactions:", interactions)
        print(interactions["0,0"][0])

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # 1) Scan all keys (assumed (x, y)) and record red > 125
            to_click: list[tuple[int, int]] = []
            for key in interactions:
                x, y = interactions[key]
                r, g, b = pyautogui.pixel(x, y)
                if r > 125:
                    to_click.append((x, y))

            # 2) After recording them all, click them all
            for x, y in to_click:
                if not self.should_continue:
                    break
                pyautogui.click(x, y)

            if not self.sleep(1):
                break
