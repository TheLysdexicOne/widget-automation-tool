"""
Template Automator (Frame ID: X.X)
Template for creating new frame automators in WidgetInc.

Copy this template and customize for your specific frame:
1. Update the frame ID and name in docstring
2. Update class name (TemplateAutomator -> YourFrameAutomator)
3. Define your button names used in run_automation()
4. Implement your automation logic in run_automation()
5. Optional: Override timing constants if needed
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class TemplateAutomator(BaseAutomator):
    """Template automation logic - replace with your frame name."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

        # Optional: Override timing constants for this specific frame
        # self.max_run_time = 600  # 10 minutes instead of default 5
        # self.click_delay = 0.1   # Slower clicking if needed
        # self.cycle_delay = 0.2   # Longer delays between cycles
        # self.factory_delay = 1.0 # Even longer for complex operations

    def run_automation(self):
        """
        Main automation logic - customize this for your frame.

        Common patterns from existing automators:
        - Button clicking: Use self.create_button() for button engines
        - State checking: button.active() or button.inactive()
        - Timing: Include timeout logic with start_time and self.max_run_time
        - Storage full detection: Check button states after actions
        - Graceful stopping: Use self.sleep() for interrupt detection
        - Loop condition: Use self.should_continue instead of self.is_running and not self.should_stop
        """
        start_time = time.time()

        # Pattern 1: Simple button clicking (Iron Mine style)
        # button_names = ["miner1", "miner2", "miner3", "miner4"]
        # buttons = [self.create_button(name) for name in button_names]
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     failed = 0
        #     for button in buttons:
        #         if button.active():
        #             button.click()
        #             self.sleep(0.1)
        #             if button.active():  # Still active after click = problem
        #                 failed += 1
        #         else:
        #             failed += 1
        #
        #     # Storage full detection
        #     if failed >= len(buttons):
        #         self.log_storage_error()
        #         break
        #
        #     # Wait for buttons to become inactive, then cycle
        #     while self.should_continue and buttons[0].inactive():
        #         if not self.sleep(0.2):
        #             return

        # Pattern 2: Load-then-process automation (Iron Smelter style)
        # load = self.create_button("load")
        # smelt = self.create_button("smelt")
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     if load.active():
        #         load.click()
        #         self.sleep(0.05)
        #         if load.active():  # Load still active
        #             smelt.click()
        #             self.sleep(0.1)
        #             if smelt.active():  # Storage full detection
        #                 self.log_storage_error()
        #                 break
        #     else:
        #         self.log_frame_error()
        #         break
        #
        #     if not self.sleep(0.1):
        #         break

        # Pattern 3: Continuous action button (Widget Factory style)
        # create = self.create_button("create")
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     if not create.inactive():  # Button is active
        #         create.click()
        #         # Optional: Add progress monitoring here
        #
        #     if not self.sleep(0.01):  # Very fast clicking
        #         break

        # Pattern 4: Hold-click automation (Gyroscope Fabricator style)
        # create = self.create_button("create")
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     if create.active():
        #         create.hold_click(0.45)  # Hold for specific duration

        # Pattern 5: Waiting for state changes (Widget Spinner style)
        # from utility.window_utils import grid_to_screen_coordinates
        #
        # spin = self.create_button("spin")
        # wait_point = (87, 33)  # Grid coordinates
        # scan_point = grid_to_screen_coordinates(wait_point[0], wait_point[1])
        # scan_color = (57, 63, 70)
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     # Wait for specific pixel color (spinning animation complete)
        #     if not self.scan.pixel_watcher(scan_point, scan_color, timeout=30.0, check_interval=0.004):
        #         self.log_timeout_error()
        #         break
        #
        #     spin.click()
        #     if not self.sleep(0.25):
        #         break

        # Pattern 6: Action with wait cycles (Sand Pit style)
        # excavate = self.create_button("excavate")
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     if excavate.active():
        #         excavate.click()
        #         self.sleep(2)  # Action takes time
        #         if not excavate.inactive():  # Should be inactive after completion
        #             self.log_storage_error()
        #             break
        #     else:
        #         self.log_frame_error()
        #         break
        #
        #     # Wait for action to complete before next cycle
        #     while self.should_continue and not excavate.active():
        #         if not self.sleep(0.2):
        #             return

        # Pattern 7: Mouse operations with nested loops (Oil Power Plant style)
        # import pyautogui
        # from utility.window_utils import grid_to_screen_coordinates
        #
        # pbar_color = (0, 149, 28)
        # handle = self.frame_data["interactions"]["handle"]
        # pbar = self.frame_data["interactions"]["progress_bar"]
        # handle_x, handle_y = grid_to_screen_coordinates(handle[0], handle[1])
        # pbar_x, pbar_y = grid_to_screen_coordinates(pbar[0], pbar[1])
        #
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     pyautogui.mouseDown(handle_x, handle_y)
        #     pyautogui.moveTo(pbar_x, pbar_y, duration=0)
        #     while self.should_continue:
        #         monitor_start = time.time()
        #         progress_detected = False
        #
        #         while time.time() - monitor_start < 5.0:
        #             if not self.should_continue:
        #                 pyautogui.mouseUp()
        #                 return
        #             if pyautogui.pixelMatchesColor(pbar_x, pbar_y, pbar_color):
        #                 progress_detected = True
        #                 break
        #             time.sleep(0.1)
        #
        #         if not progress_detected:
        #             pyautogui.mouseUp()
        #             self.log_storage_error()
        #             break
        #
        #         time.sleep(5)
        #
        #     pyautogui.mouseUp()

        # TODO: Replace this placeholder with your actual automation logic
        self.log_info("Template automator running - implement your logic here!")

        # Placeholder loop - replace with your automation pattern
        while self.should_continue:
            # Check timeout (uncomment and modify as needed)
            if time.time() - start_time > self.max_run_time:
                break

            # Your automation logic goes here

            # Always end with self.sleep() for proper interruption handling
            if not self.sleep(1.0):  # 1 second delay for template
                break

        self.log_info("Template automation completed")


# Example subclass for quick customization:
class ExampleFrameAutomator(TemplateAutomator):
    """Example of how to customize the template for a specific frame."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Custom timing for this frame
        self.max_run_time = 300  # 5 minutes

    def run_automation(self):
        """Example implementation using Iron Mine pattern."""
        start_time = time.time()

        # Create button engines using actual method names
        button_names = ["action1", "action2", "collect"]
        buttons = [self.create_button(name) for name in button_names]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            failed = 0
            for i, button in enumerate(buttons):
                if button.active():
                    button.click()
                    self.sleep(self.click_delay)
                    if button.active():  # Still active = problem
                        failed += 1
                else:
                    failed += 1

            # Storage full detection
            if failed >= len(buttons):
                self.log_storage_error()
                break

            # Log progress occasionally
            self.log_debug(f"Automation cycle completed, {failed} failed actions")

            # Cycle delay
            if not self.sleep(self.cycle_delay):
                break
