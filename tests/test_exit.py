#!/usr/bin/env python3
"""
Test script to verify proper exit behavior
"""

import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from overlay.main_overlay import MainOverlayWidget


def main():
    app = QApplication(sys.argv)

    # Simple icon
    icon = QIcon()
    app.setWindowIcon(icon)

    # Create overlay
    overlay = MainOverlayWidget(debug_mode=True)
    overlay.show()

    # Simple system tray
    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()

    exit_action = QAction("Exit", menu)
    menu.addAction(exit_action)
    tray.setContextMenu(menu)
    tray.show()

    def on_exit():
        print("Exit action triggered")
        overlay.close()
        app.quit()

    exit_action.triggered.connect(on_exit)

    # Auto exit after 3 seconds for testing
    def auto_exit():
        print("Auto exit after 3 seconds")
        on_exit()

    QTimer.singleShot(3000, auto_exit)

    print("Starting test app, will auto-exit in 3 seconds")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
