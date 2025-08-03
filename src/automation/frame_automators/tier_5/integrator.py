"""
Integrator Automator (Frame ID: 5.4)
Handles automation for the Integrator frame in WidgetInc.
"""

import time
import cv2
import numpy as np
from typing import Any, Dict
from PIL import ImageGrab

from automation.base_automator import BaseAutomator
from utility.window_utils import get_monitor_screenshot, screen_to_screenshot_coords, get_box


class IntegratorAutomator(BaseAutomator):
    """Automation logic for Integrator (Frame 5.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        output = self.frame_data["interactions"]["output"]
        input1 = self.frame_data["interactions"]["input1"]
        input2 = self.frame_data["interactions"]["input2"]
        input3 = self.frame_data["interactions"]["input3"]

        # op = screen_to_screenshot_coords(*output)
        # i1 = screen_to_screenshot_coords(*input1)
        # i2 = screen_to_screenshot_coords(*input2)
        # i3 = screen_to_screenshot_coords(*input3)

        border = self.frame_data["colors"]["border"]
        empty = self.frame_data["colors"]["empty"]
        red = self.frame_data["colors"]["red"]
        green = self.frame_data["colors"]["green"]

        screenshot = get_monitor_screenshot()
        box = get_box(output, border)
        print(f"Output box: {box}")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
