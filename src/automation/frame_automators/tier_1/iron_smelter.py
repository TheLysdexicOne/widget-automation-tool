"""
Iron Smelter Automator (Frame ID: 1.2)
Handles automation for the Iron Smelter frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class IronSmelterAutomator(BaseAutomator):
    """Automation logic for Iron Smelter (Frame 1.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        load = self.create_button("load")
        smelt = self.create_button("smelt")

        # Main automation loop
        while self.should_continue:
            if load.active():
                load.click()
                self.sleep(0.1)
                if load.active():
                    smelt.click()

                    while self.should_continue and smelt.inactive():
                        self.sleep(0.2)

            while self.should_continue and load.inactive():
                if not self.sleep(0.2):
                    return
