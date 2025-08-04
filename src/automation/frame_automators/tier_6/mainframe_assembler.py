"""
Mainframe Assembler Automator (Frame ID: 6.3)
Handles automation for the Mainframe Assembler frame in WidgetInc.
"""

import os
import json
import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot, get_box_no_border


class MainframeAssemblerAutomator(BaseAutomator):
    """Automation logic for Mainframe Assembler (Frame 6.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
    
    def 

    def run_automation(self):
        start_time = time.time()

        matrix_bbox = self.frame_data["frame_xy"]["bbox"]["matrix_bbox"]
        bucket_y = self.frame_data["frame_xy"]["interactions"]["bucket_y"][1]
        bucket_color = self.frame_data["colors"]["bucket_color"]
        matrix_colors = [(r, g, b) for r in range(31) for g in range(256) for b in range(31)]

        full_bbox = get_box_no_border(matrix_bbox, matrix_colors)
        x1, y1, x2, y2 = full_bbox

        
        self.logger.info(f"Matrix bounding box: ({x1}, {y1}, {x2}, {y2})")


        # Find lowest point of the matrix



        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break

        #     if not self.sleep(0.1):
        #         break

        #     screenshot = get_frame_screenshot()
        #     x1, y1, x2, y2 = matrix_bbox
        #     width = x2 - x1

        #     best_x = None
        #     for x in range(x1, x2, int(width / 20)):
        #         pixel = screenshot.getpixel((x,))
