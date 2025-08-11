"""
Core Foundry Automator (Frame ID: 5.3)
Handles automation for the Core Foundry frame in WidgetInc.
"""

import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class CoreFoundryAutomator(BaseAutomator):
    """Automation logic for Core Foundry (Frame 5.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        buttons = [
            self.create_button("button1"),
            self.create_button("button2"),
            self.create_button("button3"),
            self.create_button("button4"),
        ]

        # Main automation loop
        while self.should_continue:
            for btn in buttons:
                if btn.active():
                    btn.click()
                    break

            self.sleep(0.025)
