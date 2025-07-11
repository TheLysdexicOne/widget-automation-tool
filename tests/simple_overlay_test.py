#!/usr/bin/env python3
"""
Simple standalone test for the overlay GUI
This version doesn't require WidgetInc to be running
"""

import tkinter as tk
from tkinter import ttk
import time
import threading


class SimpleOverlayTest:
    def __init__(self):
        self.root = None
        self.is_expanded = False
        self.is_pinned = False
        self.hover_timer = None
        self.collapse_timer = None

        # GUI state
        self.status_text = "INACTIVE"
        self.detail_text = "No minigame detected"

        # Dimensions
        self.collapsed_size = (32, 32)
        self.circle_size = (24, 24)
        self.expanded_width = 200
        self.expanded_height = 80

        # Colors
        self.bg_color = "#2C2C2C"
        self.circle_color = "#FF4444"
        self.text_color = "#FFFFFF"
        self.pin_color = "#FFD700"

        self.setup_gui()

    def setup_gui(self):
        """Initialize the overlay GUI"""
        self.root = tk.Tk()
        self.root.title("Widget Automation Overlay Test")

        # Make window transparent and always on top
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.overrideredirect(True)  # Remove window decorations

        # Position in top-right corner
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - self.collapsed_size[0] - 50
        y = 50
        self.root.geometry(f"{self.collapsed_size[0]}x{self.collapsed_size[1]}+{x}+{y}")

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, relief="solid", bd=1)
        self.main_frame.pack(fill="both", expand=True)

        # Create canvas for custom drawing
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=self.bg_color,
            highlightthickness=0,
            width=self.collapsed_size[0],
            height=self.collapsed_size[1],
        )
        self.canvas.pack()

        # Bind events
        self.bind_events()

        # Draw initial state
        self.draw_collapsed()

    def bind_events(self):
        """Bind mouse events to the overlay"""

        def on_enter(event):
            if not self.is_pinned:
                self.start_hover_timer()

        def on_leave(event):
            if not self.is_pinned:
                self.start_collapse_timer()

        def on_click(event):
            self.toggle_pin()

        # Bind to both canvas and frame
        for widget in [self.canvas, self.main_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def start_hover_timer(self):
        """Start timer for hover expansion"""
        if self.hover_timer:
            self.hover_timer.cancel()

        if self.collapse_timer:
            self.collapse_timer.cancel()
            self.collapse_timer = None

        self.hover_timer = threading.Timer(0.25, self.expand_overlay)
        self.hover_timer.start()

    def start_collapse_timer(self):
        """Start timer for collapse"""
        if self.hover_timer:
            self.hover_timer.cancel()
            self.hover_timer = None

        if self.collapse_timer:
            self.collapse_timer.cancel()

        self.collapse_timer = threading.Timer(0.5, self.collapse_overlay)
        self.collapse_timer.start()

    def expand_overlay(self):
        """Expand the overlay to show status"""
        if not self.is_expanded:
            self.is_expanded = True

            # Calculate new position - expand to the left
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()

            # New X position: move left by the difference in width
            new_x = current_x - (self.expanded_width - self.collapsed_size[0])

            # Resize and reposition window
            self.root.geometry(
                f"{self.expanded_width}x{self.expanded_height}+{new_x}+{current_y}"
            )
            self.canvas.configure(
                width=self.expanded_width, height=self.expanded_height
            )

            # Redraw expanded view
            self.draw_expanded()

    def collapse_overlay(self):
        """Collapse the overlay to minimal size"""
        if self.is_expanded and not self.is_pinned:
            self.is_expanded = False

            # Calculate original position - move back to the right
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()

            # New X position: move right by the difference in width
            new_x = current_x + (self.expanded_width - self.collapsed_size[0])

            # Resize and reposition window
            self.root.geometry(
                f"{self.collapsed_size[0]}x{self.collapsed_size[1]}+{new_x}+{current_y}"
            )
            self.canvas.configure(
                width=self.collapsed_size[0], height=self.collapsed_size[1]
            )

            # Redraw collapsed view
            self.draw_collapsed()

    def toggle_pin(self):
        """Toggle the pinned state"""
        self.is_pinned = not self.is_pinned

        if self.is_pinned:
            self.expand_overlay()

        # Redraw to show/hide pin icon
        if self.is_expanded:
            self.draw_expanded()

    def draw_collapsed(self):
        """Draw the collapsed state (just the red circle)"""
        self.canvas.delete("all")

        # Draw background square
        self.canvas.create_rectangle(
            0,
            0,
            self.collapsed_size[0],
            self.collapsed_size[1],
            fill=self.bg_color,
            outline=self.bg_color,
        )

        # Draw red circle (centered)
        circle_x = (self.collapsed_size[0] - self.circle_size[0]) // 2
        circle_y = (self.collapsed_size[1] - self.circle_size[1]) // 2

        self.canvas.create_oval(
            circle_x,
            circle_y,
            circle_x + self.circle_size[0],
            circle_y + self.circle_size[1],
            fill=self.circle_color,
            outline=self.circle_color,
        )

    def draw_expanded(self):
        """Draw the expanded state with text"""
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

        # Draw red circle (top-right)
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
        if self.is_pinned:
            pin_x = 10
            pin_y = 10
            self.draw_pin_icon(pin_x, pin_y)
            text_x = 30
        else:
            text_x = 10

        # Draw status text
        self.canvas.create_text(
            text_x,
            15,
            text=self.status_text,
            fill=self.text_color,
            font=("Arial", 10, "bold"),
            anchor="w",
        )

        # Draw detail text
        self.canvas.create_text(
            text_x,
            35,
            text=self.detail_text,
            fill=self.text_color,
            font=("Arial", 8),
            anchor="w",
        )

    def draw_pin_icon(self, x, y):
        """Draw a simple pin/lock icon"""
        # Simple pin icon (golden color)
        self.canvas.create_oval(
            x, y, x + 8, y + 8, fill=self.pin_color, outline=self.pin_color
        )
        self.canvas.create_rectangle(
            x + 2, y + 6, x + 6, y + 12, fill=self.pin_color, outline=self.pin_color
        )

    def update_status(self, status_text, detail_text=None):
        """Update the status and detail text"""
        self.status_text = status_text
        if detail_text:
            self.detail_text = detail_text

        # Update circle color based on status
        if "ACTIVE" in status_text.upper():
            self.circle_color = "#44FF44"  # Green for active
        elif "INACTIVE" in status_text.upper():
            self.circle_color = "#FF4444"  # Red for inactive
        elif "ERROR" in status_text.upper():
            self.circle_color = "#FFAA00"  # Orange for error
        elif "WAITING" in status_text.upper():
            self.circle_color = "#4444FF"  # Blue for waiting
        elif "STARTING" in status_text.upper():
            self.circle_color = "#FF44FF"  # Purple for starting

        # Redraw
        if self.is_expanded:
            self.draw_expanded()
        else:
            self.draw_collapsed()

    def run(self):
        """Run the overlay"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nSimple overlay test interrupted")
        finally:
            if self.root:
                self.root.destroy()


def main():
    print("Simple Overlay Test")
    print("=" * 30)
    print("Features to test:")
    print("- Hover over the red circle (wait 0.25s)")
    print("- Move mouse away to collapse (wait 0.5s)")
    print("- Click to pin/unpin")
    print("- Watch status changes")
    print("- Press Ctrl+C or close window to exit")
    print()

    overlay = SimpleOverlayTest()

    # Flag to control the test
    test_running = True

    # Test status cycling
    def cycle_states():
        states = [
            ("STARTING", "Initializing..."),
            ("WAITING", "Looking for WidgetInc..."),
            ("INACTIVE", "No minigame detected"),
            ("ACTIVE", "Running: Test Game"),
            ("ERROR", "Test error message"),
            ("INACTIVE", "Test complete"),
        ]

        time.sleep(2)  # Wait for GUI to appear

        state_index = 0
        while test_running:
            status, detail = states[state_index]
            overlay.update_status(status, detail)
            state_index = (state_index + 1) % len(states)

            # Sleep in small chunks to be responsive to interrupts
            for _ in range(30):  # 3 seconds total
                if not test_running:
                    break
                time.sleep(0.1)

    def stop_test():
        """Stop the test"""
        nonlocal test_running
        test_running = False
        overlay.root.quit()

    # Handle window close event
    overlay.root.protocol("WM_DELETE_WINDOW", stop_test)

    # Start cycling in background
    threading.Thread(target=cycle_states, daemon=True).start()

    # Run the overlay
    try:
        overlay.run()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        test_running = False


if __name__ == "__main__":
    main()
