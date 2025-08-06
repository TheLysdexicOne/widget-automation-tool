"""
Copper Forge Automator (Frame ID: 4.2)
Handles automation for the Copper Forge frame in WidgetInc.
"""

from typing import Any, Dict

from automation.base_automator import BaseAutomator


class CopperForgeAutomator(BaseAutomator):
    """Automation logic for Copper Forge (Frame 4.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        self.smelter_cycle()
