"""
Quantum Tunneler Automator (Frame ID: 8.4)
Handles automation for the Quantum Tunneler frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class QuantumTunnelerAutomator(BaseAutomator):
    """Automation logic for Quantum Tunneler (Frame 8.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        source_shape_1 = self.frame_data["interactions"]["source_shape_1"]
        source_shape_2 = self.frame_data["interactions"]["source_shape_2"]
        source_shape_3 = self.frame_data["interactions"]["source_shape_3"]
        source_shape_4 = self.frame_data["interactions"]["source_shape_4"]
        target_shape_1 = self.frame_data["interactions"]["target_shape_1"]
        target_shape_2 = self.frame_data["interactions"]["target_shape_2"]
        target_shape_3 = self.frame_data["interactions"]["target_shape_3"]
        target_shape_4 = self.frame_data["interactions"]["target_shape_4"]
        source_dot_1 = self.frame_data["interactions"]["source_dot_1"]
        source_dot_2 = self.frame_data["interactions"]["source_dot_2"]
        source_dot_3 = self.frame_data["interactions"]["source_dot_3"]
        source_dot_4 = self.frame_data["interactions"]["source_dot_4"]
        target_dot_1 = self.frame_data["interactions"]["target_dot_1"]
        target_dot_2 = self.frame_data["interactions"]["target_dot_2"]
        target_dot_3 = self.frame_data["interactions"]["target_dot_3"]
        target_dot_4 = self.frame_data["interactions"]["target_dot_4"]

        source_shapes = {
            "source1": {"location": source_shape_1, "dot": source_dot_1},
            "source2": {"location": source_shape_2, "dot": source_dot_2},
            "source3": {"location": source_shape_3, "dot": source_dot_3},
            "source4": {"location": source_shape_4, "dot": source_dot_4},
        }
        target_shapes = {
            "target1": {"location": target_shape_1, "dot": target_dot_1},
            "target2": {"location": target_shape_2, "dot": target_dot_2},
            "target3": {"location": target_shape_3, "dot": target_dot_3},
            "target4": {"location": target_shape_4, "dot": target_dot_4},
        }

        # Main automation loop
        while self.should_continue:
            for source in source_shapes.values():
                for target in target_shapes.values():
                    if self.should_continue and self.pixel(source["location"][0], source["location"][1]) == self.pixel(
                        target["location"][0], target["location"][1]
                    ):
                        self.mouseDown(*source["dot"], duration=0.1)
                        self.moveTo(*target["dot"])
                        self.mouseUp()
                        self.sleep(0.1)
            if not self.sleep(2.5):
                break
