"""
Iron Smelter Automator (Frame ID: 1.2)
Handles automation for the Iron Smelter frame in WidgetInc.
"""

import time
from typing import Any, Dict

from ..base_automator import BaseAutomator


class IronSmelterAutomator(BaseAutomator):
    """Automation logic for Iron Smelter (Frame 1.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        """Load then smelt repeatedly with storage full detection via button behavior."""
        start_time = time.time()

        # Create button engines for clean syntax
        load = self.engine.create_button(self.button_manager.get_button("load"), "load")
        smelt = self.engine.create_button(self.button_manager.get_button("smelt"), "smelt")

        # Main automation loop
        while self.is_running and not self.should_stop:
            if time.time() - start_time > self.max_run_time:
                break
            if load.active():
                load.click()
                self.sleep(0.05)
                if load.active():
                    smelt.click()
                    self.sleep(0.05)
                    # Storage full behavior
                    if smelt.active():
                        self.log_storage_error()
                        break
            else:
                self.log_frame_error()

            if not self.sleep(0.1):
                break
