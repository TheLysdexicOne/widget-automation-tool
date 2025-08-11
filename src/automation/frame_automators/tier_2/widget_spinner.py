"""
Widget Spinner Automator (Frame ID: 2.4)
Handles automation for the Widget Spinner frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class WidgetSpinnerAutomator(BaseAutomator):
    """Automation logic for Widget Spinner (Frame 2.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        # Create button engines for clean syntax
        spin = self.create_button("spin")
        watch_point = self.frame_data["interactions"]["watch_point"]
        watch_color = self.frame_data["colors"]["watch_color"]

        # Main automation loop
        while self.should_continue:
            current_color = self.pixel(watch_point[0], watch_point[1])
            if current_color != watch_color:
                spin.click()
                self.sleep(0.1)
            if not self.sleep(0.01):
                break
