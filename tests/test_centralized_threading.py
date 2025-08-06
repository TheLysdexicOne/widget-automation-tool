"""
Test centralized threading approach in AutomationController.
"""

import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from automation.automation_controller import AutomationController


class TestCentralizedThreading:
    """Test the centralized threading implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.controller = AutomationController()

    def test_controller_has_threading_support(self):
        """Test that AutomationController has threading attributes."""
        assert hasattr(self.controller, "automation_threads")
        assert isinstance(self.controller.automation_threads, dict)

    def test_start_automation_creates_thread(self):
        """Test that start_automation creates a thread."""
        # Mock frame data for Iron Mine
        frame_data = {"id": "1.1", "name": "Iron Mine", "tier": 1, "programmed": 1}

        # Start automation
        success = self.controller.start_automation(frame_data)

        # Should succeed
        assert success is True

        # Should have created a thread
        assert "1.1" in self.controller.automation_threads
        thread = self.controller.automation_threads["1.1"]
        assert isinstance(thread, threading.Thread)
        assert thread.name == "Automation-1.1"

        # Clean up
        self.controller.stop_automation("1.1")

    def test_stop_automation_cleans_up_thread(self):
        """Test that stop_automation properly cleans up threads."""
        # Mock frame data for Iron Smelter
        frame_data = {"id": "1.2", "name": "Iron Smelter", "tier": 1, "programmed": 1}

        # Start automation
        self.controller.start_automation(frame_data)
        assert "1.2" in self.controller.automation_threads

        # Stop automation
        success = self.controller.stop_automation("1.2")
        assert success is True

        # Thread should be cleaned up
        assert "1.2" not in self.controller.automation_threads

    def test_multiple_automations_different_threads(self):
        """Test that multiple automations get different threads."""
        frame_data_1 = {"id": "1.1", "name": "Iron Mine", "tier": 1, "programmed": 1}

        frame_data_2 = {"id": "1.2", "name": "Iron Smelter", "tier": 1, "programmed": 1}

        # Start both automations
        success_1 = self.controller.start_automation(frame_data_1)
        success_2 = self.controller.start_automation(frame_data_2)

        assert success_1 is True
        assert success_2 is True

        # Should have different threads
        assert "1.1" in self.controller.automation_threads
        assert "1.2" in self.controller.automation_threads

        thread_1 = self.controller.automation_threads["1.1"]
        thread_2 = self.controller.automation_threads["1.2"]

        assert thread_1 != thread_2
        assert thread_1.name == "Automation-1.1"
        assert thread_2.name == "Automation-1.2"

        # Clean up
        self.controller.stop_automation("1.1")
        self.controller.stop_automation("1.2")

    def test_automator_no_threading_code_needed(self):
        """Test that individual automators don't need threading code."""
        # Import an automator to check it doesn't have threading
        from automation.frame_automators.tier_1.iron_smelter import IronSmelterAutomator

        frame_data = {"id": "1.2", "name": "Iron Smelter", "tier": 1}

        automator = IronSmelterAutomator(frame_data)

        # Should NOT have threading attributes
        assert not hasattr(automator, "automation_thread")
        assert not hasattr(automator, "_thread")

        # Should have basic automation methods
        assert hasattr(automator, "start_automation")
        assert hasattr(automator, "stop_automation")
        assert hasattr(automator, "_run_automation")

    def teardown_method(self):
        """Clean up after each test."""
        # Stop any running automations
        for frame_id in list(self.controller.automation_threads.keys()):
            self.controller.stop_automation(frame_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
