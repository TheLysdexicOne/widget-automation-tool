"""
Copper Mine Automator (Frame ID: 4.1)
Handles automation for the Copper Mine frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class CopperMineAutomator(BaseAutomator):
    """Automation logic for Copper Mine (Frame 4.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        self.ore_miner()
