"""
Standalone Test Runner

Completely separate from the main application. Waits for the application to be ready,
then runs tests without interfering with the Qt event loop.
"""

import time
import sys
import logging
import psutil
from pathlib import Path

# Add src to path so we can import from the application
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tests.simple_test import test_overlay_click


class StandaloneTestRunner:
    """Runs tests independently of the main application."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def wait_for_application_process(self, timeout=30):
        """Wait for the main application process to be running."""
        self.logger.info("Waiting for Widget Automation Tool to start...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Look for python process running main.py
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["name"] and "python" in proc.info["name"].lower():
                        cmdline = proc.info["cmdline"]
                        if cmdline and any("main.py" in cmd for cmd in cmdline):
                            self.logger.info(
                                f"Found application process: PID {proc.info['pid']}"
                            )
                            return proc.info["pid"]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            time.sleep(0.5)

        raise Exception("Application process not found within timeout")

    def wait_for_application_ready(self, timeout=30):
        """Wait for application to be fully initialized."""
        self.logger.info("Waiting for application to be ready...")

        # Wait for process
        self.wait_for_application_process(timeout)

        # Additional time for Qt application to initialize and find WidgetInc.exe
        self.logger.info("Waiting for application initialization...")
        time.sleep(8)  # Give plenty of time for overlay to position

        self.logger.info("Application should be ready")

    def get_overlay_coordinates_from_logs(self):
        """Parse the latest log file to get overlay coordinates."""
        log_file = Path(__file__).parent / "widget_automation.log"

        if not log_file.exists():
            raise Exception("Log file not found")

        # Read the log file and find the latest overlay position
        with open(log_file, "r") as f:
            lines = f.readlines()

        # Look for overlay position lines (most recent)
        overlay_pos = None
        for line in reversed(lines):
            if "Overlay positioned at" in line:
                # Extract coordinates from log line like: "Overlay positioned at (-488, 185)"
                try:
                    parts = line.split("Overlay positioned at (")[1].split(")")[0]
                    x, y = map(int, parts.split(", "))
                    overlay_pos = (x, y)
                    break
                except:
                    continue

        if overlay_pos is None:
            raise Exception("Could not find overlay position in logs")

        # Calculate center (overlay is 40x40, center at +20, +20)
        center_x = overlay_pos[0] + 20
        center_y = overlay_pos[1] + 20

        self.logger.info(
            f"Found overlay at {overlay_pos}, center at ({center_x}, {center_y})"
        )
        return center_x, center_y

    def run_overlay_expansion_test(self):
        """Run the overlay expansion test."""
        try:
            self.logger.info("Starting standalone overlay expansion test...")

            # Wait for application to be ready
            self.wait_for_application_ready()

            # Get coordinates from logs
            x, y = self.get_overlay_coordinates_from_logs()

            # Run the test
            self.logger.info(f"Running test with coordinates ({x}, {y})")
            test_overlay_click(x, y)

            self.logger.info("Test completed successfully")
            return 0

        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return 1


def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python standalone_test_runner.py <test_name>")
        print("Available tests: overlay_expansion")
        sys.exit(1)

    test_name = sys.argv[1]

    runner = StandaloneTestRunner()

    if test_name == "overlay_expansion":
        result = runner.run_overlay_expansion_test()
    else:
        print(f"Unknown test: {test_name}")
        result = 1

    sys.exit(result)


if __name__ == "__main__":
    main()
