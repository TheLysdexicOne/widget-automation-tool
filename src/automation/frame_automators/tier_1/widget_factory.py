"""
Widget Factory Automator (Frame ID: 1.3)
Handles automation for the Widget Factory frame in WidgetInc.
"""

from typing import Any, Dict

import pyautogui
from automation.base_automator import BaseAutomator


class WidgetFactoryAutomator(BaseAutomator):
    """Automation logic for Widget Factory (Frame 1.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        """Click create button repeatedly."""
        create = self.create_button("create")

        while self.should_continue:
            if not create.inactive():
                create.click()
            if not self.sleep(0.01):
                break
