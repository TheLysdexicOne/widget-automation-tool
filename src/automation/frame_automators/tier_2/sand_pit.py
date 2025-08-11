"""
Sand Pit Automator (Frame ID: 2.1)
Handles automation for the Sand Pit frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class SandPitAutomator(BaseAutomator):
    """Automation logic for Sand Pit (Frame 2.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        # Create button engines for clean syntax
        excavate = self.create_button("excavate")

        # Main automation loop
        while self.should_continue:
            excavate.click()
            self.sleep(1)
            if not self.sleep(0.2):
                return
