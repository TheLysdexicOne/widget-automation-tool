"""
Plastic Extractor Automator (Frame ID: 4.3)
Handles automation for the Plastic Extractor frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator
from utility.window_utils import get_vertical_bar_data


class PlasticExtractorAutomator(BaseAutomator):
    """Automation logic for Plastic Extractor (Frame 4.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        extract = self.create_button("extract")
        pressurize = self.create_button("pressurize")

        pressure_box = self.frame_data["interactions"]["pressure_box"]
        empty_color = self.frame_data["colors"]["empty_color"]
        filled_colors = self.frame_data["colors"]["filled_colors"]
        box_data = get_vertical_bar_data(pressure_box, empty_color, filled_colors)
        x = pressure_box[0]
        y = box_data["top"]

        fail = 0
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            pixel_color = pyautogui.pixel(x, y)
            while pixel_color not in filled_colors:
                pressurize.click()
                pixel_color = pyautogui.pixel(x, y)
            if pixel_color in filled_colors:
                extract.click()
                self.sleep(0.1)
                if extract.active():
                    fail += 1
                while extract.inactive():
                    if not self.sleep(1):
                        break
            if fail > 3:
                self.log_storage_error()
            if not self.sleep(0.05):
                break
