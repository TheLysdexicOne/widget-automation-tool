"""
Nuclear Power Plant Automator (Frame ID: 7.3)
Handles automation for the Nuclear Power Plant frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class NuclearPowerPlantAutomator(BaseAutomator):
    """Automation logic for Nuclear Power Plant (Frame 7.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start = self.create_button("start")

        indicator = self.frame_data["colors"]["indicator"]

        x1 = self.frame_data["interactions"]["x1"][0]
        x2 = self.frame_data["interactions"]["x2"][0]
        y1 = self.frame_data["interactions"]["y1"][1]
        y2 = self.frame_data["interactions"]["y2"][1]
        y3 = self.frame_data["interactions"]["y3"][1]
        slider_1 = self.frame_data["interactions"]["slider_1"]
        slider_2 = self.frame_data["interactions"]["slider_2"]
        slider_3 = self.frame_data["interactions"]["slider_3"]

        pbar = self.frame_data["interactions"]["pbar"]
        pbar_color = self.frame_data["colors"]["pbar_color"]

        y_values = [y1, y2, y3]

        x_range = range(int(x1), int(x2) + 1, 5)
        sliders = {"slider_1": slider_1, "slider_2": slider_2, "slider_3": slider_3}
        # Main automation loop
        while self.should_continue:
            for i, y in enumerate(y_values):
                slider = sliders[f"slider_{i + 1}"]
                for x in x_range:
                    color = self.pixel(x, int(y))
                    if color == indicator:
                        self.mouseDown(slider[0], slider[1])
                        self.moveTo(x + 5, int(y), duration=0.1)
                        self.mouseUp()
                        sliders[f"slider_{i + 1}"] = (x, slider[1])
                        self.sleep(0.1)
                        break
            start.click()
            self.sleep(1)
            while self.should_continue:
                if self.pixel(pbar[0], pbar[1]) == pbar_color:
                    self.sleep(0.1)
                else:
                    break

            if not self.sleep(0.5):
                break
