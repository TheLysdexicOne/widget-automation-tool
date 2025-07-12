#!/usr/bin/env python3
"""
Enhanced Overlay GUI with Activate Button and Settings
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
import pyperclip
import pyautogui
from overlay_gui import OverlayGUI
from widget_inc_manager import WidgetIncManager


class EnhancedOverlay(OverlayGUI):
    def __init__(self):
        # Settings
        self.hide_activate_button_setting = False
        self.debug_mode = False
        self.enable_logging = False
        self.enable_on_screen_debug = False
        self.enable_disabled_buttons = False
        self.enable_cursor_trail = False
        self.enable_click_visuals = False
        self.enable_cursor_tracking = False

        # State
        self.current_minigame = None
        self.automation_active = False
        self.automation_start_time = None
        self.activate_button = None
        self.status_overlay = None
        self.cursor_info_label = None

        # Click recording
        self.click_history = []
        self.max_click_history = 10
        self.recording_clicks = False
        self.drag_start = None
        self.recorded_clicks = []  # List to store recorded clicks
        self.enable_click_recording = False  # Toggle for click recording

        # Initialize parent
        super().__init__()

        # Override dimensions for larger overlay
        self.collapsed_size = (40, 40)
        self.circle_size = (30, 30)
        self.expanded_width = 320
        self.expanded_height = 160

        # Bind mouse motion for cursor tracking
        self.root.bind("<Motion>", self.on_mouse_motion)

    def setup_gui(self):
        """Initialize the enhanced overlay GUI"""
        super().setup_gui()

        # Create activate button (initially hidden)
        self.create_activate_button()

        # Create status overlay for active state
        self.create_status_overlay()

    def create_activate_button(self):
        """Create the activate button"""
        if not self.widget_manager.find_widget_inc_window():
            return

        window = self.widget_manager.window
        if not window:
            return

        # Calculate button position (center screen, 20% from bottom)
        button_width = 120
        button_height = 40
        button_x = window.left + (window.width - button_width) // 2
        button_y = window.top + int(window.height * 0.8) - button_height // 2

        # Create button window
        self.activate_button = tk.Toplevel()
        self.activate_button.title("Activate")
        self.activate_button.geometry(
            f"{button_width}x{button_height}+{button_x}+{button_y}"
        )
        self.activate_button.attributes("-topmost", True)
        self.activate_button.attributes("-alpha", 0.9)
        self.activate_button.overrideredirect(True)

        # Create button
        self.activate_btn = tk.Button(
            self.activate_button,
            text="ACTIVATE",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=3,
            command=self.on_activate_clicked,
        )
        self.activate_btn.pack(fill="both", expand=True)

        # Initially hide the button
        self.activate_button.withdraw()

        # Add tooltip for disabled state
        self.create_tooltip(
            self.activate_btn, "Logic for this minigame has not been coded yet"
        )

    def create_status_overlay(self):
        """Create status overlay for active state"""
        if not self.widget_manager.find_widget_inc_window():
            return

        window = self.widget_manager.window
        if not window:
            return

        # Create status window at top of screen
        self.status_overlay = tk.Toplevel()
        self.status_overlay.title("Status")
        self.status_overlay.geometry(
            f"400x60+{window.left + (window.width - 400) // 2}+{window.top + 20}"
        )
        self.status_overlay.attributes("-topmost", True)
        self.status_overlay.attributes("-alpha", 0.9)
        self.status_overlay.overrideredirect(True)
        self.status_overlay.configure(bg="#2C2C2C")

        # Create status label
        self.status_label = tk.Label(
            self.status_overlay,
            text="Press SPACE or ESCAPE to stop",
            font=("Arial", 14, "bold"),
            bg="#2C2C2C",
            fg="white",
        )
        self.status_label.pack(pady=5)

        # Create timer label
        self.timer_label = tk.Label(
            self.status_overlay,
            text="Timer: 00:00",
            font=("Arial", 12),
            bg="#2C2C2C",
            fg="#CCCCCC",
        )
        self.timer_label.pack()

        # Initially hide the status overlay
        self.status_overlay.withdraw()

        # Bind keyboard events
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_set()

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""

        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip.configure(bg="#FFFFE0")

            label = tk.Label(
                tooltip,
                text=text,
                font=("Arial", 10),
                bg="#FFFFE0",
                fg="black",
                relief="solid",
                bd=1,
                padx=5,
                pady=3,
            )
            label.pack()

            # Hide tooltip after 3 seconds
            tooltip.after(3000, tooltip.destroy)

        widget.bind("<Enter>", show_tooltip)

    def draw_expanded(self):
        """Draw the expanded state with settings"""
        # Calculate required height
        base_height = 140
        debug_height = 120 if self.debug_mode else 0
        cursor_height = 120 if self.enable_cursor_tracking else 0

        new_height = base_height + debug_height + cursor_height

        # Resize if needed
        if self.expanded_height != new_height:
            self.expanded_height = new_height
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            self.root.geometry(
                f"{self.expanded_width}x{self.expanded_height}+{current_x}+{current_y}"
            )
            self.canvas.configure(
                width=self.expanded_width, height=self.expanded_height
            )

        # Clear and redraw
        self.canvas.delete("all")

        # Draw background
        self.canvas.create_rectangle(
            0,
            0,
            self.expanded_width,
            self.expanded_height,
            fill=self.bg_color,
            outline="#555555",
        )

        # Draw circle
        circle_x = self.expanded_width - self.circle_size[0] - 5
        circle_y = 5
        self.canvas.create_oval(
            circle_x,
            circle_y,
            circle_x + self.circle_size[0],
            circle_y + self.circle_size[1],
            fill=self.circle_color,
            outline=self.circle_color,
        )

        # Draw pin icon if pinned
        text_x = 40 if self.is_pinned else 10
        if self.is_pinned:
            self.draw_pin_icon(10, 10)

        # Draw status text
        self.canvas.create_text(
            text_x,
            20,
            text=self.status_text,
            fill=self.text_color,
            font=("Arial", 12, "bold"),
            anchor="w",
        )

        # Draw detail text
        self.canvas.create_text(
            text_x,
            40,
            text=self.detail_text,
            fill=self.text_color,
            font=("Arial", 9),
            anchor="w",
        )

        # Draw settings checkboxes
        y_offset = 70

        # Hide Activate Button checkbox
        self.draw_checkbox(
            10, y_offset, "Hide Activate Button", self.hide_activate_button_setting
        )
        y_offset += 25

        # Debug Mode checkbox
        self.draw_checkbox(10, y_offset, "Debug Mode", self.debug_mode)
        y_offset += 25

        # Debug mode options
        if self.debug_mode:
            self.draw_checkbox(20, y_offset, "Enable logging", self.enable_logging)
            y_offset += 20
            self.draw_checkbox(
                20, y_offset, "Enable on-screen debug", self.enable_on_screen_debug
            )
            y_offset += 20
            self.draw_checkbox(
                20, y_offset, "Enable disabled buttons", self.enable_disabled_buttons
            )
            y_offset += 20
            self.draw_checkbox(
                20, y_offset, "Enable cursor trail", self.enable_cursor_trail
            )
            y_offset += 20
            self.draw_checkbox(
                20, y_offset, "Enable click visuals", self.enable_click_visuals
            )
            y_offset += 20
            self.draw_checkbox(
                20, y_offset, "Enable cursor tracking", self.enable_cursor_tracking
            )
            y_offset += 25

        # Cursor tracking info
        if self.enable_cursor_tracking:
            self.draw_cursor_info(y_offset)

    def draw_checkbox(self, x, y, text, checked):
        """Draw a checkbox with text"""
        # Draw checkbox
        checkbox_size = 12
        self.canvas.create_rectangle(
            x, y, x + checkbox_size, y + checkbox_size, fill="white", outline="gray"
        )

        if checked:
            self.canvas.create_text(
                x + checkbox_size // 2,
                y + checkbox_size // 2,
                text="✓",
                fill="green",
                font=("Arial", 8, "bold"),
            )

        # Draw text
        self.canvas.create_text(
            x + checkbox_size + 5,
            y + checkbox_size // 2,
            text=text,
            fill=self.text_color,
            font=("Arial", 8),
            anchor="w",
        )

    def draw_cursor_info(self, y_offset):
        """Draw cursor tracking information"""
        # Get current cursor position
        cursor_x, cursor_y = pyautogui.position()

        # Format cursor position with better layout
        cursor_info = f"Cursor: ({cursor_x}, {cursor_y})"

        # Draw cursor position
        self.canvas.create_text(
            10,
            y_offset,
            text=cursor_info,
            fill=self.text_color,
            font=("Arial", 10, "bold"),
            anchor="w",
        )

        # Draw recorded clicks info
        if self.recorded_clicks:
            y_offset += 20
            recent_clicks = self.recorded_clicks[-3:]  # Show last 3 clicks

            self.canvas.create_text(
                10,
                y_offset,
                text="Recent Clicks:",
                fill=self.text_color,
                font=("Arial", 9, "bold"),
                anchor="w",
            )

            for i, click in enumerate(recent_clicks):
                y_offset += 15
                click_text = (
                    f"  {i+1}. ({click['x']}, {click['y']}) - {click['button']}"
                )
                self.canvas.create_text(
                    10,
                    y_offset,
                    text=click_text,
                    fill=self.text_color,
                    font=("Arial", 8),
                    anchor="w",
                )

        # Draw click recording status
        if self.enable_click_recording:
            y_offset += 20
            recording_text = f"Recording: {len(self.recorded_clicks)} clicks"
            self.canvas.create_text(
                10,
                y_offset,
                text=recording_text,
                fill="#00ff00",
                font=("Arial", 9, "bold"),
                anchor="w",
            )

            # Show copy to clipboard button
            if self.recorded_clicks:
                self.canvas.create_text(
                    200,
                    y_offset,
                    text="[Copy to Clipboard]",
                    fill="#00aaff",
                    font=("Arial", 8),
                    anchor="w",
                    tags="copy_clicks",
                )

        # Schedule next update
        self.root.after(50, self.update_cursor_info)

    def update_cursor_info(self):
        """Update cursor information if tracking is enabled"""
        if self.enable_cursor_tracking and self.is_expanded:
            # Redraw to update cursor info
            self.draw_expanded()

    def copy_clicks_to_clipboard(self):
        """Copy recorded clicks to clipboard as formatted text"""
        if not self.recorded_clicks:
            return

        # Format clicks as Python code
        click_code = "# Recorded clicks:\n"
        for i, click in enumerate(self.recorded_clicks):
            click_code += (
                f"pyautogui.click({click['x']}, {click['y']})  # Click {i+1}\n"
            )

        # Copy to clipboard
        pyperclip.copy(click_code)

        # Update status temporarily
        old_detail = self.detail_text
        self.detail_text = f"Copied {len(self.recorded_clicks)} clicks to clipboard!"
        self.draw_expanded()

        # Restore original detail text after 2 seconds
        self.root.after(2000, lambda: self.set_detail_text(old_detail))

    def set_detail_text(self, text):
        """Set the detail text and refresh display"""
        self.detail_text = text
        if self.is_expanded:
            self.draw_expanded()

    def on_mouse_motion(self, event):
        """Handle mouse motion for cursor tracking"""
        if self.enable_cursor_tracking and self.is_expanded:
            # Redraw to update cursor info
            self.draw_expanded()

    def on_key_press(self, event):
        """Handle key press events"""
        if event.keysym in ["space", "Escape"] and self.automation_active:
            self.stop_automation()

    def show_activate_button(self, minigame_data):
        """Show the activate button for detected minigame"""
        if self.hide_activate_button_setting:
            return

        self.current_minigame = minigame_data

        if self.activate_button:
            # Update button state
            has_logic = minigame_data.get("has_logic", False)

            if has_logic or self.enable_disabled_buttons:
                self.activate_btn.configure(bg="#4CAF50", fg="white", state="normal")
            else:
                self.activate_btn.configure(
                    bg="#CCCCCC", fg="#666666", state="disabled"
                )

            # Show button
            self.activate_button.deiconify()

    def hide_activate_button(self):
        """Hide the activate button"""
        if self.activate_button:
            self.activate_button.withdraw()
        self.current_minigame = None

    def on_activate_clicked(self):
        """Handle activate button click"""
        if not self.current_minigame:
            return

        # Button press animation
        self.activate_btn.configure(relief="sunken")
        self.root.after(100, lambda: self.activate_btn.configure(relief="raised"))

        # Start automation
        self.start_automation()

    def start_automation(self):
        """Start automation for current minigame"""
        if not self.current_minigame:
            return

        self.automation_active = True
        self.automation_start_time = time.time()

        # Update overlay to active state
        self.update_status("ACTIVE", f"Running: {self.current_minigame['name']}")

        # Hide activate button
        self.hide_activate_button()

        # Show status overlay
        if self.status_overlay:
            self.status_overlay.deiconify()

        # Start timer update
        self.update_timer()

        # TODO: Add actual automation logic here
        print(f"Started automation for: {self.current_minigame['name']}")

    def stop_automation(self):
        """Stop automation"""
        self.automation_active = False
        self.automation_start_time = None

        # Update overlay to inactive state
        self.update_status("INACTIVE", "No minigame detected")

        # Hide status overlay
        if self.status_overlay:
            self.status_overlay.withdraw()

        print("Automation stopped")

    def update_timer(self):
        """Update the timer display"""
        if not self.automation_active or not self.automation_start_time:
            return

        elapsed = time.time() - self.automation_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        if self.timer_label:
            self.timer_label.configure(text=f"Timer: {minutes:02d}:{seconds:02d}")

        # Schedule next update
        self.root.after(1000, self.update_timer)

    def destroy(self):
        """Destroy the overlay and all components"""
        if self.activate_button:
            self.activate_button.destroy()
        if self.status_overlay:
            self.status_overlay.destroy()
        super().destroy()

    def bind_events(self):
        """Bind mouse events to the overlay"""

        def on_enter(event):
            if not self.is_pinned:
                self.start_hover_timer()

        def on_leave(event):
            if not self.is_pinned:
                self.start_collapse_timer()

        def on_click(event):
            # Check if click is within the original 40x40 collapsed area for pin toggle
            if event.x <= self.collapsed_size[0] and event.y <= self.collapsed_size[1]:
                self.toggle_pin()
            # Check if click is on a checkbox (only when expanded)
            elif self.is_expanded:
                self.handle_checkbox_click(event.x, event.y)

        # Bind to both canvas and frame
        for widget in [self.canvas, self.main_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def handle_checkbox_click(self, x, y):
        """Handle checkbox clicks and return True if a checkbox was clicked"""
        checkbox_size = 12
        y_offset = 70  # Match the y_offset from draw_expanded()

        # Check Hide Activate Button checkbox
        if 10 <= x <= 10 + checkbox_size and y_offset <= y <= y_offset + checkbox_size:
            self.hide_activate_button_setting = not self.hide_activate_button_setting
            self.draw_expanded()
            return True

        y_offset += 25  # Match the increment from draw_expanded()

        # Check Debug Mode checkbox
        if 10 <= x <= 10 + checkbox_size and y_offset <= y <= y_offset + checkbox_size:
            self.debug_mode = not self.debug_mode
            self.draw_expanded()
            return True

        y_offset += 25  # Match the increment from draw_expanded()

        # Debug mode checkboxes
        if self.debug_mode:
            checkboxes = [
                ("enable_logging", "Enable logging"),
                ("enable_on_screen_debug", "Enable on-screen debug"),
                ("enable_disabled_buttons", "Enable disabled buttons"),
                ("enable_cursor_trail", "Enable cursor trail"),
                ("enable_click_visuals", "Enable click visuals"),
                ("enable_cursor_tracking", "Enable cursor tracking"),
            ]

            for attr_name, _ in checkboxes:
                if (
                    20 <= x <= 20 + checkbox_size
                    and y_offset <= y <= y_offset + checkbox_size
                ):
                    current_value = getattr(self, attr_name)
                    setattr(self, attr_name, not current_value)
                    self.draw_expanded()
                    return True
                y_offset += 20  # Match the increment from draw_expanded()

        # Check for "Copy to Clipboard" button click
        if self.enable_cursor_tracking and self.recorded_clicks:
            # Calculate the approximate position of the copy button
            copy_button_y = y_offset + 20  # Position after cursor tracking info
            if 200 <= x <= 320 and copy_button_y <= y <= copy_button_y + 20:
                self.copy_clicks_to_clipboard()
                return True

        return False


def create_enhanced_overlay():
    """Create and return a new enhanced overlay instance"""
    return EnhancedOverlay()
