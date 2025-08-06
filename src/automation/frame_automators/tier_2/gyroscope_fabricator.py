"""
Gyroscope Fabricator Automator (Frame ID: 2.3)
Handles automation for the Gyroscope Fabricator frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class GyroscopeFabricatorAutomator(BaseAutomator):
    """Automation logic for Gyroscope Fabricator (Frame 2.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button engines for clean syntax
        create = self.create_button("create")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            if create.active():
                create.hold_click(0.45)
