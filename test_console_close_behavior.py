"""
Comprehensive test script with proper timing for console close behavior.
This will wait for full application initialization before testing.
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


def test_console_behavior_with_proper_timing():
    """Test console close behavior with proper timing for full initialization."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🎯 Testing console close behavior with proper timing...")

    # Create QApplication (required for PyQt)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create the application instance
        logger.info("📦 Creating application instance...")
        widget_app = WidgetAutomationApp()

        # Wait for full initialization
        logger.info("⏳ Waiting for application to fully initialize...")
        time.sleep(10)  # Give it 10 seconds to fully load

        if widget_app.debug_console:
            logger.info("✅ Debug console created successfully")

            # Show the console
            logger.info("🔄 Showing debug console...")
            widget_app.debug_console.show()

            # Wait for UI to fully render
            logger.info("⏳ Waiting for UI to fully render...")
            time.sleep(5)

            # Check initial state
            logger.info("📊 Checking initial console state...")
            is_visible_initial = widget_app.debug_console.isVisible()
            logger.info(f"Console visible (initial): {is_visible_initial}")

            # Switch to monitoring tab
            logger.info("🔄 Switching to monitoring tab...")
            widget_app.debug_console.tab_widget.setCurrentIndex(2)

            # Wait for tab to fully activate
            time.sleep(3)

            # Check monitoring state
            monitoring_tab = widget_app.debug_console.monitoring_tab
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                timer_active = monitoring_tab.update_timer.isActive()
                logger.info(f"📊 Monitoring timer active: {timer_active}")

                # Check if we have any data
                if hasattr(monitoring_tab, "current_coordinates"):
                    coords_count = (
                        len(monitoring_tab.current_coordinates)
                        if monitoring_tab.current_coordinates
                        else 0
                    )
                    logger.info(f"📍 Coordinate data entries: {coords_count}")

            # Now test different close methods
            logger.info("🧪 Testing different close methods...")

            # Method 1: Console tab close button
            logger.info("🔄 Testing console tab close button...")
            console_tab = widget_app.debug_console.console_tab
            if hasattr(console_tab, "_close_console"):
                console_tab._close_console()
                time.sleep(3)  # Wait for action to complete

                is_visible_after_tab_close = widget_app.debug_console.isVisible()
                logger.info(
                    f"Console visible after tab close: {is_visible_after_tab_close}"
                )

                if is_visible_after_tab_close:
                    logger.warning(
                        "❌ Console tab close button didn't hide the window!"
                    )
                else:
                    logger.info("✅ Console tab close button worked correctly")

            # Show console again for next test
            if not widget_app.debug_console.isVisible():
                logger.info("🔄 Showing console again for next test...")
                widget_app.debug_console.show()
                time.sleep(2)

            # Method 2: Window X button (closeEvent)
            logger.info("🔄 Testing window close event...")
            widget_app.debug_console.close()  # This should trigger closeEvent
            time.sleep(3)

            is_visible_after_close_event = widget_app.debug_console.isVisible()
            logger.info(
                f"Console visible after close event: {is_visible_after_close_event}"
            )

            if is_visible_after_close_event:
                logger.warning("❌ Window close event didn't hide the window!")
            else:
                logger.info("✅ Window close event worked correctly")

            # Show console again for next test
            if not widget_app.debug_console.isVisible():
                logger.info("🔄 Showing console again for final test...")
                widget_app.debug_console.show()
                time.sleep(2)

            # Method 3: System tray toggle
            logger.info("🔄 Testing system tray toggle...")
            if widget_app.system_tray and hasattr(
                widget_app.system_tray, "_on_toggle_debug_console"
            ):
                widget_app.system_tray._on_toggle_debug_console()
                time.sleep(3)

                is_visible_after_tray_toggle = widget_app.debug_console.isVisible()
                logger.info(
                    f"Console visible after system tray toggle: {is_visible_after_tray_toggle}"
                )

                if is_visible_after_tray_toggle:
                    logger.warning("❌ System tray toggle didn't hide the window!")
                else:
                    logger.info("✅ System tray toggle worked correctly")

            # Final check - ensure monitoring is still running
            logger.info("📊 Final check - monitoring status...")
            if monitoring_tab and hasattr(monitoring_tab, "update_timer"):
                final_timer_active = monitoring_tab.update_timer.isActive()
                logger.info(f"📊 Monitoring timer still active: {final_timer_active}")

                if final_timer_active:
                    logger.info(
                        "✅ Monitoring continues running after console operations!"
                    )
                else:
                    logger.warning("❌ Monitoring stopped during console operations!")

            # Check system tray functionality
            if widget_app.system_tray and hasattr(widget_app.system_tray, "tray_icon"):
                tray_visible = widget_app.system_tray.tray_icon.isVisible()
                logger.info(f"🔧 System tray icon visible: {tray_visible}")

            logger.info("✅ Complete test finished successfully!")

        else:
            logger.error("❌ Failed to create debug console")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Give a moment before shutdown
        logger.info("⏳ Waiting before shutdown...")
        time.sleep(2)

        # Clean shutdown
        try:
            if widget_app:
                widget_app.shutdown()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")

        app.quit()


if __name__ == "__main__":
    test_console_behavior_with_proper_timing()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🔧 Testing improved console close behavior...")

    # Create QApplication (required for PyQt)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create the application instance
        widget_app = WidgetAutomationApp()

        if widget_app.debug_console:
            logger.info("✅ Debug console created successfully")

            # Show the console
            widget_app.debug_console.show()
            time.sleep(1)

            # Check if console is visible
            is_visible_before = widget_app.debug_console.isVisible()
            logger.info(f"📺 Console visible before close: {is_visible_before}")

            # Test 1: Window X button (closeEvent)
            logger.info("🔄 Testing Window X button close (closeEvent)...")
            widget_app.debug_console.close()  # This should trigger closeEvent
            time.sleep(1)

            is_visible_after_close = widget_app.debug_console.isVisible()
            logger.info(f"📺 Console visible after close: {is_visible_after_close}")

            if not is_visible_after_close:
                logger.info("✅ Window X button correctly minimizes to tray!")
            else:
                logger.error("❌ Window X button failed - window still visible")

            # Test 2: Show again and test Console tab close button
            logger.info("🔄 Showing console again...")
            widget_app.debug_console.show()
            time.sleep(1)

            # Switch to console tab and simulate close button
            widget_app.debug_console.tab_widget.setCurrentIndex(0)  # Console tab
            time.sleep(0.5)

            logger.info("🔄 Testing Console tab close button...")
            console_tab = widget_app.debug_console.console_tab
            if hasattr(console_tab, "_close_console"):
                console_tab._close_console()  # Simulate close button click
                time.sleep(1)

                is_visible_after_tab_close = widget_app.debug_console.isVisible()
                logger.info(
                    f"📺 Console visible after tab close: {is_visible_after_tab_close}"
                )

                if not is_visible_after_tab_close:
                    logger.info(
                        "✅ Console tab close button correctly minimizes to tray!"
                    )
                else:
                    logger.error(
                        "❌ Console tab close button failed - window still visible"
                    )

            # Test 3: Show again and test system tray toggle
            logger.info("🔄 Testing system tray toggle...")
            widget_app.debug_console.show()
            time.sleep(1)

            if widget_app.system_tray:
                widget_app.system_tray._on_toggle_debug_console()
                time.sleep(1)

                is_visible_after_tray = widget_app.debug_console.isVisible()
                logger.info(
                    f"📺 Console visible after tray toggle: {is_visible_after_tray}"
                )

                if not is_visible_after_tray:
                    logger.info("✅ System tray toggle correctly minimizes to tray!")
                else:
                    logger.error("❌ System tray toggle failed - window still visible")

            # Test 4: Final show test
            logger.info("🔄 Final show test...")
            widget_app.debug_console.show()
            time.sleep(1)

            is_visible_final = widget_app.debug_console.isVisible()
            logger.info(f"📺 Console visible after final show: {is_visible_final}")

            if is_visible_final:
                logger.info("✅ Console can be shown again after being minimized!")
            else:
                logger.error("❌ Console cannot be shown - possible shell window issue")

            logger.info("✅ Console close behavior test completed!")

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
    test_console_behavior_with_proper_timing()
