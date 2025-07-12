#!/usr/bin/env python3
"""
Simplified Enhanced Overlay - Debug options moved to Debug GUI
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
import pyperclip
from overlay_gui import OverlayGUI
from widget_inc_manager import WidgetIncManager


class SimplifiedOverlay(OverlayGUI):
    def __init__(self):
        # Basic settings (debug options moved to Debug GUI)
        self.hide_activate_button_setting = False

        # State
        self.current_minigame = None
        self.automation_active = False
        self.automation_start_time = None
        self.activate_button = None
        self.status_overlay = None

        # Initialize parent
        super().__init__()

        # Override dimensions for cleaner overlay
        self.collapsed_size = (40, 40)
        self.circle_size = (30, 30)
        self.expanded_width = 250
        self.expanded_height = 100

    def setup_gui(self):
        """Initialize the simplified overlay GUI"""
        super().setup_gui()

        # Create activate button (initially hidden)
        self.create_activate_button()

        # Create status overlay for active state
        self.create_status_overlay()

    def draw_expanded(self):
        """Draw the expanded state - simplified version"""
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

        # Simple settings
        y_offset = 65

        # Hide Activate Button checkbox
        self.draw_checkbox(
            10, y_offset, "Hide Activate Button", self.hide_activate_button_setting
        )

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
            # Check if click is on the checkbox (only when expanded)
            elif self.is_expanded:
                self.handle_checkbox_click(event.x, event.y)

        # Bind to both canvas and frame
        for widget in [self.canvas, self.main_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def handle_checkbox_click(self, x, y):
        """Handle checkbox clicks - simplified version"""
        checkbox_size = 12
        y_offset = 65

        # Check Hide Activate Button checkbox
        if 10 <= x <= 10 + checkbox_size and y_offset <= y <= y_offset + checkbox_size:
            self.hide_activate_button_setting = not self.hide_activate_button_setting
            self.draw_expanded()
            return True

        return False

    # ... rest of the methods remain the same as enhanced_overlay.py ...
    # (create_activate_button, create_status_overlay, show_activate_button, etc.)

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

    def show_activate_button(self, minigame_data):
        """Show the activate button for detected minigame"""
        if self.hide_activate_button_setting:
            return

        self.current_minigame = minigame_data

        if self.activate_button:
            # Update button state
            has_logic = minigame_data.get("has_logic", False)
            self.activate_btn.configure(bg="#4CAF50", fg="white", state="normal")

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

    def on_key_press(self, event):
        """Handle key press events"""
        if event.keysym in ["space", "Escape"] and self.automation_active:
            self.stop_automation()

    def destroy(self):
        """Destroy the overlay and all components"""
        if self.activate_button:
            self.activate_button.destroy()
        if self.status_overlay:
            self.status_overlay.destroy()
        super().destroy()


def create_simplified_overlay():
    """Create and return a new simplified overlay instance"""
    return SimplifiedOverlay()


if __name__ == "__main__":
    # Test the simplified overlay
    overlay = create_simplified_overlay()
    overlay.run()
