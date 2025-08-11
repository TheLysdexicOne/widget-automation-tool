"""
Circuit Fab Automator (Frame ID: 4.4)
Handles automation for the Circuit Fab frame in WidgetInc.
"""

import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator


class CircuitFabAutomator(BaseAutomator):
    """Automation logic for Circuit Fab (Frame 4.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        engrave = self.create_button("engrave")
        lever_down = self.frame_data["interactions"]["lever_down"]
        lever_color = self.frame_data["colors"]["lever_color"]

        # Lever Positions
        lever_positions = self.frame_data["interactions"]["lever_pos"]

        # Main automation loop
        while self.should_continue:
            for _ in range(5):
                self.click(engrave.x, engrave.y)
                self.sleep(0.05)

            for lever_pos in lever_positions:
                lever_pos_color = self.pixel(lever_pos[0], lever_pos[1])
                if tuple(lever_color) == lever_pos_color:
                    self.mouseDown(lever_pos[0], lever_pos[1], duration=0.2)
                    self.moveTo(lever_down[0], lever_down[1], duration=0.2)
                    self.mouseUp(duration=0.2)
                    break

            if not self.sleep(0.1):
                break
