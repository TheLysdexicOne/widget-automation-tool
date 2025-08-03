"""
Tesla Coil Automator (Frame ID: 5.1)
Handles automation for the Tesla Coil frame in WidgetInc.
"""

import pyautogui
import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class TeslaCoilAutomator(BaseAutomator):
    """Automation logic for Tesla Coil (Frame 5.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        call_lightning = self.create_button("call_lightning")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            while self.should_continue and not call_lightning.inactive():
                pyautogui.mouseDown(call_lightning.x, call_lightning.y)
                self.sleep(0.1)
            pyautogui.mouseUp()
            if not self.sleep(0.1):
                break
