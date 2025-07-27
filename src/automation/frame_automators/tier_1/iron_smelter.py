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

        # Get button data
        load_button = self.button_manager.get_button("load")
        smelt_button = self.button_manager.get_button("smelt")

        # Main automation loop
        while self.is_running and not self.should_stop:
            if time.time() - start_time > self.max_run_time:
                break

            if self.engine.button_active(load_button):
                self.engine.click_button(load_button)
                self.safe_sleep(0.05)
                if self.engine.button_active(load_button):
                    if self.engine.button_active(smelt_button):
                        self.engine.click_button(smelt_button)
                        self.safe_sleep(0.05)

                        # Storage full behavior
                        if self.engine.button_active(smelt_button):
                            self.log_info("Button behavior suggests storage is full. Stopping.")
                            break
                else:
                    # Load button became inactive - normal behavior, continue with short sleep
                    self.safe_sleep(0.1)  # 100ms as specified
            else:
                # Load button inactive - wait a bit
                self.safe_sleep(0.1)

            # Use safe_sleep for right-click detection between cycles
            if not self.safe_sleep(0.1):
                break
