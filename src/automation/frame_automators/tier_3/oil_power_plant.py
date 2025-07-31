"""
Oil Power Plant Automator (Frame ID: 3.2)
Handles automation for the Oil Power Plant frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_screen_coordinates


class OilPowerPlantAutomator(BaseAutomator):
    """Automation logic for Oil Power Plant (Frame 3.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pbar_color = (0, 149, 28)

        # Pull handle and progress bar acting as buttons
        handle = self.frame_data["interactions"]["handle"]
        pbar = self.frame_data["interactions"]["progress_bar"]

        handle_x, handle_y = grid_to_screen_coordinates(handle[0], handle[1])
        pbar_x, pbar_y = grid_to_screen_coordinates(pbar[0], pbar[1])

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            pyautogui.mouseDown(handle_x, handle_y)
            pyautogui.moveTo(pbar_x, pbar_y, duration=0)
            while self.should_continue:
                # Monitor progress bar for one second to see if it appears/fills
                monitor_start = time.time()
                progress_detected = False

                while time.time() - monitor_start < 5.0:
                    if not self.should_continue:
                        # Release mouse and exit if stopped
                        pyautogui.mouseUp()
                        return
                    if pyautogui.pixelMatchesColor(pbar_x, pbar_y, pbar_color):
                        progress_detected = True
                        break
                    time.sleep(0.1)

                if not progress_detected:
                    # No progress bar appeared - storage is full, release and break
                    pyautogui.mouseUp()
                    self.log_storage_error()
                    break

                # Progress bar appeared, keep holding and wait for next cycle
                time.sleep(5)

            # Always release mouse when exiting inner loop
            pyautogui.mouseUp()
