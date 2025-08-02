"""
Capacitor Bank Automator (Frame 3.4)
Handles automation for the Capacitor Bank frame in WidgetInc.
"""

import time
import pyautogui
from PIL import ImageGrab

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_fill_by_color


class CapacitorBankAutomator(BaseAutomator):
    """Automation logic for Capacitor Bank (Frame 3.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()
        self.screenshot = ImageGrab.grab(all_screens=True)

        # Create button objects
        self.plus1 = self.create_button("plus1")
        self.plus2 = self.create_button("plus2")
        self.plus4 = self.create_button("plus4")
        self.plus8 = self.create_button("plus8")

        # Get voltage box coordinates
        self.voltage_box = self.frame_data["interactions"]["voltage_box"]
        self.empty_color = self.frame_data["colors"]["empty_color"]
        self.fill_colors = [
            self.frame_data["colors"]["fill_color1"],
            self.frame_data["colors"]["fill_color2"],
            self.frame_data["colors"]["fill_color3"],
        ]

        # Progress bar coordinates
        self.pbar_x, self.pbar_y = self.frame_data["interactions"]["pbar"]
        self.pbar_color = self.frame_data["colors"]["pbar_color"]

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            # Get voltage box fill - fix argument order
            fill = get_fill_by_color(self.voltage_box, self.empty_color, self.fill_colors)
            voltage = round(15 * fill / 100)
            self.log_info(f"Current voltage: {voltage}")
            if voltage > 0:
                self.match_voltage(voltage)

                if self.monitor_progress_bar():
                    self.screenshot = ImageGrab.grab(all_screens=True)
                    continue
            break

    def match_voltage(self, voltage):
        """Click buttons to match target voltage."""
        buttons = [(8, self.plus8), (4, self.plus4), (2, self.plus2), (1, self.plus1)]

        for value, button in buttons:
            while voltage >= value:
                button.click()
                voltage -= value
                time.sleep(0.1)

    def monitor_progress_bar(self):
        """Monitor progress bar for 6 seconds to see if it completes."""
        start_time = time.time()
        completion_detected = False

        while time.time() - start_time < 6.25:
            # Get live pixel data using pyautogui
            current_pixel = pyautogui.pixel(self.pbar_x, self.pbar_y)

            if current_pixel == self.pbar_color:
                completion_detected = True

            time.sleep(0.1)

        # After 6 seconds, return whether completion was detected at any point
        return completion_detected
