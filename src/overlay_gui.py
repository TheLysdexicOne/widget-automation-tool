import tkinter as tk
from tkinter import ttk
import time
import threading
from widget_inc_manager import WidgetIncManager


class OverlayGUI:
    def __init__(self):
        self.root = None
        self.widget_manager = WidgetIncManager()
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
        self.root = tk.Toplevel()
        self.root.title("Widget Automation Overlay")

        # Make window transparent and always on top
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.overrideredirect(True)  # Remove window decorations

        # Set initial size and position
        self.position_window()

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

        # Start position monitoring
        self.monitor_position()

    def position_window(self):
        """Position the overlay window relative to WidgetInc"""
        if self.widget_manager.find_widget_inc_window():
            widget_window = self.widget_manager.window

            if widget_window:
                try:
                    # Position on right side of WidgetInc window, offset from top
                    x = (
                        widget_window.left
                        + widget_window.width
                        - self.collapsed_size[0]
                        - 10
                    )
                    y = widget_window.top + 64  # Offset for header bar + 32px

                    self.root.geometry(
                        f"{self.collapsed_size[0]}x{self.collapsed_size[1]}+{x}+{y}"
                    )
                    return
                except Exception as e:
                    print(f"Error positioning overlay: {e}")

        # Fallback to screen position (top-right corner)
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - self.collapsed_size[0] - 50
        y = 50
        self.root.geometry(f"{self.collapsed_size[0]}x{self.collapsed_size[1]}+{x}+{y}")

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
        status_upper = status_text.upper()
        if status_upper == "ACTIVE":
            self.circle_color = "#44FF44"  # Green for active
        elif status_upper == "INACTIVE":
            self.circle_color = "#FF4444"  # Red for inactive
        elif "ERROR" in status_upper:
            self.circle_color = "#FFAA00"  # Orange for error
        elif "WAITING" in status_upper:
            self.circle_color = "#4444FF"  # Blue for waiting
        elif "STARTING" in status_upper:
            self.circle_color = "#FF44FF"  # Purple for starting
        else:
            self.circle_color = "#CCCCCC"  # Gray for unknown states

        # Redraw in current state
        if self.is_expanded:
            self.draw_expanded()
        else:
            self.draw_collapsed()

    def monitor_position(self):
        """Monitor WidgetInc window position and update overlay position"""

        def check_position():
            try:
                # Store the original window reference to avoid re-detecting
                if not hasattr(self, "_target_window") or self._target_window is None:
                    # Only search for WidgetInc on first run or if we lost the window
                    if self.widget_manager.find_widget_inc_window():
                        self._target_window = self.widget_manager.window
                    else:
                        return

                # Check if our stored window is still valid
                widget_window = self._target_window
                if widget_window:
                    try:
                        # Test if window is still valid by accessing its properties
                        _ = widget_window.left
                        _ = widget_window.top
                        _ = widget_window.width
                        _ = widget_window.height
                    except:
                        # Window is no longer valid, clear reference
                        self._target_window = None
                        return

                    # Calculate new position for collapsed state (right-aligned)
                    new_x = (
                        widget_window.left
                        + widget_window.width
                        - self.collapsed_size[0]
                        - 10
                    )
                    new_y = widget_window.top + 64

                    # If expanded, adjust x position to expand left
                    if self.is_expanded:
                        new_x = new_x - (self.expanded_width - self.collapsed_size[0])

                    # Update position if significantly different
                    if (
                        abs(new_x - self.root.winfo_x()) > 10
                        or abs(new_y - self.root.winfo_y()) > 10
                    ):
                        width = (
                            self.expanded_width
                            if self.is_expanded
                            else self.collapsed_size[0]
                        )
                        height = (
                            self.expanded_height
                            if self.is_expanded
                            else self.collapsed_size[1]
                        )
                        self.root.geometry(f"{width}x{height}+{new_x}+{new_y}")

            except Exception as e:
                # Clear the stored window reference on error
                self._target_window = None
                # Silently ignore errors when WidgetInc isn't running (for testing)
                pass

            # Schedule next check
            self.root.after(1000, check_position)

        # Initialize target window reference
        self._target_window = None

        # Start monitoring
        self.root.after(1000, check_position)

    def show(self):
        """Show the overlay"""
        if self.root:
            self.root.deiconify()

    def hide(self):
        """Hide the overlay"""
        if self.root:
            self.root.withdraw()

    def destroy(self):
        """Destroy the overlay"""
        if self.hover_timer:
            self.hover_timer.cancel()
        if self.collapse_timer:
            self.collapse_timer.cancel()
        if self.root:
            self.root.destroy()


def create_overlay():
    """Create and return a new overlay instance"""
    return OverlayGUI()


if __name__ == "__main__":
    # Test the overlay
    root = tk.Tk()
    root.withdraw()  # Hide main window

    overlay = create_overlay()
    overlay.show()

    # Test status updates
    def test_updates():
        import time

        time.sleep(3)
        overlay.update_status("ACTIVE", "Clicker game detected")
        time.sleep(3)
        overlay.update_status("ERROR", "Connection lost")
        time.sleep(3)
        overlay.update_status("INACTIVE", "No minigame detected")

    # Start test in background
    threading.Thread(target=test_updates, daemon=True).start()

    root.mainloop()
