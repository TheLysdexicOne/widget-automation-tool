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
        self.smelter_cycle()
