"""
Uranium Mine Automator (Frame ID: 7.1)
Handles automation for the Uranium Mine frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.coordinate_utils import (
    conv_frame_percent_to_frame_coords,
    conv_frame_percent_to_screen_coords,
    conv_frame_coords_to_frame_percent,
    conv_frame_coords_to_screen_coords,
    conv_screen_coords_to_frame_coords,
    conv_screen_coords_to_frame_percent,
    conv_frame_percent_to_screen_bbox,
)


class UraniumMineAutomator(BaseAutomator):
    """Automation logic for Uranium Mine (Frame 7.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        test = (0.5, 0.5)
        print(f"Converted {test} to frame coords: {conv_frame_percent_to_frame_coords(*test)}")
        print(f"Converted {test} to screen coords: {conv_frame_percent_to_screen_coords(*test)}")

        test2 = (1080, 720)
        print(f"Converting {test2} to frame percent: {conv_frame_coords_to_frame_percent(*test2)}")
        print(f"Converting {test2} to screen coords: {conv_frame_coords_to_screen_coords(*test2)}")

        test3 = (-1280, 720)
        print(f"Converting {test3} to frame percent: {conv_screen_coords_to_frame_percent(*test3)}")
        print(f"Converting {test3} to frame coords: {conv_screen_coords_to_frame_coords(*test3)}")

        test4 = (0.4, 0.6, 0.8, 0.9)
        print(f"Converting {test4} to screen bbox: {conv_frame_percent_to_screen_bbox(test4)}")
        # Main automation loop
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break

        #     if not self.sleep(0.1):
        #         break
