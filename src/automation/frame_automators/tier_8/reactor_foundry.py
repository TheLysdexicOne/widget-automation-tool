"""
Reactor Foundry Automator (Frame ID: 8.3)
Handles automation for the Reactor Foundry frame in WidgetInc.
"""

import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator


class ReactorFoundryAutomator(BaseAutomator):
    """Automation logic for {filename} (Frame {id}})."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0.01

    def run_automation(self):
        self.left = self.frame_data["interactions"]["left"]
        self.top = self.frame_data["interactions"]["top"]
        self.right = self.frame_data["interactions"]["right"]
        self.bottom = self.frame_data["interactions"]["bottom"]

        self.moveTo(*self.left)
        self.mouseDown(*self.left, duration=0.1)
        # Main automation loop
        while self.should_continue:
            self.moveTo(*self.top, duration=0.05)
            self.moveTo(*self.right, duration=0.05)
            self.moveTo(*self.bottom, duration=0.05)
            self.moveTo(*self.left, duration=0.05)
            if not self.sleep(0.05):
                break
        self.moveTo(*self.left, duration=0.1)
        self.mouseUp()
