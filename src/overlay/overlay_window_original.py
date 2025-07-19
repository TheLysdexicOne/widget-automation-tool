"""
Simplified overlay window with always-expanded design and screenshot functionality.
Always shows the full 200x100 overlay with status circle and screenshot button.
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
from utility.window_utils import calculate_overlay_position
from utility.widget_utils import create_floating_button, ensure_widget_on_top
from utility.logging_utils import get_smart_logger


class OverlayWindowOriginal(QWidget):
    """
    Simplified overlay window with always-expanded design and screenshot functionality.
    Always shows 200x100 overlay with status circle and external screenshot button.
    """

    def __init__(self, window_manager, app=None):
        super().__init__()
        self.window_manager = window_manager
        self.app = app  # Reference to main application for target window info
        self.logger = get_smart_logger(__name__)

        # Overlay dimensions (always expanded)
        self.overlay_width = 200
        self.overlay_height = 100
        self.circle_diameter = 24  # Status indicator circle

        # State management (simplified)
        self.screenshot_menu = None  # Track active screenshot menu
        self.screenshot_menu_open = False  # Simple flag to track menu state
        self.screenshot_button_widget = None  # External screenshot button widget

        # State colors matching original
        self.state_colors = {
            "active": QColor("#00FF00"),  # Green - performing automation
            "ready": QColor("#00FFFF"),  # Cyan - ready to activate
            "attention": QColor("#FFFF00"),  # Yellow - recognized but no automation
            "inactive": QColor("#FFA500"),  # Orange - not recognized
            "error": QColor("#FF0000"),  # Red - error
        }
        self.current_color = self.state_colors["inactive"]

        # Timer for updates - slightly faster for smooth window following
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 100ms for smooth window following

        self.setup_window()

    def setup_window(self):
        """Initialize the overlay window for always-expanded mode."""
        # Window flags for overlay behavior
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

        # Set fixed size to expanded overlay dimensions
        self.setFixedSize(self.overlay_width, self.overlay_height)

        # Create and show external screenshot button immediately
        self._create_screenshot_button()
        self.logger.info(
            f"Screenshot button widget created: {self.screenshot_button_widget is not None}"
        )

        # Initially hidden
        self.hide()

        self.logger.debug("Simplified overlay window setup complete")

    def position_overlay(self):
        """Position overlay in top-right corner of target window."""
        if not (self.app and self.app.current_target_window):
            if self.isVisible():
                self.hide()
            return

        try:
            window = self.app.current_target_window
            target_x, target_y = calculate_overlay_position(
                window, self.width(), self.height(), offset_x=-8, offset_y=40
            )

            # Only move if position actually changed (reduce flicker)
            current_pos = self.pos()
            if current_pos.x() != target_x or current_pos.y() != target_y:
                self.move(target_x, target_y)

                # Also reposition screenshot button
                if (
                    self.screenshot_button_widget
                    and self.screenshot_button_widget.isVisible()
                ):
                    self._position_screenshot_button()

        except Exception as e:
            self.logger.error(f"Error positioning overlay: {e}")

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
        """Paint the always-expanded overlay graphics."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._paint_overlay(painter)

        except Exception as e:
            self.logger.error(f"Error painting overlay: {e}")

    def _paint_overlay(self, painter):
        """Paint the always-expanded overlay with status circle and information."""
        # Draw full background with proper shading
        bg_color = QColor(44, 44, 44, 220)  # Dark gray, more opaque
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(0, 0, 0, 255), 2))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        # Draw status circle in top-right corner
        circle_margin = 6
        circle_x = self.width() - self.circle_diameter - circle_margin
        circle_y = circle_margin

        # Determine display color based on app state
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
                display_color = self.state_colors["inactive"]  # Orange - not recognized
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

        # Set up fonts for text
        main_font = QFont("Arial", 12, QFont.Weight.Bold)
        info_font = QFont("Arial", 9)

        # Line spacing
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

        painter.drawText(10, start_y, state_text)

        # Line 2: Target info
        painter.setFont(info_font)
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        if self.app and self.app.current_target_window:
            target_name = self.app.current_target_window.title
            if len(target_name) > 15:  # Adjust length to fit layout
                target_name = target_name[:15] + "..."

            # Draw target text
            target_text = f"Target: {target_name}"
            painter.drawText(10, start_y + line_height, target_text)

        # Line 3: Click hint
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawText(10, start_y + (2 * line_height), "Right-click for menu")

    def _create_screenshot_button(self):
        """Create the external screenshot button widget."""
        if self.screenshot_button_widget:
            return  # Already created

        # Use utility to create standardized floating button
        self.screenshot_button_widget = create_floating_button(
            parent=self,
            width=40,
            height=30,
            click_handler=self._handle_screenshot_button_click,
            icon_text="📷",
        )

        self.logger.info("External screenshot button created successfully")

    def _handle_screenshot_button_click(self, event):
        """Handle screenshot button click."""
        self.logger.info("External screenshot button clicked")

        if self.screenshot_menu_open:
            if self.screenshot_menu:
                self.screenshot_menu.close()
            self._on_screenshot_menu_closed()
        else:
            self._show_screenshot_menu(event.globalPosition().toPoint())

    def _position_screenshot_button(self):
        """Position the screenshot button below the status circle."""
        if not self.screenshot_button_widget:
            return

        # Position below the status circle (not the entire overlay)
        circle_margin = 2
        circle_diameter = self.circle_diameter
        button_margin = 0
        x_offset = -6

        overlay_geometry = self.geometry()

        # Status circle is in top-right corner
        circle_x = overlay_geometry.x() + (
            overlay_geometry.width() - circle_diameter - circle_margin + x_offset
        )
        circle_y = overlay_geometry.y() + circle_margin

        # Position button below the circle, centered horizontally with it
        button_x = (
            circle_x + (circle_diameter - self.screenshot_button_widget.width()) // 2
        )
        button_y = circle_y + circle_diameter + button_margin

        self.screenshot_button_widget.move(button_x, button_y)

        # Ensure screenshot button stays on top of overlay
        self.screenshot_button_widget.raise_()
        self.screenshot_button_widget.activateWindow()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events - left click to pin, right click for menu."""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

        # Ensure screenshot button stays visible after overlay interaction
        ensure_widget_on_top(self.screenshot_button_widget)

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

            # Offset
            offset_x = -50

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

            # Show menu at specified position or fallback to overlay center
            if position:
                menu_pos = QPoint(position.x() + offset_x, position.y())
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

    def _update_display(self):
        """Update display information and position."""
        # Always reposition the overlay to follow the target window
        self.position_overlay()

        # Ensure overlay is visible if we have a target window
        if self.app and self.app.current_target_window and not self.isVisible():
            self.show()

        # Always ensure screenshot button is positioned and visible when overlay is visible
        if self.isVisible():
            self._position_screenshot_button()
            if (
                self.screenshot_button_widget
                and not self.screenshot_button_widget.isVisible()
            ):
                self.screenshot_button_widget.show()
            # Always ensure screenshot button is on top
            if (
                self.screenshot_button_widget
                and self.screenshot_button_widget.isVisible()
            ):
                self.screenshot_button_widget.raise_()
        else:
            # Hide screenshot button when overlay is hidden
            if (
                self.screenshot_button_widget
                and self.screenshot_button_widget.isVisible()
            ):
                self.screenshot_button_widget.hide()

        self.update()  # Trigger repaint

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
