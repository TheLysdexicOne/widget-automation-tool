"""
Circuit Fab Automator (Frame ID: 4.4)
Handles automation for the Circuit Fab frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class CircuitFabAutomator(BaseAutomator):
    """Automation logic for Circuit Fab (Frame 4.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pyautogui.PAUSE = 0

        engrave = self.create_button("engrave")
        lever_down = self.frame_data["interactions"]["lever_down"]
        lever_color = self.frame_data["colors"]["lever_color"]

        # Lever Positions
        lever_positions = self.frame_data["interactions"]["lever_pos"]

        fail = 0
        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            for _ in range(5):
                engrave.click()
                self.sleep(0.05)
                fail = 0

            for lever_pos in lever_positions:
                lever_pos_color = pyautogui.pixel(lever_pos[0], lever_pos[1])
                if tuple(lever_color) == lever_pos_color:
                    pyautogui.mouseDown(lever_pos[0], lever_pos[1], duration=0.2)
                    pyautogui.moveTo(lever_down[0], lever_down[1], duration=0.2)
                    pyautogui.mouseUp(duration=0.2)
                    break
            else:
                # Lever not found in any valid position
                fail += 1
            if fail > 3:
                self.log_storage_error()
                break
            if not self.sleep(0.1):
                break
