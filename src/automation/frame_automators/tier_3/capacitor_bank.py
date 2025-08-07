"""
Capacitor Bank Automator (Frame 3.4)
Handles automation for the Capacitor Bank frame in WidgetInc.
"""

import time
import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_vertical_fill


class CapacitorBankAutomator(BaseAutomator):
    """Automation logic for Capacitor Bank (Frame 3.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button objects
        self.plus1 = self.create_button("plus1")
        self.plus2 = self.create_button("plus2")
        self.plus4 = self.create_button("plus4")
        self.plus8 = self.create_button("plus8")

        # Get voltage box coordinates
        vbox_top = self.frame_data["frame_xy"]["interactions"]["voltage_box_top"]
        vbox_bot = self.frame_data["frame_xy"]["interactions"]["voltage_box_bot"]
        vbox_x = vbox_top[0]
        vbox_y_top = vbox_top[1]
        vbox_y_bot = vbox_bot[1]

        empty_color = self.frame_data["colors"]["empty_color"]
        filled_colors = self.frame_data["colors"]["filled_colors"]

        # Progress bar coordinates
        one_volt = self.frame_data["interactions"]["1v"]

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            # Get voltage box fill - fix argument order
            fill = get_vertical_fill(vbox_x, vbox_y_top, vbox_y_bot, empty_color, filled_colors)
            voltage = round(15 * fill / 100)
            self.log_info(f"Current voltage: {voltage}")
            if voltage > 0:
                self.match_voltage(voltage)
                print(f"Matched voltage: {voltage}V")
            print("waiting 4 seconds")
            self.sleep(4)

            while self.should_continue and pyautogui.pixel(*one_volt) not in filled_colors:
                print(f"{pyautogui.pixel(*one_volt)} not in {filled_colors}")
                print("Waiting for 1V to fill...")
                self.sleep(0.5)
            if not self.sleep(0.5):
                break

    def match_voltage(self, voltage):
        """Click buttons to match target voltage."""
        buttons = [(8, self.plus8), (4, self.plus4), (2, self.plus2), (1, self.plus1)]

        for value, button in buttons:
            while voltage >= value:
                button.click()
                voltage -= value
                time.sleep(0.1)
