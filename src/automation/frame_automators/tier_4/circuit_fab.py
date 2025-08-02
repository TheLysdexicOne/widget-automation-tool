"""
Circuit Fab Automator (Frame ID: 4.4)
Handles automation for the Circuit Fab frame in WidgetInc.
"""

import time

from typing import Any, Dict

import pyautogui

from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_screen_coords


class CircuitFabAutomator(BaseAutomator):
    """Automation logic for Circuit Fab (Frame 4.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        engrave = self.create_button("engrave")
        lever_up = self.frame_data["interactions"]["lever_up"]
        lever_down = self.frame_data["interactions"]["lever_down"]
        lever_color = self.frame_data["colors"]["lever_color"]

        # Lever Positions
        lever1 = self.frame_data["interactions"]["lever1"]
        lever2 = self.frame_data["interactions"]["lever2"]
        lever3 = self.frame_data["interactions"]["lever3"]
        lever4 = self.frame_data["interactions"]["lever4"]
        lever5 = self.frame_data["interactions"]["lever5"]

        lever_positions = [lever_up, lever1, lever2, lever3, lever4, lever5]

        for lever_pos in lever_positions:
            # create screen coordinates for lever positions
            lever_up_xy = grid_to_screen_coords(lever_up[0], lever_up[1])
            lever_down_xy = grid_to_screen_coords(lever_down[0], lever_down[1])
            lever_xy = [grid_to_screen_coords(pos[0], pos[1]) for pos in lever_positions]

        fail = 0
        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            for _ in range(5):
                engrave.click()
                fail = 0

            for lever_pos in lever_xy:
                lever_pos_color = pyautogui.pixel(lever_pos[0], lever_pos[1])
                if tuple(lever_color) == lever_pos_color:
                    pyautogui.mouseDown(lever_pos[0], lever_pos[1])
                    pyautogui.moveTo(lever_down_xy[0], lever_down_xy[1], duration=0.1)
                    pyautogui.mouseUp()
                    break
            else:
                # Lever not found in any valid position
                fail += 1
            if fail > 3:
                self.log_storage_error()
                break
            if not self.sleep(0.1):
                break
