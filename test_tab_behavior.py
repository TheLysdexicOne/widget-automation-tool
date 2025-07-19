"""
Enhanced test script to debug console close behavior and tab activation.
This will help us understand tab activation sequence and timer states.
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


def test_console_tabs_behavior():
    """Test what happens with tab activation and monitoring timers."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing console tab activation and monitoring behavior...")

    # Create QApplication (required for PyQt)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create the application instance
        widget_app = WidgetAutomationApp()

        # Show the console initially
        if widget_app.debug_console:
            logger.info("✅ Debug console created successfully")

            # Check which tab is currently active
            current_tab_index = widget_app.debug_console.tab_widget.currentIndex()
            tab_count = widget_app.debug_console.tab_widget.count()
            logger.info(
                f"📋 Total tabs: {tab_count}, Current active tab index: {current_tab_index}"
            )

            # Get tab names
            for i in range(tab_count):
                tab_name = widget_app.debug_console.tab_widget.tabText(i)
                logger.info(f"📋 Tab {i}: {tab_name}")

            # Check monitoring tab timer state
            monitoring_tab = widget_app.debug_console.monitoring_tab
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_initial = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (initial): {timer_active_initial}"
                )

            # Now show the console (this should trigger showEvent)
            widget_app.debug_console.show()
            logger.info("🔄 Console shown - showEvent should trigger...")

            # Wait a moment for UI to process
            time.sleep(1)

            # Check monitoring tab timer state after show
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after_show = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (after show): {timer_active_after_show}"
                )

            # Manually switch to monitoring tab
            logger.info("🔄 Switching to monitoring tab...")
            widget_app.debug_console.tab_widget.setCurrentIndex(
                2
            )  # Monitoring tab is index 2

            # Wait a moment
            time.sleep(1)

            # Check monitoring tab timer state after switching
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after_switch = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (after switch to monitoring): {timer_active_after_switch}"
                )

            # Now hide the console
            logger.info("🔄 Hiding console...")
            widget_app.debug_console.hide()

            # Wait a moment
            time.sleep(1)

            # Check monitoring tab timer state after hiding
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_after_hide = monitoring_tab.update_timer.isActive()
                logger.info(
                    f"📊 Monitoring timer active (after hide): {timer_active_after_hide}"
                )

            # Show console again
            logger.info("🔄 Showing console again...")
            widget_app.debug_console.show()

            # Wait a moment
            time.sleep(1)

            # Check which tab is active now and timer state
            current_tab_index_final = widget_app.debug_console.tab_widget.currentIndex()
            logger.info(
                f"📋 Current active tab index (after re-show): {current_tab_index_final}"
            )

            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active_final = monitoring_tab.update_timer.isActive()
                logger.info(f"📊 Monitoring timer active (final): {timer_active_final}")

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
    test_console_tabs_behavior()
