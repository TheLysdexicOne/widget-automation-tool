"""
Widget Minitizers Automator (Frame ID: 8.1)
Handles automation for the Widget Minitizers frame in WidgetInc.
"""

import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator


class WidgetMinitizersAutomator(BaseAutomator):
    """Automation logic for Widget Minitizers (Frame 8.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        shrink = self.create_button("shrink")

        # Main automation loop
        while self.should_continue:
            self.click(shrink.x, shrink.y)

            if not self.sleep(0.05):
                break
