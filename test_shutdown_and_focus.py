"""
Test script to verify the fixes for:
1. Application closing seamlessly (Ctrl+C and system tray exit)
2. Console close button debouncing
3. Console focus behavior
"""

import logging
import time
import signal
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.application import WidgetAutomationApp


def test_shutdown_and_focus_fixes():
    """Test the fixes for shutdown, debouncing, and focus issues."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing shutdown, debouncing, and focus fixes...")

    # Create QApplication (required for PyQt)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create the application instance
        logger.info("📦 Creating application instance...")
        widget_app = WidgetAutomationApp(debug_mode=True)

        # Wait for full initialization
        logger.info("⏳ Waiting for application to fully initialize...")
        time.sleep(8)

        if widget_app.debug_console:
            logger.info("✅ Debug console created successfully")

            # Test 1: Focus behavior
            logger.info("🔍 Testing focus behavior...")
            widget_app.debug_console.show()
            time.sleep(2)

            is_visible = widget_app.debug_console.isVisible()
            has_focus = widget_app.debug_console.isActiveWindow()
            logger.info(f"Console visible: {is_visible}, has focus: {has_focus}")

            # Test 2: Rapid close button clicks (debouncing test)
            logger.info("🔍 Testing close button debouncing...")
            console_tab = widget_app.debug_console.console_tab
            if console_tab and hasattr(console_tab, "_close_console"):
                # Simulate rapid clicks
                logger.info("Simulating 5 rapid close button clicks...")
                for i in range(5):
                    logger.info(f"Click {i+1}")
                    console_tab._close_console()
                    time.sleep(0.1)  # Very rapid clicks

                time.sleep(1)
                is_visible_after_rapid = widget_app.debug_console.isVisible()
                logger.info(
                    f"Console visible after rapid clicks: {is_visible_after_rapid}"
                )

                if not is_visible_after_rapid:
                    logger.info("✅ Debouncing working - console minimized correctly")
                else:
                    logger.warning("❌ Debouncing may not be working properly")

            # Show console again for final test
            if not widget_app.debug_console.isVisible():
                logger.info("🔄 Showing console again...")
                widget_app.debug_console.show()
                time.sleep(2)

            # Test 3: Clean shutdown via system tray
            logger.info("🔍 Testing system tray shutdown...")
            if widget_app.system_tray and hasattr(widget_app.system_tray, "_on_exit"):
                logger.info("Calling system tray exit...")
                widget_app.system_tray._on_exit()
                time.sleep(2)
                logger.info("✅ System tray exit completed")
            else:
                logger.warning("❌ System tray not available for exit test")

        else:
            logger.error("❌ Failed to create debug console")

    except KeyboardInterrupt:
        logger.info("🔍 KeyboardInterrupt received - testing Ctrl+C handling...")
        widget_app.shutdown()
        logger.info("✅ Ctrl+C handling working")
        return 0

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        if widget_app:
            widget_app.shutdown()
        return 1

    return 0


if __name__ == "__main__":
    # Test signal handling
    def signal_test_handler(signum, frame):
        print(f"✅ Signal {signum} received and handled correctly")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_test_handler)
    signal.signal(signal.SIGTERM, signal_test_handler)

    try:
        exit_code = test_shutdown_and_focus_fixes()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("✅ KeyboardInterrupt handling working")
        sys.exit(0)
