"""
Template Automator (Frame ID: X.X)
Template for creating new frame automators in WidgetInc.

Copy this template and customize for your specific frame:
1. Update the frame ID and name in docstring
2. Update class name (TemplateAutomator -> YourFrameAutomator)
3. Define your button names in button_list
4. Implement your automation logic in run_automation()
5. Optional: Override timing constants if needed
"""

from typing import Any, Dict
# import time  # Uncomment if using timeout logic

from ..base_automator import BaseAutomator


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

        Template patterns:
        - Simple clicking: Check if button is active, then click
        - Timed automation: Include timeout logic
        - State detection: Check for completion/failure states
        - Graceful stopping: Use safe_sleep for interrupt detection
        """

        # Example 1: Simple button clicking (like iron mine)
        # button_names = ["button1", "button2", "button3"]
        # buttons = [self.button_manager.get_button(name) for name in button_names]
        #
        # while self.is_running and not self.should_stop:
        #     for button in buttons:
        #         if self.engine.is_button_active(button):
        #             self.engine.click_button(button)  # Built-in safety validation
        #             self.safe_sleep(self.click_delay)
        #
        #     if not self.safe_sleep(self.cycle_delay):
        #         break

        # Example 2: Timed automation with timeout (like iron smelter)
        # start_time = time.time()
        # action_button = self.button_manager.get_button("action")
        #
        # while self.is_running and not self.should_stop:
        #     # Stop after configured time limit
        #     if time.time() - start_time > self.max_run_time:
        #         break
        #
        #     if self.engine.is_button_active(action_button):
        #         self.engine.click_button(action_button)  # Built-in safety validation
        #         self.safe_sleep(self.click_delay)
        #
        #     if not self.safe_sleep(self.cycle_delay):
        #         break

        # Example 3: State-based automation with failure detection
        # buttons = [self.button_manager.get_button(name) for name in ["btn1", "btn2"]]
        # failed_count = 0
        #
        # while self.is_running and not self.should_stop:
        #     success = False
        #
        #     for button in buttons:
        #         if self.engine.is_button_active(button):
        #             self.engine.click_button(button)  # Built-in safety validation
        #             self.safe_sleep(self.click_delay)
        #             success = True
        #
        #     if not success:
        #         failed_count += 1
        #         if failed_count >= 5:  # Adjust threshold as needed
        #             self.log_info("No available actions - stopping automation")
        #             break
        #     else:
        #         failed_count = 0  # Reset on success
        #
        #     if not self.safe_sleep(self.cycle_delay):
        #         break

        # TODO: Replace this placeholder with your actual automation logic
        self.log_info("Template automator running - implement your logic here!")

        # Placeholder loop - replace with your automation
        while self.is_running and not self.should_stop:
            # Your automation logic goes here

            # Always end with safe_sleep for proper interruption handling
            if not self.safe_sleep(1.0):  # 1 second delay for template
                break

        self.log_info("Template automation completed")


# Example subclass for quick customization:
class ExampleFrameAutomator(TemplateAutomator):
    """Example of how to customize the template for a specific frame."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Custom timing for this frame
        self.max_run_time = 300  # 5 minutes
        self.cycle_delay = 0.5  # Slower cycling

    def run_automation(self):
        """Example implementation for a hypothetical frame."""
        button_names = ["action1", "action2", "collect"]
        buttons = [self.button_manager.get_button(name) for name in button_names]

        while self.is_running and not self.should_stop:
            actions_performed = 0

            # Try each button
            for i, button in enumerate(buttons):
                if self.engine.button_active(button):
                    self.engine.click_button(button, button_names[i])  # Built-in safety
                    self.safe_sleep(self.click_delay)
                    actions_performed += 1

            # Log progress occasionally
            if actions_performed > 0:
                self.log_debug(f"Performed {actions_performed} actions this cycle")

            # Check for completion or pause between cycles
            if not self.safe_sleep(self.cycle_delay):
                break
