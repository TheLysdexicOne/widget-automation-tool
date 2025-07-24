#!/usr/bin/env python3
"""
Simple real environment test that actually reproduces the original bug.
"""

import subprocess
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_original_bug_reproduction():
    """Reproduce the original bug: overlay not exiting when system tray exit is triggered."""

    project_root = Path(__file__).parent.parent

    logger.info("🧪 TESTING: Original bug reproduction")
    logger.info("This should demonstrate that the overlay doesn't exit properly")

    # Start overlay only mode
    batch_file = project_root / "start.bat"
    logger.info(f"Starting: {batch_file}")

    proc = subprocess.Popen([str(batch_file)], cwd=str(project_root))

    logger.info(f"Process PID: {proc.pid}")

    # Wait for startup
    time.sleep(3)

    logger.info("✅ Application should be running now")
    logger.info("🎯 Please manually:")
    logger.info("   1. Verify the overlay is visible")
    logger.info("   2. Right-click the system tray icon")
    logger.info("   3. Click 'Exit'")
    logger.info("   4. Check if overlay actually disappears")

    # Wait for user to test manually
    input("Press Enter after testing the system tray exit...")

    # Check if process is still running
    if proc.poll() is None:
        logger.error("❌ BUG CONFIRMED: Process is still running after system tray exit!")
        logger.info("This means the overlay did not respond to the exit command.")

        # Force kill
        proc.terminate()
        proc.wait()
        logger.info("Process terminated manually")
        return False
    else:
        logger.info("✅ Process exited cleanly")
        return True


if __name__ == "__main__":
    test_original_bug_reproduction()
