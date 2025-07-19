"""
Test script to debug console close behavior.
This will help us understand what happens when console is hidden.
"""

import logging
import time
from PyQt6.QtWidgets import QApplication
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.application import WidgetAutomationApp
from utility.logging_utils import ThrottledLogger


def test_console_close_behavior():
    """Test what happens when console is closed/hidden."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing console close behavior...")

    # Create QApplication (required for PyQt)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create the application instance
        widget_app = WidgetAutomationApp()

        # Show the console initially
        if widget_app.debug_console:
            logger.info("✅ Debug console created successfully")
            widget_app.debug_console.show()

            # Wait a moment for UI to stabilize
            time.sleep(2)

            # Check monitoring tab state before hiding
            monitoring_tab = widget_app.debug_console.monitoring_tab
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_before = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active before hide: {timer_active_before}"
                )

            # Hide the console (simulate close button)
            logger.info("🔄 Hiding console...")
            widget_app.debug_console.hide()

            # Wait a moment
            time.sleep(1)

            # Check monitoring tab state after hiding
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active after hide: {timer_active_after}"
                )

            # Show console again
            logger.info("🔄 Showing console again...")
            widget_app.debug_console.show()

            # Wait a moment
            time.sleep(1)

            # Check monitoring tab state after showing again
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after_show = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active after show: {timer_active_after_show}"
                )

            logger.info("✅ Test completed successfully")

        else:
            logger.error("❌ Failed to create debug console")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean shutdown
        try:
            if widget_app:
                widget_app.shutdown()
        except:
            pass

        app.quit()


if __name__ == "__main__":
    test_console_close_behavior()
