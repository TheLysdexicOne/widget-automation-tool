"""
Plastic Extractor Automator (Frame ID: 4.3)
Handles automation for the Plastic Extractor frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict
from PIL import ImageGrab

from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_playable_area_coords, get_monitor_screenshot


class PlasticExtractorAutomator(BaseAutomator):
    """Automation logic for Plastic Extractor (Frame 4.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        extract = self.create_button("extract")
        pressurize = self.create_button("pressurize")
        screenshot = get_monitor_screenshot()
        grid_x = 160
        grid_y = 22
        # should be ~1720,238
        coords = grid_to_playable_area_coords(grid_x, grid_y)
        print(f"Grid coordinates: {coords}")

        # self.x = self.frame_data["interactions"]["box"]
        # colors = self.frame_data["colors"]

        # self.pixel_top_xy = grid_to_screen_coords(*self.grid_top)
        # fail = 0
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break

        #     pixel_color = pyautogui.pixel(self.pixel_top_xy[0], self.pixel_top_xy[1])
        #     if pixel_color != self.fill_color:
        #         for _ in range(7):
        #             pressurize.click()
        #     elif pixel_color == self.fill_color:
        #         extract.click()
        #         self.sleep(0.1)
        #         if extract.active():
        #             fail += 1
        #         while extract.inactive():
        #             if not self.sleep(1):
        #                 break
        #     if fail > 3:
        #         self.log_storage_error()
        #     if not self.sleep(0.05):
        #         break
