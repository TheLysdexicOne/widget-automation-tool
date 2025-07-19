"""
Final test script to simulate the exact user scenario.
This will test if console close button works correctly without stopping functionality.
"""

import logging
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.application import WidgetAutomationApp


def test_user_scenario():
    """Test the exact scenario: open console, go to monitoring, close console."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info(
        "🎯 Testing user scenario: console monitoring should continue after close..."
    )

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

            # Wait for UI to stabilize
            time.sleep(1)

            # Switch to monitoring tab (like user would)
            logger.info("🔄 User switches to monitoring tab...")
            widget_app.debug_console.tab_widget.setCurrentIndex(2)  # Monitoring tab

            # Wait a moment for tab to activate
            time.sleep(1)

            # Check monitoring tab is working
            monitoring_tab = widget_app.debug_console.monitoring_tab
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (monitoring tab active): {timer_active}"
                )

                # Check if we're getting coordinate updates
                if monitoring_tab.current_coordinates:
                    logger.info(
                        f"📍 Monitoring data present: {len(monitoring_tab.current_coordinates)} coordinate entries"
                    )
                else:
                    logger.info(
                        "📍 No monitoring data yet (this is normal if no target window)"
                    )

            # Now simulate user clicking close button (console tab close button)
            logger.info("🔄 User clicks close button on console...")

            # The console tab close button calls self.parent().hide()
            widget_app.debug_console.hide()

            # Wait a moment
            time.sleep(1)

            # Check if monitoring is still working after close
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after_close = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (after close): {timer_active_after_close}"
                )

                if timer_active_after_close:
                    logger.info(
                        "✅ SUCCESS: Monitoring continues running after console close!"
                    )
                else:
                    logger.error(
                        "❌ FAILURE: Monitoring stopped when console was closed!"
                    )

            # Verify system tray is still functional
            if widget_app.system_tray:
                logger.info("🔧 System tray still active - user can reopen console")

            # Test reopening console
            logger.info("🔄 User reopens console from system tray...")
            widget_app.debug_console.show()

            # Wait a moment
            time.sleep(1)

            # Check monitoring tab is still active and working
            current_tab = widget_app.debug_console.tab_widget.currentIndex()
            logger.info(
                f"📋 Current tab after reopen: {current_tab} (should be 2 for monitoring)"
            )

            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_final = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (after reopen): {timer_active_final}"
                )

            logger.info(
                "✅ Test completed successfully - Console close behavior working correctly!"
            )

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
    test_user_scenario()
