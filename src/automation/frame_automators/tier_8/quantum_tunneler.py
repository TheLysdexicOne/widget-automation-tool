"""
Quantum Tunneler Automator (Frame ID: 8.4)
Handles automation for the Quantum Tunneler frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class QuantumTunnelerAutomator(BaseAutomator):
    """Automation logic for Quantum Tunneler (Frame 8.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

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
            if time.time() - start_time > self.max_run_time:
                break

            for source in source_shapes.values():
                for target in target_shapes.values():
                    if self.should_continue and pyautogui.pixel(
                        source["location"][0], source["location"][1]
                    ) == pyautogui.pixel(target["location"][0], target["location"][1]):
                        pyautogui.mouseDown(*source["dot"], duration=0.1)
                        pyautogui.moveTo(*target["dot"])
                        pyautogui.mouseUp()
                        self.sleep(0.1)
            if not self.sleep(2.5):
                break


"""
0.590741, 0.362500, 0.622222, 0.409722 = (0.6064815, 0.386111)
0.590741, 0.487500, 0.622222, 0.534722 = (0.6064815, 0.511111)
0.590741, 0.612500, 0.622222, 0.659722 = (0.6064815, 0.636111)
0.590741, 0.737500, 0.622222, 0.784722 = (0.6064815, 0.761111)
0.840741, 0.362500, 0.872222, 0.409722 = (0.8564815, 0.386111)
0.840741, 0.487500, 0.872222, 0.534722 = (0.8564815, 0.511111)
0.840741, 0.612500, 0.872222, 0.659722 = (0.8564815, 0.636111)
0.840741, 0.737500, 0.872222, 0.784722 = (0.8564815, 0.761111)


0.640741, 0.375000, 0.656481, 0.398611 = (0.648611,  0.3868055)
0.640741, 0.500000, 0.656481, 0.523611 = (0.648611,  0.5118055)
0.640741, 0.625000, 0.656481, 0.648611 = (0.648611,  0.6368055)
0.640741, 0.750000, 0.656481, 0.773611 = (0.648611,  0.7618055)
0.807407, 0.375000, 0.823148, 0.398611 = (0.8152775, 0.3868055)
0.807407, 0.500000, 0.823148, 0.523611 = (0.8152775, 0.5118055)
0.807407, 0.625000, 0.823148, 0.648611 = (0.8152775, 0.6368055)
0.807407, 0.750000, 0.823148, 0.773611 = (0.8152775, 0.7618055)
"""
