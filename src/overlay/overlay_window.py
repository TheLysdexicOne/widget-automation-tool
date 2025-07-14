"""
Overlay Window

Window overlay that attaches to the target application window.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen

import pygetwindow as gw


class OverlayWindow(QWidget):
    """Overlay window that attaches to the target application."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)

        # Overlay configuration
        self.circle_diameter = 24
        self.box_size = 32
        self.offset_x = 0
        self.offset_y = 32

        # State colors
        self.state_colors = {
            "active": QColor("#00FF00"),  # Green
            "waiting": QColor("#FFFF00"),  # Yellow
            "inactive": QColor("#808080"),  # Gray
            "error": QColor("#FF0000"),  # Red
        }
        self.current_color = self.state_colors["inactive"]

        # Target window info
        self.target_hwnd = None
        self.target_window = None

        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.start(100)  # Update every 100ms

        # Setup window
        self._setup_window()

    def _setup_window(self):
        """Setup the overlay window properties."""
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )

        # Set window properties
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Set size
        self.setFixedSize(self.box_size, self.box_size)

        # Initially hidden
        self.hide()

        self.logger.debug("Overlay window setup complete")

    def attach_to_window(self, hwnd):
        """Attach overlay to a target window."""
        try:
            self.target_hwnd = hwnd

            # Find the window object
            self.target_window = None
            for window in gw.getAllWindows():
                if hasattr(window, "_hWnd") and window._hWnd == hwnd:
                    self.target_window = window
                    break

            if self.target_window:
                self.logger.info(
                    f"Overlay attached to window: {self.target_window.title}"
                )
                self._update_position()
                self.show()
            else:
                self.logger.warning(f"Could not find window object for hwnd: {hwnd}")

        except Exception as e:
            self.logger.error(f"Failed to attach overlay to window: {e}")

    def detach_from_window(self):
        """Detach overlay from target window."""
        self.target_hwnd = None
        self.target_window = None
        self.hide()
        self.logger.debug("Overlay detached from window")

    def _update_position(self):
        """Update overlay position based on target window."""
        if not self.target_window or not self.isVisible():
            return

        try:
            # Get target window position and size
            target_rect = QRect(
                self.target_window.left,
                self.target_window.top,
                self.target_window.width,
                self.target_window.height,
            )

            # Calculate overlay position (top-right corner + offset)
            overlay_x = target_rect.right() - self.box_size + self.offset_x
            overlay_y = target_rect.top() + self.offset_y

            # Move overlay to calculated position
            self.move(overlay_x, overlay_y)

        except Exception as e:
            self.logger.error(f"Failed to update overlay position: {e}")
            # If we can't update position, the window might be gone
            self.detach_from_window()

    def update_state_color(self, state):
        """Update overlay color based on application state."""
        try:
            state_name = state.value if hasattr(state, "value") else str(state).lower()

            if state_name in self.state_colors:
                self.current_color = self.state_colors[state_name]
                self.update()  # Trigger repaint
                self.logger.debug(f"Overlay color updated for state: {state_name}")
            else:
                self.logger.warning(f"Unknown state for color update: {state_name}")

        except Exception as e:
            self.logger.error(f"Failed to update overlay color: {e}")

    def paintEvent(self, event):
        """Paint the overlay graphics."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw shaded box background
            box_color = QColor(0, 0, 0, 100)  # Semi-transparent black
            painter.setBrush(QBrush(box_color))
            painter.setPen(QPen(QColor(0, 0, 0, 150), 1))
            painter.drawRect(0, 0, self.box_size, self.box_size)

            # Draw colored circle
            circle_x = (self.box_size - self.circle_diameter) // 2
            circle_y = (self.box_size - self.circle_diameter) // 2

            painter.setBrush(QBrush(self.current_color))
            painter.setPen(QPen(self.current_color.darker(120), 2))
            painter.drawEllipse(
                circle_x, circle_y, self.circle_diameter, self.circle_diameter
            )

        except Exception as e:
            self.logger.error(f"Error painting overlay: {e}")

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.logger.debug("Overlay clicked")
            # TODO: Implement expand/pin functionality
            # For now, just log the click

    def enterEvent(self, event):
        """Handle mouse enter events."""
        self.logger.debug("Mouse entered overlay")
        # TODO: Implement hover expand functionality

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.logger.debug("Mouse left overlay")
        # TODO: Implement hover collapse functionality

    def set_opacity(self, opacity: float):
        """Set overlay opacity (0.0 to 1.0)."""
        try:
            self.setWindowOpacity(opacity)
            self.logger.debug(f"Overlay opacity set to: {opacity}")
        except Exception as e:
            self.logger.error(f"Failed to set overlay opacity: {e}")

    def update_configuration(self):
        """Update overlay configuration from config manager."""
        try:
            if hasattr(self.app, "config_manager") and self.app.config_manager:
                config = self.app.config_manager

                # Update sizes
                self.circle_diameter = config.get_setting(
                    "overlay.size.circle_diameter", 24
                )
                self.box_size = config.get_setting("overlay.size.box_size", 32)

                # Update offsets
                self.offset_x = config.get_setting("overlay.position.offset_x", 0)
                self.offset_y = config.get_setting("overlay.position.offset_y", 32)

                # Update colors
                colors = config.get_setting("overlay.colors", {})
                for state_name, color_hex in colors.items():
                    if state_name in self.state_colors:
                        self.state_colors[state_name] = QColor(color_hex)

                # Update opacity
                opacity = config.get_setting("overlay.opacity", 0.8)
                self.set_opacity(opacity)

                # Update size
                self.setFixedSize(self.box_size, self.box_size)

                self.logger.debug("Overlay configuration updated")

        except Exception as e:
            self.logger.error(f"Failed to update overlay configuration: {e}")

    def hide(self):
        """Hide the overlay."""
        super().hide()
        self.logger.debug("Overlay hidden")

    def show(self):
        """Show the overlay."""
        super().show()
        self.logger.debug("Overlay shown")
