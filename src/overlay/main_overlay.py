"""
Main Overlay Widget - Simple Status Indicator

A pretty, minimal overlay that attaches to the WidgetInc window.
Just shows a colored status indicator - no complex functionality.
"""

import logging
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from utility.window_utils import find_target_window


class MainOverlayWidget(QWidget):
    """Simple, pretty overlay indicator that attaches to WidgetInc window."""

    # Signals
    target_found = pyqtSignal(bool)

    def __init__(self, target_process="WidgetInc.exe", debug_mode=False):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.target_process = target_process
        self.debug_mode = debug_mode

        # Window state
        self.target_hwnd = None
        self.target_connected = False

        # Visual properties
        self.status_color = QColor(100, 150, 255)  # Nice blue when disconnected
        self.status_text = "Searching..."

        self._setup_widget()
        self._start_monitoring()
        self._connect_app_signals()

    def _setup_widget(self):
        """Setup the overlay widget with nice styling."""
        # Window properties
        self.setWindowTitle("Widget Automation Tool - Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Size and positioning
        self.resize(120, 40)
        self._center_on_screen()

        # Make it draggable
        self.dragging = False
        self.drag_position = None

    def _start_monitoring(self):
        """Start monitoring for the target window."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_target_window)
        self.monitor_timer.start(1000)  # Check every second
        self.logger.info(f"Started monitoring for {self.target_process}")

    def _connect_app_signals(self):
        """Connect to application signals for proper shutdown."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._cleanup_and_close)
            self.logger.debug("Connected overlay to application quit signal")

    def _cleanup_and_close(self):
        """Clean up resources and close the overlay."""
        self.logger.info("*** Overlay cleanup initiated")
        if hasattr(self, "monitor_timer"):
            self.logger.debug("Stopping monitor timer")
            self.monitor_timer.stop()
        self.logger.debug("Calling overlay close()")
        self.close()
        self.logger.info("*** Overlay cleanup complete")

    def closeEvent(self, event):
        """Handle close event - ensure cleanup."""
        self.logger.info("*** Overlay close event received")
        if hasattr(self, "monitor_timer"):
            self.logger.debug("Stopping monitor timer in closeEvent")
            self.monitor_timer.stop()
        self.logger.debug("Accepting close event")
        event.accept()
        super().closeEvent(event)
        self.logger.info("*** Overlay closeEvent complete")

    def _check_target_window(self):
        """Check if target window exists and update position."""
        target_info = find_target_window(self.target_process)

        if target_info and target_info.get("window_info"):
            # Target found
            if not self.target_connected:
                self.target_connected = True
                self.status_color = QColor(50, 200, 50)  # Green when connected
                self.status_text = "Connected"
                self.target_found.emit(True)
                self.logger.info("Target window found - overlay connected")

            # Update position to attach to target window
            self._update_position(target_info)

        else:
            # Target lost
            if self.target_connected:
                self.target_connected = False
                self.status_color = QColor(255, 100, 100)  # Red when disconnected
                self.status_text = "Disconnected"
                self.target_found.emit(False)
                self.logger.info("Target window lost - overlay disconnected")

        self.update()  # Trigger repaint

    def _update_position(self, target_info):
        """Position the overlay relative to the target window."""
        try:
            window_info = target_info["window_info"]
            window_rect = window_info["window_rect"]  # (left, top, right, bottom)

            # Position overlay in top-right corner of target window
            overlay_x = window_rect[2] - self.width() - 10  # right - width - margin
            overlay_y = window_rect[1] + 10  # top + margin

            self.move(overlay_x, overlay_y)

        except Exception as e:
            self.logger.warning(f"Failed to update overlay position: {e}")
            self.logger.debug(f"Target info structure: {target_info}")

    def _center_on_screen(self):
        """Center the overlay on screen when target not found."""
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Fallback position
            self.move(100, 100)

    def paintEvent(self, event):
        """Draw the pretty status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with rounded corners and subtle shadow effect
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Shadow effect
        shadow_rect = rect.adjusted(2, 2, 2, 2)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 8, 8)

        # Main background
        gradient_color = QColor(self.status_color)
        gradient_color.setAlpha(200)
        painter.setBrush(QBrush(gradient_color))
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawRoundedRect(rect, 8, 8)

        # Status indicator dot
        dot_size = 12
        dot_x = rect.left() + 10
        dot_y = rect.center().y() - dot_size // 2
        painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)

        # Bright status dot
        bright_color = QColor(self.status_color)
        bright_color.setAlpha(255)
        painter.setBrush(QBrush(bright_color))
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
        painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)

        # Status text
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)

        text_rect = rect.adjusted(dot_x + dot_size + 8, 0, -5, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, self.status_text)

    # Mouse events for dragging
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self.dragging and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.drag_position = None
