"""
Test Coordinator

Waits for application to be stable, calculates coordinates, and runs simple tests.
"""

import time
import subprocess
import sys
import os
import logging
from pathlib import Path


class TestCoordinator:
    """Coordinates test execution after application stabilizes."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def wait_for_application_ready(self, app_instance):
        """Wait for application to be fully ready and stable."""
        self.logger.info("Waiting for application to be ready...")

        # Wait for basic initialization
        max_wait = 10  # seconds
        waited = 0

        while waited < max_wait:
            if (
                app_instance.overlay_window
                and app_instance.overlay_window.isVisible()
                and app_instance.process_monitor
                and app_instance.process_monitor.current_target_hwnd
            ):

                self.logger.info("Application components ready")
                break

            time.sleep(0.5)
            waited += 0.5
        else:
            raise Exception("Application did not become ready in time")

        # Additional stabilization time
        self.logger.info("Allowing additional time for stabilization...")
        time.sleep(3.0)

        # Final check that overlay is still positioned correctly
        overlay_rect = app_instance.overlay_window.geometry()
        self.logger.info(
            f"Final overlay position: ({overlay_rect.x()}, {overlay_rect.y()})"
        )

        return True

    def get_overlay_click_coordinates(self, app_instance):
        """Get the exact coordinates to click on the overlay."""
        overlay_rect = app_instance.overlay_window.geometry()

        # Calculate center of the overlay (for the circle)
        center_x = overlay_rect.x() + 20  # Center of 40x40 overlay
        center_y = overlay_rect.y() + 20

        self.logger.info(f"Calculated click coordinates: ({center_x}, {center_y})")
        return center_x, center_y

    def run_overlay_expansion_test(self, app_instance):
        """Run the overlay expansion test."""
        self.logger.info("Starting overlay expansion test...")

        try:
            # Wait for application to be ready
            self.wait_for_application_ready(app_instance)

            # Get coordinates
            x, y = self.get_overlay_click_coordinates(app_instance)

            # Run the test directly in this process (no subprocess)
            self.logger.info(f"Running test with coordinates ({x}, {y})")

            # Import and run the test function directly
            from .simple_test import test_overlay_click

            test_overlay_click(x, y)

            # Give a moment for the action to complete
            time.sleep(1.0)

            # Check if the overlay expanded
            new_rect = app_instance.overlay_window.geometry()
            if new_rect.width() > 40 and app_instance.overlay_window.is_pinned:
                self.logger.info(
                    f"SUCCESS: Overlay expanded to {new_rect.width()}x{new_rect.height()}"
                )
                return 0
            else:
                self.logger.error(
                    f"FAIL: Overlay did not expand (width={new_rect.width()}, pinned={app_instance.overlay_window.is_pinned})"
                )
                return 1

        except Exception as e:
            self.logger.error(f"Test coordination failed: {e}")
            return 1
