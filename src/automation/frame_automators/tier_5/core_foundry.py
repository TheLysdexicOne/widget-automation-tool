"""
Core Foundry Automator (Frame ID: 5.3)
Handles automation for the Core Foundry frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class CoreFoundryAutomator(BaseAutomator):
    """Automation logic for Core Foundry (Frame 5.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pyautogui.PAUSE = 0

        buttons = [
            self.create_button("button1"),
            self.create_button("button2"),
            self.create_button("button3"),
            self.create_button("button4"),
        ]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            if buttons[0].active():
                buttons[0].click()
            elif buttons[1].active():
                buttons[1].click()
            elif buttons[2].active():
                buttons[2].click()
            elif buttons[3].active():
                buttons[3].click()

            self.sleep(0.025)
