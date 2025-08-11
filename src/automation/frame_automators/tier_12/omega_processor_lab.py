"""
Omega Processor Lab Automator (Frame ID: 12.1)
Handles automation for the Omega Processor Lab frame in WidgetInc.
"""

from automation.base_automator import BaseAutomator


class OmegaProcessorLabAutomator(BaseAutomator):
    """Automation logic for Omega Processor Lab (Frame 12.1)."""

    def run_automation(self):
        target = self.frame_data["interactions"]["target"]
        drag_points = self.frame_data["interactions"]["drag_points"]

        drag_point_2 = drag_points["2"]

        processors = {
            name: dict(self.frame_data["interactions"][name], color_map=self.frame_data["colors"][f"{name}_color_map"])
            for name in ("circuit_board", "micro_processor", "nano_processor", "pico_processor")
        }
        background_color_map = self.frame_data["colors"]["background_color_map"]

        while self.should_continue:
            target_color = self.pixel(*target)
            self.logger.info(f"Target color: {target_color}")
            for name, data in processors.items():
                if target_color in data["color_map"]:
                    self.logger.info(f"Target matches {name} color map")
                    self.mouseDown(*data["lever"])
                    self.moveTo(data["catch"][0], data["catch"][1], duration=0.1)
                    self.mouseUp()
                    break
            else:
                self.fatal_error(f"Target color {target_color} does not match any processor color map")
                break

            while self.pixel(*data["catch"]) in background_color_map:
                self.sleep(0.05)

            self.mouseDown()
            self.moveTo(*drag_point_2, duration=1.5)
            self.sleep(1.5)
            self.mouseUp()

            if not self.sleep(2):
                break
