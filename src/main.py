#!/usr/bin/env python3
"""
Widget Automation Tool - Main Entry Point
"""

import sys
import argparse
import logging
import signal
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, QSize
from overlay.main_overlay import MainOverlay
from gui.main_window import MainWindow


def setup_logging(debug=False):
    """Setup logging configuration."""
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Simple log setup - one file, rotate when large
    log_file = logs_dir / "widget_automation.log"

    # Basic cleanup - keep log files under 10MB
    if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
        backup_file = logs_dir / "widget_automation.log.bak"
        if backup_file.exists():
            backup_file.unlink()
        log_file.rename(backup_file)

    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    handlers = []
    handlers.append(logging.FileHandler(log_file, mode="a"))
    if debug:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers,
    )

    return logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Widget Automation Tool", prog="widget-automation-tool")
    parser.add_argument("--gui", action="store_true", help="Show GUI window in addition to overlay")
    parser.add_argument("--debug", action="store_true", help="Show GUI + overlay with debug console logging")
    parser.add_argument("--target", default="WidgetInc.exe", help="Target process name (default: WidgetInc.exe)")
    parser.add_argument("--version", action="version", version="Widget Automation Tool 2.0.0")
    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = setup_logging(args.debug)
    logger.info("Starting Widget Automation Tool...")
    if args.debug:
        logger.info(f"Debug mode enabled, target: {getattr(args, 'target', None)}")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load and apply QSS stylesheet before showing any widgets
    qss_path = Path(__file__).parent / "config" / "styles" / "main.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Set application and tray icon (use multiple sizes for better display)
    icons_dir = Path(__file__).parent.parent / "assets" / "icons"
    icon96 = icons_dir / "development-96.png"
    icon64 = icons_dir / "development-64.png"

    # Create a multi-size icon for better taskbar display
    app_icon = QIcon()
    if icon96.exists():
        app_icon.addFile(str(icon96), QSize(96, 96))
        logger.debug(f"Added 96x96 icon: {icon96}")
    if icon64.exists():
        app_icon.addFile(str(icon64), QSize(64, 64))
        logger.debug(f"Added 64x64 icon: {icon64}")

    # Add scaled versions for common taskbar sizes
    if icon64.exists():
        app_icon.addFile(str(icon64), QSize(32, 32))
        app_icon.addFile(str(icon64), QSize(24, 24))
        app_icon.addFile(str(icon64), QSize(16, 16))
        logger.debug("Added scaled icon sizes for taskbar")

    if app_icon.isNull():
        app_icon = app.windowIcon()
        logger.warning("No custom icons found, using default")

    app.setWindowIcon(app_icon)

    # Check system tray availability before proceeding
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.error("System tray is not available on this system")
        return 1

    # Instantiate windows but do not show yet
    overlay = MainOverlay(target_process=getattr(args, "target", "WidgetInc.exe"), debug_mode=args.debug)
    gui = MainWindow()

    # Set taskbar icons properly for each window
    overlay.setWindowIcon(app_icon)
    gui.setWindowIcon(app_icon)

    windows = {"overlay": overlay, "gui": gui}
    current_window = None

    # System tray setup
    system_tray = QSystemTrayIcon(app_icon, app)
    system_tray.setToolTip("Widget Automation Tool")

    # Verify icon is set before creating menu
    if app_icon.isNull():
        logger.warning("App icon is null, system tray may not display properly")
    else:
        logger.debug("System tray icon set successfully")

    tray_menu = QMenu()
    action_gui = QAction("GUI", tray_menu)
    action_overlay = QAction("Overlay", tray_menu)
    action_exit = QAction("Exit", tray_menu)
    tray_menu.addAction(action_gui)
    tray_menu.addAction(action_overlay)
    tray_menu.addSeparator()
    tray_menu.addAction(action_exit)
    system_tray.setContextMenu(tray_menu)

    # Ensure tray icon is visible
    system_tray.setVisible(True)
    system_tray.show()
    logger.info("System tray icon initialized and shown")

    # Force system tray to appear with a small delay (Windows quirk)
    def ensure_tray_visible():
        if not system_tray.isVisible():
            logger.warning("System tray not visible, forcing visibility...")
            system_tray.hide()
            system_tray.show()
        else:
            logger.debug("System tray confirmed visible")

    QTimer.singleShot(500, ensure_tray_visible)  # Check after 500ms

    def show_window(which):
        nonlocal current_window
        win = windows[which]
        if win.isVisible():
            # If window is already visible, just bring it to front
            win.raise_()
            win.activateWindow()
        else:
            # Show the window without hiding others
            win.show()
            win.raise_()
            win.activateWindow()
        current_window = win

    def toggle_window(which):
        """Toggle a window's visibility without affecting other windows."""
        win = windows[which]
        if win.isVisible():
            win.hide()
        else:
            win.show()
            win.raise_()
            win.activateWindow()

    def on_gui():
        show_window("gui")

    def on_overlay():
        show_window("overlay")

    def on_exit():
        logger.info("Exiting via system tray menu.")
        logger.debug("System tray hide...")
        system_tray.hide()

        logger.debug("Closing windows explicitly...")
        # Explicitly close and cleanup all windows
        for name, win in windows.items():
            if win:
                logger.debug(f"Checking {name} window: hidden={win.isHidden()}, visible={win.isVisible()}")
                if not win.isHidden():
                    logger.debug(f"Closing {name} window")
                    # For overlay, call cleanup explicitly since aboutToQuit signal may not work
                    if name == "overlay" and hasattr(win, "_cleanup_and_close"):
                        logger.debug("Calling overlay cleanup explicitly")
                        win._cleanup_and_close()
                    else:
                        win.close()
                else:
                    logger.debug(f"{name} window already hidden")

        logger.debug("Calling app.quit()...")
        # Force application quit
        app.quit()
        logger.debug("app.quit() called")

        # Force exit after a short delay if app.quit() doesn't work
        def force_exit():
            logger.warning("Forcing application exit")
            import os

            os._exit(0)

        QTimer.singleShot(2000, force_exit)  # Force exit after 2 seconds

    # Connect the GUI's exit action to the proper exit function
    if hasattr(gui, "_exit_application"):
        # Replace the GUI's exit method with the proper one
        gui._exit_application = on_exit

    action_gui.triggered.connect(on_gui)
    action_overlay.triggered.connect(on_overlay)
    action_exit.triggered.connect(on_exit)

    # Add system tray activation (double-click to show overlay)
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            show_window("overlay")
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - could show a window or do nothing
            pass

    system_tray.activated.connect(on_tray_activated)

    # Minimize to tray on close (X button)
    def minimize_to_tray(event=None):
        if current_window:
            current_window.hide()
        system_tray.showMessage(
            "Widget Automation Tool",
            "Application minimized to system tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )
        if event:
            event.ignore()

    # Patch closeEvent only for overlay (not GUI - GUI has its own close handling)
    def _closeEvent(self, event):
        minimize_to_tray(event)

    # Only apply minimize-to-tray behavior to the overlay
    overlay.closeEvent = _closeEvent.__get__(overlay, type(overlay))

    # GUI window keeps its own closeEvent behavior (minimize to tray vs exit)
    # The GUI's closeEvent is handled in MainWindow class

    # Minimize to start bar on minimize
    for win in windows.values():
        orig_change = getattr(win, "changeEvent", None)

        def _changeEvent(self, event):
            from PyQt6.QtCore import QEvent

            if event.type() == QEvent.Type.WindowStateChange:
                if self.isMinimized():
                    # Minimize to start bar (default behavior)
                    pass
            if orig_change:
                orig_change(event)

        win.changeEvent = _changeEvent.__get__(win, type(win))

    # Show windows on startup based on arguments
    # Always show overlay
    show_window("overlay")

    # Show GUI if --gui flag is used (debug mode is overlay + debug logging only)
    if getattr(args, "gui", False):
        show_window("gui")

    # Clean shutdown on signal
    def shutdown_handler(signum, frame):
        logger.info(f"Signal {signum} received, shutting down...")
        system_tray.hide()

        # Explicitly close and cleanup all windows
        for name, win in windows.items():
            if win and not win.isHidden():
                logger.debug(f"Closing {name} window via signal")
                win.close()

        app.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        return app.exec()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, shutting down...")
        system_tray.hide()
        for name, win in windows.items():
            if win:
                logger.debug(f"Closing {name} window via keyboard interrupt")
                win.close()
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        system_tray.hide()
        for name, win in windows.items():
            if win:
                logger.debug(f"Closing {name} window via exception")
                win.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
