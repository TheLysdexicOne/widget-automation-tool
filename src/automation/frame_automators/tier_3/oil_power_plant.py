"""
Oil Power Plant Automator (Frame ID: 3.2)
Handles automation for the Oil Power Plant frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class OilPowerPlantAutomator(BaseAutomator):
    """Automation logic for Oil Power Plant (Frame 3.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        # Pull lever and progress bar acting as buttons
        lever_up = self.frame_data["interactions"]["lever_up"]
        lever_down = self.frame_data["interactions"]["lever_down"]

        # Main automation loop
        while self.should_continue:
            self.mouseDown(*lever_up)
            self.moveTo(*lever_down, duration=0.1)
            while self.should_continue:
                self.sleep(0.5)
            self.mouseUp()
