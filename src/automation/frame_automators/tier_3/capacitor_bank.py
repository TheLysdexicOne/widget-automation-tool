"""
Capacitor Bank Automator (Frame 3.4)
Handles automation for the Capacitor Bank frame in WidgetInc.
"""

import time
import pyautogui
from PIL import ImageGrab

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_screenshot_coords, grid_to_screen_coords


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

        # Get voltage meter coordinates
        self.vtop = self.frame_data["interactions"]["voltage_meter_top"]
        self.vbot = self.frame_data["interactions"]["voltage_meter_bottom"]
        self.vfill_color = (72, 237, 56)

        # Convert to screen coordinates
        self.vtop_coords = grid_to_screenshot_coords(self.vtop[0], self.vtop[1])
        self.vbot_coords = grid_to_screenshot_coords(self.vbot[0], self.vbot[1])
        self.bar_height = self.vbot_coords[1] - self.vtop_coords[1]

        # Progress bar coordinates
        self.pbar = self.frame_data["interactions"]["progress_bar"]
        self.pbar_coords = grid_to_screen_coords(self.pbar[0], self.pbar[1])
        self.pbar_color = tuple(self.pbar[2])

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            voltage = self.calc_voltage()
            self.log_info(f"Current voltage: {voltage}")
            if voltage > 0:
                self.match_voltage(voltage)

                if self.monitor_progress_bar():
                    self.screenshot = ImageGrab.grab(all_screens=True)
                    continue
            break

    def calc_voltage(self):
        """Calculate voltage from fill level (1-15)."""
        for y in range(self.vtop_coords[1], self.vbot_coords[1]):
            if self.screenshot.getpixel((self.vtop_coords[0], y)) == self.vfill_color:
                fill_level = self.bar_height - (y - self.vtop_coords[1])
                fill_percentage = fill_level / self.bar_height
                return round(15 * fill_percentage)
        return 0

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
            current_pixel = pyautogui.pixel(self.pbar_coords[0], self.pbar_coords[1])

            if current_pixel == self.pbar_color:
                completion_detected = True

            time.sleep(0.1)

        # After 6 seconds, return whether completion was detected at any point
        return completion_detected
