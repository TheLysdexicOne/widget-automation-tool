"""
Overlay Window

Window         # State colors
        self.state_colors = {
            "active": QColor("#00FF00"),      # Green - performing automation
            "ready": QColor("#00FFFF"),       # Cyan - ready to activate
            "attention": QColor("#FFFF00"),   # Yellow - recognized but no automation
            "inactive": QColor("#808080"),    # Gray - not recognized
            "error": QColor("#FF0000")        # Red - error
        } that attaches to the target application window.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QAction

import pygetwindow as gw


class OverlayWindow(QWidget):
    """Overlay window that attaches to the target application."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)

        # Overlay configuration
        self.circle_diameter = 24
        self.box_size = 40  # Increased from 32 to 40
        self.offset_x = -8  # Left 8 pixels from right edge
        self.offset_y = 40  # Down 40 pixels from top edge (8 more than before)

        # State colors
        self.state_colors = {
            "active": QColor("#00FF00"),  # Green - performing automation
            "ready": QColor("#00FFFF"),  # Cyan - ready to activate
            "attention": QColor("#FFFF00"),  # Yellow - recognized but no automation
            "inactive": QColor("#FFA500"),  # Orange - not recognized
            "error": QColor("#FF0000"),  # Red - error
        }
        self.current_color = self.state_colors["inactive"]

        # Target window info
        self.target_hwnd = None
        self.target_window = None

        # Position tracking for throttled logging
        self.last_position = None
        self.last_move_time = 0
        self.position_log_delay = 1.0  # Log position only after 1 second of no movement

        # Expansion state
        self.is_expanded = False
        self.is_pinned = False
        self.original_size = (self.box_size, self.box_size)
        self.expanded_size = (200, 100)  # Expanded overlay size

        # Hover timer for expansion delay
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._expand_overlay)
        self.hover_delay = 500  # 0.5 seconds as requested

        # Animation for smooth expansion
        self.size_animation = QPropertyAnimation(self, b"geometry")
        self.size_animation.setDuration(200)  # 200ms animation
        self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.size_animation.finished.connect(self._on_animation_finished)

        # Position update timer with dynamic polling
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.slow_polling_rate = 100  # 100ms for normal operation
        self.fast_polling_rate = 8  # 16ms for title bar detection
        self.position_timer.start(self.slow_polling_rate)

        # Title bar detection for dynamic polling
        self.is_fast_polling = False
        self.fast_polling_delay = (
            2.0  # Keep fast polling for 2 seconds after leaving title bar
        )
        self.fast_polling_end_time = 0  # Track when to end fast polling
        self.delay_start_time = 0  # Track when delay period started
        self.delay_logged = False  # Track if we've logged the delay start message

        # Setup window
        self._setup_window()

    def _setup_window(self):
        """Setup the overlay window properties."""
        # Window flags for multi-monitor overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )

        # Set window title
        self.setWindowTitle("Widget Automation Overlay")

        # Set window properties
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Enable mouse tracking and hover
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Accept focus to receive mouse events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
                # Ensure overlay can receive mouse events
                self.raise_()
                self.activateWindow()
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
        if not self.target_hwnd or not self.isVisible():
            return

        try:
            import win32gui
            import time

            # Get both screen and client rectangles for title bar detection
            screen_rect = win32gui.GetWindowRect(
                self.target_hwnd
            )  # (left, top, right, bottom)
            screen_x, screen_y, screen_r, screen_b = screen_rect

            # Get client rectangle (content area without frame/titlebar)
            client_rect = win32gui.GetClientRect(self.target_hwnd)
            client_left, client_top, client_right, client_bottom = client_rect

            # Convert client coordinates to screen coordinates
            client_screen_pos = win32gui.ClientToScreen(self.target_hwnd, (0, 0))
            client_screen_x, client_screen_y = client_screen_pos

            # Calculate client area dimensions
            client_width = client_right - client_left
            client_height = client_bottom - client_top

            # Calculate title bar height for dynamic polling
            title_bar_height = client_screen_y - screen_y

            # Check if mouse is in title bar area (for dynamic polling)
            try:
                import win32api

                mouse_pos = win32api.GetCursorPos()
                mouse_x, mouse_y = mouse_pos

                # Check if mouse is in window frame area (for dynamic polling during resize)
                # This includes title bar, borders, and any non-client area
                in_window_frame = (
                    screen_x <= mouse_x <= screen_r
                    and screen_y <= mouse_y <= screen_b
                    and not (
                        client_screen_x <= mouse_x <= client_screen_x + client_width
                        and client_screen_y
                        <= mouse_y
                        <= client_screen_y + client_height
                    )
                )

                # Adjust polling rate based on title bar detection with delay
                current_time = time.time()

                if in_window_frame:
                    # Mouse is in window frame - switch to fast polling immediately
                    if not self.is_fast_polling:
                        self.is_fast_polling = True
                        self.position_timer.setInterval(self.fast_polling_rate)
                        self.logger.debug(
                            f"Switching to FAST polling ({self.fast_polling_rate}ms) - mouse in window frame"
                        )
                    # Reset the end time since we're still in window frame
                    self.fast_polling_end_time = 0
                    self.delay_start_time = 0
                    # Don't reset delay_logged here - let it persist during rapid movements

                elif self.is_fast_polling and self.fast_polling_end_time == 0:
                    # Mouse left window frame - start tracking the delay period
                    if self.delay_start_time == 0:
                        # First time leaving - start the delay tracking
                        self.delay_start_time = current_time
                        self.fast_polling_end_time = (
                            current_time
                            + self.fast_polling_delay
                            + (self.fast_polling_delay / 2.0)
                        )

                    # Check if we should log the delay message (after half the delay period)
                    grace_period = self.fast_polling_delay / 2.0
                    if (
                        not self.delay_logged
                        and current_time >= self.delay_start_time + grace_period
                    ):
                        self.delay_logged = True
                        self.logger.debug(
                            f"Mouse left window frame - keeping FAST polling for {self.fast_polling_delay} seconds"
                        )

                elif (
                    self.is_fast_polling
                    and self.fast_polling_end_time > 0
                    and current_time >= self.fast_polling_end_time
                ):
                    # Delay period has ended - switch back to slow polling
                    self.is_fast_polling = False
                    self.fast_polling_end_time = 0
                    self.delay_start_time = 0
                    self.delay_logged = False  # Reset for next cycle
                    self.position_timer.setInterval(self.slow_polling_rate)
                    self.logger.debug(
                        f"Switching to SLOW polling ({self.slow_polling_rate}ms) - delay period ended"
                    )

            except (ImportError, Exception):
                # Fallback if win32api is not available
                pass

            # Position at top-right corner of CLIENT area with offsets
            overlay_x = (
                client_screen_x + client_width - self.width() + self.offset_x
            )  # Right edge minus width plus X offset
            overlay_y = (
                client_screen_y + self.offset_y
            )  # Top edge of client area plus Y offset

            # Move overlay to calculated position
            current_position = (overlay_x, overlay_y)
            self.move(overlay_x, overlay_y)

            # Throttled logging - only log when position changes and after delay
            current_time = time.time()
            if self.last_position != current_position:
                # Position changed, update tracking
                self.last_position = current_position
                self.last_move_time = current_time
            elif (current_time - self.last_move_time) >= self.position_log_delay:
                # Position stable for required delay, log once
                if self.last_move_time > 0:  # Only log if we've actually moved
                    self.logger.debug(
                        f"Overlay positioned at ({overlay_x}, {overlay_y}) using client area: x:{client_screen_x} y:{client_screen_y} w:{client_width} h:{client_height} | Title bar: {title_bar_height}px"
                    )
                    self.last_move_time = 0  # Reset to prevent repeated logging

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

            if self.is_expanded:
                # Draw expanded overlay
                self._paint_expanded_overlay(painter)
            else:
                # Draw compact overlay
                self._paint_compact_overlay(painter)

        except Exception as e:
            self.logger.error(f"Error painting overlay: {e}")

    def _paint_compact_overlay(self, painter):
        """Paint the compact overlay (just the circle in box)."""
        # Draw rounded background with lighter shading
        box_color = QColor(0, 0, 0, 130)  # Lighter semi-transparent black (was 100)
        border_color = QColor(80, 80, 80, 180)  # Slightly lighter border

        painter.setBrush(QBrush(box_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(
            0, 0, self.box_size, self.box_size, 6, 6
        )  # 6px corner radius

        # Draw colored circle
        circle_x = (self.box_size - self.circle_diameter) // 2
        circle_y = (self.box_size - self.circle_diameter) // 2

        painter.setBrush(QBrush(self.current_color))
        painter.setPen(QPen(self.current_color.darker(120), 2))
        painter.drawEllipse(
            circle_x, circle_y, self.circle_diameter, self.circle_diameter
        )

    def _paint_expanded_overlay(self, painter):
        """Paint the expanded overlay with additional information."""
        # Draw full background with proper shading
        bg_color = QColor(44, 44, 44, 220)  # Dark gray, more opaque
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(0, 0, 0, 255), 2))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        # Draw status circle in top-right corner (anchored properly)
        circle_margin = 6
        circle_x = self.width() - self.circle_diameter - circle_margin
        circle_y = circle_margin

        painter.setBrush(QBrush(self.current_color))
        painter.setPen(QPen(self.current_color.darker(120), 2))
        painter.drawEllipse(
            circle_x, circle_y, self.circle_diameter, self.circle_diameter
        )

        # Draw status text in ALL CAPS with proper styling
        from PyQt6.QtGui import QFont

        # Main status text (large, colored, all caps)
        main_font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(main_font)
        painter.setPen(QPen(self.current_color, 2))

        # Get current state text in ALL CAPS
        state_name = "UNKNOWN"
        if hasattr(self.app, "get_state"):
            state = self.app.get_state()
            state_name = (
                state.value.upper() if hasattr(state, "value") else str(state).upper()
            )

        painter.drawText(10, 25, state_name)

        # Secondary info text (smaller, white)
        info_font = QFont("Arial", 9)
        painter.setFont(info_font)
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        # Draw pin indicator
        if self.is_pinned:
            painter.drawText(10, 45, "📌 Pinned")

        # Draw target info if available
        if self.target_window:
            target_name = (
                self.target_window.title[:20] + "..."
                if len(self.target_window.title) > 20
                else self.target_window.title
            )
            painter.drawText(10, 60 if self.is_pinned else 45, f"Target: {target_name}")

        # Draw click hint (smaller, gray)
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        hint_y = 75 if self.is_pinned else 60 if self.target_window else 45
        painter.drawText(10, hint_y, "Click to pin/unpin")

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        self.logger.info(
            f"Overlay clicked at local pos: ({event.pos().x()}, {event.pos().y()}), global pos: ({event.globalPosition().toPoint().x()}, {event.globalPosition().toPoint().y()})"
        )
        if event.button() == Qt.MouseButton.LeftButton:
            self.logger.info("Left mouse button pressed - toggling pin")
            self._toggle_pin()
        elif event.button() == Qt.MouseButton.RightButton:
            self.logger.info("Right mouse button pressed - showing context menu")
            self._show_context_menu(event.globalPosition().toPoint())
        else:
            self.logger.info(f"Non-left button pressed: {event.button()}")

    def _show_context_menu(self, global_pos):
        """Show context menu with console tab options."""
        try:
            menu = QMenu(self)

            # Add console tab actions
            console_action = QAction("Console", self)
            console_action.triggered.connect(lambda: self._show_console_tab("console"))
            menu.addAction(console_action)

            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(
                lambda: self._show_console_tab("settings")
            )
            menu.addAction(settings_action)

            monitoring_action = QAction("Monitoring", self)
            monitoring_action.triggered.connect(
                lambda: self._show_console_tab("monitoring")
            )
            menu.addAction(monitoring_action)

            debug_action = QAction("Debug", self)
            debug_action.triggered.connect(lambda: self._show_console_tab("debug"))
            menu.addAction(debug_action)

            menu.addSeparator()

            # Add overlay controls
            if self.is_pinned:
                unpin_action = QAction("Unpin Overlay", self)
                unpin_action.triggered.connect(self._toggle_pin)
                menu.addAction(unpin_action)
            else:
                pin_action = QAction("Pin Overlay", self)
                pin_action.triggered.connect(self._toggle_pin)
                menu.addAction(pin_action)

            # Show menu at cursor position
            menu.exec(global_pos)

        except Exception as e:
            self.logger.error(f"Failed to show context menu: {e}")

    def _show_console_tab(self, tab_name):
        """Show the debug console and switch to specified tab."""
        try:
            if hasattr(self.app, "debug_console") and self.app.debug_console:
                self.app.debug_console.show()
                self.app.debug_console.raise_()
                self.app.debug_console.activateWindow()

                # Switch to the specified tab
                if hasattr(self.app.debug_console, "switch_to_tab"):
                    self.app.debug_console.switch_to_tab(tab_name)
                else:
                    self.logger.warning("Debug console does not support tab switching")
            else:
                self.logger.warning("Debug console not available")

        except Exception as e:
            self.logger.error(f"Failed to show console tab {tab_name}: {e}")

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        # Mouse movement events (no logging to reduce noise)
        pass

    def enterEvent(self, event):
        """Handle mouse enter events."""
        # Only track entry, no automatic expansion
        pass

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        # Only track exit, no automatic collapse
        pass

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

    def _expand_overlay(self):
        """Expand the overlay to show additional information."""
        if not self.is_expanded and not self.is_pinned:
            self.logger.debug("Expanding overlay")
            self.is_expanded = True
            self._animate_to_size(self.expanded_size)

    def _collapse_overlay(self):
        """Collapse the overlay back to original size."""
        if self.is_expanded and not self.is_pinned:
            self.logger.debug("Collapsing overlay")
            self.is_expanded = False
            self._animate_to_size(self.original_size)

    def _toggle_pin(self):
        """Toggle the pinned state of the overlay."""
        self.is_pinned = not self.is_pinned
        self.logger.debug(f"Overlay pinned: {self.is_pinned}")

        if self.is_pinned:
            # Expand when pinned
            if not self.is_expanded:
                self.logger.debug(
                    f"Expanding overlay from {self.original_size} to {self.expanded_size}"
                )
                self.is_expanded = True
                self._animate_to_size(self.expanded_size)
            else:
                self.logger.debug("Overlay already expanded")
        else:
            # Always collapse when unpinned
            self._collapse_overlay()

    def _animate_to_size(self, target_size):
        """Animate the overlay to a target size."""
        current_geometry = self.geometry()
        new_width, new_height = target_size

        self.logger.debug(
            f"Animating from {current_geometry.width()}x{current_geometry.height()} to {new_width}x{new_height}"
        )

        # Remove fixed size constraint to allow resizing
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # Qt's maximum size

        # For expansion, we want to maintain the top-right anchor point
        # So when expanding from 40x40 to 200x100, we need to move left
        if new_width > current_geometry.width():
            # Expanding - move left to maintain right edge position
            new_x = current_geometry.x() - (new_width - current_geometry.width())
        else:
            # Contracting - move right to restore position
            new_x = current_geometry.x() + (current_geometry.width() - new_width)

        # Keep the same Y position (top edge stays in place)
        new_y = current_geometry.y()

        target_geometry = QRect(new_x, new_y, new_width, new_height)

        self.logger.debug(f"Target geometry: {target_geometry}")

        self.size_animation.setStartValue(current_geometry)
        self.size_animation.setEndValue(target_geometry)
        self.size_animation.start()

    def _on_animation_finished(self):
        """Called when size animation finishes - restore fixed size constraint."""
        current_size = self.size()
        self.setFixedSize(current_size)
        self.logger.debug(
            f"Animation finished. Fixed size restored to {current_size.width()}x{current_size.height()}"
        )
        self.update()
