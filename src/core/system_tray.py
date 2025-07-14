"""
System Tray Manager

Manages the system tray icon and context menu.
"""

import logging
from pathlib import Path

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon, QAction


class SystemTrayManager(QObject):
    """Manages the system tray icon and menu."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)

        # Create system tray icon
        self.tray_icon = None
        self.tray_menu = None

        self._setup_tray_icon()

    def _setup_tray_icon(self):
        """Setup the system tray icon and menu."""
        try:
            # Check if system tray is available
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.error("System tray is not available on this system")
                return

            # Create the tray icon
            self.tray_icon = QSystemTrayIcon(self)

            # Set icon (use a default icon for now, can be customized later)
            icon = self._create_default_icon()
            self.tray_icon.setIcon(icon)

            # Create context menu
            self._create_context_menu()

            # Set tooltip
            self.tray_icon.setToolTip("Widget Automation Tool")

            # Connect signals
            self.tray_icon.activated.connect(self._on_tray_icon_activated)

            # Show the tray icon
            self.tray_icon.show()

            self.logger.info("System tray icon created successfully")

        except Exception as e:
            self.logger.error(f"Failed to setup system tray icon: {e}")

    def _create_default_icon(self):
        """Create a default icon for the system tray."""
        # For now, use a built-in icon. Later we can use custom assets
        from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor

        # Create a simple colored circle as default icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(70, 130, 180)))  # Steel blue color
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()

        return QIcon(pixmap)

    def _create_context_menu(self):
        """Create the context menu for the system tray."""
        self.tray_menu = QMenu()

        # Show Debug Console action
        show_console_action = QAction("Show Debug Console", self)
        show_console_action.triggered.connect(self._on_show_debug_console)
        self.tray_menu.addAction(show_console_action)

        # Separator
        self.tray_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._on_exit)
        self.tray_menu.addAction(exit_action)

        # Set the menu to the tray icon
        self.tray_icon.setContextMenu(self.tray_menu)

    def _on_tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.logger.debug("Tray icon double-clicked")
            self._on_show_debug_console()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.logger.debug("Tray icon middle-clicked")

    def _on_show_debug_console(self):
        """Handle show debug console action."""
        self.logger.debug("Show debug console requested from tray menu")
        self.app.show_debug_console()

    def _on_exit(self):
        """Handle exit action."""
        self.logger.info("Exit requested from tray menu")
        self.app.shutdown()

    def update_icon_state(self, state):
        """Update the tray icon based on application state."""
        try:
            # TODO: Update icon color/appearance based on state
            # For now just update the tooltip
            state_text = state.value.title() if hasattr(state, "value") else str(state)
            tooltip = f"Widget Automation Tool - {state_text}"
            self.tray_icon.setToolTip(tooltip)

        except Exception as e:
            self.logger.error(f"Failed to update tray icon state: {e}")

    def cleanup(self):
        """Clean up the system tray icon."""
        try:
            if self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon = None

            self.logger.debug("System tray cleaned up")

        except Exception as e:
            self.logger.error(f"Error during tray cleanup: {e}")
