"""
Widget-based overlay window matching original design with screenshot functionality.
40x40 square with status circle, pin functionality, and expanded interface when pinned.
"""

import json
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QFrame,
    QScrollArea,
    QGridLayout,
    QLineEdit,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QApplication,
    QMenu,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QPoint,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QPixmap,
    QPaintEvent,
    QMouseEvent,
    QAction,
)
import pyautogui

from core.window_manager import WindowManager


class OverlayWindowOriginal(QWidget):
    """
    Original-style overlay window with screenshot functionality.
    40x40 square with status circle, pin functionality, and expanded interface when pinned.
    """

    def __init__(self, window_manager, app=None):
        super().__init__()
        self.window_manager = window_manager
        self.app = app  # Reference to main application for target window info
        self.logger = logging.getLogger(__name__)

        # Original overlay dimensions and state
        self.box_size = 40  # Original 40x40 square
        self.circle_diameter = 24  # Status indicator circle
        self.border_width = 2

        # State management
        self.is_expanded = False
        self.is_pinned = False
        self.expanded_size = (200, 100)  # Expanded overlay size
        self.screenshot_button_rect = None  # Will be set during painting
        self.screenshot_menu = None  # Track active screenshot menu
        self.screenshot_menu_open = False  # Simple flag to track menu state

        # State colors matching original
        self.state_colors = {
            "active": QColor("#00FF00"),  # Green - performing automation
            "ready": QColor("#00FFFF"),  # Cyan - ready to activate
            "attention": QColor("#FFFF00"),  # Yellow - recognized but no automation
            "inactive": QColor("#FFA500"),  # Orange - not recognized
            "error": QColor("#FF0000"),  # Red - error
        }
        self.current_color = self.state_colors["inactive"]

        # Animation for smooth expansion
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self._on_animation_finished)

        # Expanded widget (created but hidden initially)
        self.expanded_widget = None

        # Timer for updates - slightly faster for smooth window following
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 75ms (~13 FPS) for smooth window following

        self.setup_window()

    def setup_window(self):
        """Initialize the overlay window with original settings."""
        # Window flags for overlay behavior (matching original)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Enable mouse tracking and hover (for right-click functionality)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set fixed size to 40x40
        self.setFixedSize(self.box_size, self.box_size)

        # Initially hidden
        self.hide()

        self.logger.debug("Original-style overlay window setup complete")

    def position_overlay(self):
        """Position overlay in top-right corner of target window (matching original offset)."""
        if self.app and self.app.current_target_window:
            try:
                window = self.app.current_target_window

                # Use original offset calculations
                offset_x = -8  # Left 8 pixels from right edge
                offset_y = 40  # Down 40 pixels from top edge

                # Position at top-right corner of CLIENT area with offsets
                target_x = window.left + window.width - self.width() + offset_x
                target_y = window.top + offset_y

                # Only move if position actually changed (reduce flicker)
                current_pos = self.pos()
                if current_pos.x() != target_x or current_pos.y() != target_y:
                    self.logger.debug(
                        f"Target window: left={window.left}, top={window.top}, width={window.width}, height={window.height}"
                    )
                    self.logger.debug(
                        f"Repositioning overlay from ({current_pos.x()}, {current_pos.y()}) to ({target_x}, {target_y})"
                    )
                    self.move(target_x, target_y)

            except Exception as e:
                self.logger.error(f"Error positioning overlay: {e}")
        else:
            # Hide overlay if no target window
            if self.isVisible():
                self.logger.debug("No target window available - hiding overlay")
                self.hide()

    def update_state_color(self, state):
        """Update overlay color based on application state."""
        try:
            state_name = state.value if hasattr(state, "value") else str(state).lower()

            if state_name in self.state_colors:
                old_color = self.current_color
                self.current_color = self.state_colors[state_name]
                self.logger.debug(
                    f"State color updated: {state_name} -> {self.current_color.name()}"
                )
                if old_color != self.current_color:
                    self.update()
            else:
                self.logger.warning(f"Unknown state: {state_name}")
                self.current_color = self.state_colors["error"]

        except Exception as e:
            self.logger.error(f"Failed to update overlay color: {e}")

    def paintEvent(self, event: QPaintEvent):
        """Paint the overlay graphics matching original design."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            if self.is_expanded:
                self._paint_expanded_overlay(painter)
            else:
                self._paint_compact_overlay(painter)

        except Exception as e:
            self.logger.error(f"Error painting overlay: {e}")

    def _paint_compact_overlay(self, painter):
        """Paint the compact overlay (40x40 square with circle) - matching original."""
        # Draw rounded background with consistent color scheme
        bg_color = QColor(44, 44, 44, 220)  # Same as expanded overlay
        border_color = QColor(0, 0, 0, 255)  # Black border to match expanded

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(
            0, 0, self.box_size, self.box_size, 6, 6
        )  # 6px corner radius

        # Draw status circle (centered in the square)
        circle_x = (self.box_size - self.circle_diameter) // 2
        circle_y = (self.box_size - self.circle_diameter) // 2

        # Use the same state color logic as expanded overlay
        status_info = self._get_status_info()

        # Determine display color based on app state priority (same as expanded)
        if hasattr(self.app, "_state") and self.app._state:
            state = self.app._state
            state_name = state.value if hasattr(state, "value") else str(state).lower()

            # Use the proper state colors (matching ApplicationState enum)
            if state_name == "active":
                display_color = self.state_colors[
                    "active"
                ]  # Green - performing automation
            elif state_name == "ready":
                display_color = self.state_colors["ready"]  # Cyan - ready to activate
            elif state_name == "attention":
                display_color = self.state_colors[
                    "attention"
                ]  # Yellow - recognized but no automation
            elif state_name == "inactive":
                display_color = self.state_colors[
                    "inactive"
                ]  # Orange - not recognized (per ApplicationState)
            else:
                display_color = self.state_colors["error"]  # Red - error
        else:
            # Fallback: Orange for inactive if no app state
            display_color = self.state_colors["inactive"]

        painter.setBrush(QBrush(display_color))
        painter.setPen(QPen(display_color.darker(120), 2))
        painter.drawEllipse(
            circle_x, circle_y, self.circle_diameter, self.circle_diameter
        )

    def _paint_expanded_overlay(self, painter):
        """Paint the expanded overlay matching the original ASCII layout from prompt1.md."""
        # Draw full background with proper shading (matching original)
        bg_color = QColor(44, 44, 44, 220)  # Dark gray, more opaque
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(0, 0, 0, 255), 2))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        # Draw status circle in top-right corner (matching prompt1.md layout)
        circle_margin = 6
        circle_x = self.width() - self.circle_diameter - circle_margin
        circle_y = circle_margin

        # Status color based on current state (proper color meanings)
        status_info = self._get_status_info()

        # Determine display color based on app state priority
        if hasattr(self.app, "_state") and self.app._state:
            state = self.app._state
            state_name = state.value if hasattr(state, "value") else str(state).lower()

            # Use the proper state colors (matching ApplicationState enum)
            if state_name == "active":
                display_color = self.state_colors[
                    "active"
                ]  # Green - performing automation
            elif state_name == "ready":
                display_color = self.state_colors["ready"]  # Cyan - ready to activate
            elif state_name == "attention":
                display_color = self.state_colors[
                    "attention"
                ]  # Yellow - recognized but no automation
            elif state_name == "inactive":
                display_color = self.state_colors[
                    "inactive"
                ]  # Orange - not recognized (per ApplicationState)
            else:
                display_color = self.state_colors["error"]  # Red - error
        else:
            # Fallback: Orange for inactive if no app state
            display_color = self.state_colors["inactive"]

        painter.setBrush(QBrush(display_color))
        painter.setPen(QPen(display_color.darker(120), 2))
        painter.drawEllipse(
            circle_x, circle_y, self.circle_diameter, self.circle_diameter
        )

        # Set up fonts for text (matching original spacing)
        main_font = QFont("Arial", 12, QFont.Weight.Bold)
        info_font = QFont("Arial", 9)

        # Line spacing to match ASCII layout
        line_height = 15
        start_y = 20

        # Line 1: State name in ALL CAPS with proper color
        painter.setFont(main_font)
        painter.setPen(QPen(display_color, 2))

        state_text = "INACTIVE"
        if hasattr(self.app, "_state") and self.app._state:
            state = self.app._state
            state_text = (
                state.value.upper() if hasattr(state, "value") else str(state).upper()
            )

        # Just draw the state text - the status circle is positioned separately
        painter.drawText(10, start_y, state_text)

        # Line 2: Pin indicator (matching prompt1.md: "(-) Pinned")
        painter.setFont(info_font)
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        if self.is_pinned:
            painter.drawText(10, start_y + line_height, "📌 Pinned")

        # Line 3: Target info (matching prompt1.md: "Target: WidgetInc")
        if self.app and self.app.current_target_window:
            target_name = self.app.current_target_window.title
            if len(target_name) > 15:  # Adjust length to fit layout
                target_name = target_name[:15] + "..."

            # Calculate position for screenshot button (S) on same line
            target_text = f"Target: {target_name}"
            painter.drawText(10, start_y + (2 * line_height), target_text)

            # Draw (S) button on the right side of same line
            s_button_x = self.width() - 30  # Position from right edge
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawText(s_button_x, start_y + (2 * line_height), "(S)")

            # Store screenshot button area for click detection
            self.screenshot_button_rect = QRect(
                s_button_x - 5, start_y + (2 * line_height) - 12, 20, 15
            )

        # Line 4: Click hint (matching prompt1.md: "Click to pin/unpin")
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawText(10, start_y + (3 * line_height), "Click to pin/unpin")

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events - left click to pin, right click for menu."""
        self.logger.info(
            f"Overlay clicked at local pos: ({event.pos().x()}, {event.pos().y()}), global pos: ({event.globalPosition().toPoint().x()}, {event.globalPosition().toPoint().y()})"
        )

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on the screenshot button in expanded mode
            if (
                self.is_expanded
                and self.screenshot_button_rect
                and self.screenshot_button_rect.contains(event.pos())
            ):
                self.logger.info("Screenshot button (S) clicked - toggling menu")
                # Simple toggle: if flag says open, close it; if closed, open it
                if self.screenshot_menu_open:
                    self.logger.info("Menu is open - closing")
                    if self.screenshot_menu:
                        self.screenshot_menu.close()
                    self._on_screenshot_menu_closed()
                else:
                    self.logger.info("Menu is closed - opening")
                    self._show_screenshot_menu(event.globalPosition().toPoint())
            else:
                self.logger.info("Left mouse button pressed - toggling pin")
                self._toggle_pin()
        elif event.button() == Qt.MouseButton.RightButton:
            self.logger.info("Right mouse button pressed - showing context menu")
            self._show_context_menu(event.globalPosition().toPoint())

        # Record click in mouse tracker
        if self.app and hasattr(self.app, "mouse_tracker") and self.app.mouse_tracker:
            global_pos = event.globalPosition().toPoint()
            button = "left" if event.button() == Qt.MouseButton.LeftButton else "right"
            self.app.mouse_tracker.record_click(global_pos.x(), global_pos.y(), button)

    def _show_context_menu(self, global_pos):
        """Show context menu with console tab options (matching original)."""
        try:
            menu = QMenu(self)

            # Add console tab actions (matching original)
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
                console = self.app.debug_console
                console.show()
                console.raise_()
                console.activateWindow()

                # Switch to the requested tab
                if hasattr(console, "switch_to_tab"):
                    console.switch_to_tab(tab_name)
                self.logger.debug(f"Switched to console tab: {tab_name}")
            else:
                self.logger.warning("Debug console not available")

        except Exception as e:
            self.logger.error(f"Failed to show console tab {tab_name}: {e}")

    def _toggle_pin(self):
        """Toggle the pinned state and expand/collapse accordingly."""
        self.is_pinned = not self.is_pinned
        self.logger.debug(f"Overlay pinned: {self.is_pinned}")

        if self.is_pinned:
            # Pin and expand
            self._expand_overlay()
        else:
            # Unpin and collapse
            self._collapse_overlay()

        self.update()  # Repaint to show pin status

    def _expand_overlay(self):
        """Expand the overlay to show additional information and screenshot button."""
        if not self.is_expanded:
            self.is_expanded = True
            self.logger.debug("Expanding overlay")

            # Create expanded widget if it doesn't exist
            if not self.expanded_widget:
                self.expanded_widget = self._create_expanded_widget()

            # Setup layout with expanded widget
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.expanded_widget)
            self.setLayout(layout)

            # Show expanded widget
            self.expanded_widget.show()

            self._animate_to_size(self.expanded_size)

    def _collapse_overlay(self):
        """Collapse the overlay back to original size."""
        if self.is_expanded:
            self.is_expanded = False
            self.logger.debug("Collapsing overlay")

            # Hide expanded widget
            if self.expanded_widget:
                self.expanded_widget.hide()

            # Remove layout
            if self.layout():
                self.layout().deleteLater()

            self._animate_to_size((self.box_size, self.box_size))

    def _create_expanded_widget(self):
        """Create the expanded widget with screenshot functionality (only when pinned)."""
        widget = QWidget()
        widget.setStyleSheet(
            """
            QWidget {
                background-color: transparent;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #4a4a5a;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #5a5a6a;
            }
            QPushButton:pressed {
                background-color: #3a3a4a;
            }
        """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 30, 10, 10)  # Top margin to avoid status circle

        # Screenshot button (only shown when pinned, per prompt1.md)
        screenshot_btn = QPushButton("📷 Screenshot")
        screenshot_btn.clicked.connect(self._show_screenshot_menu)
        layout.addWidget(screenshot_btn)

        widget.setLayout(layout)
        return widget

    def _show_screenshot_menu(self, position=None):
        """Show the screenshot dropdown menu as per prompt1.md."""
        try:
            # Mark menu as open immediately
            self.screenshot_menu_open = True

            # Close existing menu if any
            if self.screenshot_menu and self.screenshot_menu.isVisible():
                self.screenshot_menu.close()

            # Create new menu
            self.screenshot_menu = QMenu(self)

            # Add menu items as per prompt1.md
            add_new_action = QAction("Add New Minigame", self.screenshot_menu)
            add_new_action.triggered.connect(
                lambda: self._handle_screenshot_action("add_new")
            )
            self.screenshot_menu.addAction(add_new_action)

            attach_action = QAction("Attach to Minigame", self.screenshot_menu)
            attach_action.triggered.connect(
                lambda: self._handle_screenshot_action("attach")
            )
            self.screenshot_menu.addAction(attach_action)

            self.screenshot_menu.addSeparator()

            edit_action = QAction("Edit Minigames", self.screenshot_menu)
            edit_action.triggered.connect(
                lambda: self._handle_screenshot_action("edit")
            )
            self.screenshot_menu.addAction(edit_action)

            # Show menu at specified position or near screenshot button
            if position:
                menu_pos = position
            elif self.expanded_widget and self.expanded_widget.layout().itemAt(0):
                button_rect = (
                    self.expanded_widget.layout().itemAt(0).widget().geometry()
                )
                menu_pos = self.mapToGlobal(
                    QPoint(button_rect.x(), button_rect.bottom())
                )
            else:
                # Fallback to center of overlay
                menu_pos = self.mapToGlobal(self.rect().center())

            # Connect to cleanup when menu closes
            self.screenshot_menu.aboutToHide.connect(self._on_screenshot_menu_closed)

            # Show menu (this blocks until closed)
            self.screenshot_menu.exec(menu_pos)

            # Menu closed - ensure cleanup happens
            self._on_screenshot_menu_closed()

        except Exception as e:
            self.logger.error(f"Failed to show screenshot menu: {e}")
            self._on_screenshot_menu_closed()  # Ensure flag is reset on error

    def _on_screenshot_menu_closed(self):
        """Called when screenshot menu is closed."""
        self.screenshot_menu = None
        self.screenshot_menu_open = False
        self.logger.info("Screenshot menu closed - flag reset")

    def _handle_screenshot_action(self, action):
        """Handle screenshot menu actions."""
        self.logger.info(f"Screenshot action: {action}")

        if action == "add_new":
            self._add_new_minigame()
        elif action == "attach":
            self._attach_to_minigame()
        elif action == "edit":
            self._edit_minigames()

    def _add_new_minigame(self):
        """Show Add New Minigame dialog as per prompt1.md."""
        # For now, show a placeholder message
        self.logger.info("Add New Minigame - Coming soon!")

    def _attach_to_minigame(self):
        """Show Attach to Minigame dialog as per prompt1.md."""
        # For now, show a placeholder message
        self.logger.info("Attach to Minigame - Coming soon!")

    def _edit_minigames(self):
        """Show Edit Minigames dialog as per prompt1.md."""
        # For now, show a placeholder message
        self.logger.info("Edit Minigames - Coming soon!")

    def _animate_to_size(self, target_size):
        """Animate the overlay to a target size (matching original)."""
        current_geometry = self.geometry()
        new_width, new_height = target_size

        self.logger.debug(
            f"Animating from {current_geometry.width()}x{current_geometry.height()} to {new_width}x{new_height}"
        )

        # Remove fixed size constraint to allow resizing
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # Qt's maximum size

        # For expansion, maintain the top-right anchor point
        if new_width > current_geometry.width():
            # Expanding - move left to maintain right edge position
            new_x = current_geometry.x() - (new_width - current_geometry.width())
        else:
            # Collapsing - move right to maintain right edge position
            new_x = current_geometry.x() + (current_geometry.width() - new_width)

        # Keep the same Y position (top edge stays in place)
        new_y = current_geometry.y()

        target_geometry = QRect(new_x, new_y, new_width, new_height)

        self.logger.debug(f"Target geometry: {target_geometry}")

        self.animation.setStartValue(current_geometry)
        self.animation.setEndValue(target_geometry)
        self.animation.start()

    def _on_animation_finished(self):
        """Called when size animation finishes - restore fixed size constraint."""
        current_size = self.size()
        self.setFixedSize(current_size)
        self.logger.debug(
            f"Animation finished. Fixed size restored to {current_size.width()}x{current_size.height()}"
        )
        self.update()

    def _update_display(self):
        """Update display information and position."""
        # Always reposition the overlay to follow the target window
        self.position_overlay()

        # Ensure overlay is visible if we have a target window
        if self.app and self.app.current_target_window and not self.isVisible():
            self.show()

        if not self.is_expanded:
            self.update()  # Trigger repaint for compact mode

    def _get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        target_found = (
            self.app
            and self.app.current_target_window
            and hasattr(self.app.current_target_window, "isActive")
        )

        return {
            "target_found": target_found,
        }
