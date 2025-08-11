"""
Battery Assembler Automator (Frame ID: 3.3)
Handles automation for the Battery Assembler frame in WidgetInc.
"""

import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class BatteryAssemblerAutomator(BaseAutomator):
    """Automation logic for Battery Assembler (Frame 3.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        """Optimized alternating plus/minus clicking with progress detection."""

        plus = self.create_button("plus")
        minus = self.create_button("minus")

        if plus.active():
            use_plus = True
        else:
            use_plus = False

        while self.should_continue:
            button = plus if use_plus else minus
            if button.active():
                button.click()
                use_plus = not use_plus

            if not self.sleep(0.01):
                break
