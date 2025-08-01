"""
Iron Mine Automator (Frame ID: 1.1)
Handles automation for the Iron Mine frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class IronMineAutomator(BaseAutomator):
    """Automation logic for Iron Mine (Frame 1.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        self.ore_miner()
