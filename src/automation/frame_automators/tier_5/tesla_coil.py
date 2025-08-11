"""
Tesla Coil Automator (Frame ID: 5.1)
Handles automation for the Tesla Coil frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class TeslaCoilAutomator(BaseAutomator):
    """Automation logic for Tesla Coil (Frame 5.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        call_lightning = self.create_button("call_lightning")

        while self.should_continue:
            # Hold down while button is active
            if self.should_continue and not call_lightning.inactive():
                self.mouseDown(call_lightning.x, call_lightning.y)
                while self.should_continue and not call_lightning.inactive():
                    self.sleep(0.1)
                self.mouseUp()
            if not self.sleep(0.1):
                break
