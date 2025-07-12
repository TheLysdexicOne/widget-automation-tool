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

        # Threading-safe flags for state changes
        self.should_expand = False
        self.should_collapse = False

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

        # Cycle through startup states
        self.cycle_startup_states()

        # Start flag checking for thread-safe updates
        self.check_state_flags()

    def position_window(self):
        """Position the overlay window relative to WidgetInc"""
        if self.widget_manager.find_widget_inc_window():
            widget_window = self.widget_manager.window

            if widget_window:
                try:
                    # Position perfectly aligned to top-right, down 32px from title bar
                    # Account for window borders/decorations
                    x = (
                        widget_window.left
                        + widget_window.width
                        - self.collapsed_size[0]
                    )
                    y = widget_window.top + 32  # Just below title bar

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
            # Make the entire overlay clickable for pin/unpin
            self.toggle_pin()

        def on_right_click(event):
            print(f"Right-click handler called: {event}")
            # Show context menu anywhere on the overlay
            self.show_context_menu(event)

        # Bind to canvas, frame, and root window
        for widget in [self.canvas, self.main_frame, self.root]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
            widget.bind("<Button-3>", on_right_click)  # Right click

    def start_hover_timer(self):
        """Start timer for hover expansion"""
        if self.hover_timer:
            self.hover_timer.cancel()

        if self.collapse_timer:
            self.collapse_timer.cancel()
            self.collapse_timer = None

        self.hover_timer = threading.Timer(0.25, self.set_expand_flag)
        self.hover_timer.start()

    def start_collapse_timer(self):
        """Start timer for collapse"""
        if self.hover_timer:
            self.hover_timer.cancel()
            self.hover_timer = None

        if self.collapse_timer:
            self.collapse_timer.cancel()

        self.collapse_timer = threading.Timer(0.5, self.set_collapse_flag)
        self.collapse_timer.start()

    def set_expand_flag(self):
        """Set flag to expand overlay (called from timer thread)"""
        self.should_expand = True

    def set_collapse_flag(self):
        """Set flag to collapse overlay (called from timer thread)"""
        self.should_collapse = True

    def expand_overlay(self):
        """Expand the overlay to show status"""
        if not self.is_expanded:
            self.is_expanded = True
            try:
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
            except Exception as e:
                print(f"Error expanding overlay: {e}")

    def collapse_overlay(self):
        """Collapse the overlay to minimal size"""
        if self.is_expanded and not self.is_pinned:
            self.is_expanded = False
            try:
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
            except Exception as e:
                print(f"Error collapsing overlay: {e}")

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

    def update_status(self, status, detail=""):
        """Update the overlay status"""
        self.status_text = status
        self.detail_text = detail

        # Update color based on status
        if status == "ACTIVE":
            self.circle_color = "#00FF00"  # Green
        elif status == "WAITING":
            self.circle_color = "#FFD700"  # Gold
        elif status == "ERROR":
            self.circle_color = "#FF0000"  # Red
        elif status == "RELOADED":
            self.circle_color = "#00FFFF"  # Cyan
        else:
            self.circle_color = "#FF4444"  # Default red

        # Redraw based on current state
        if self.is_expanded:
            self.draw_expanded()
        else:
            self.draw_collapsed()

    def show_activate_button(self, minigame):
        """Show activate button for detected minigame"""
        # For now, just update status - activate button functionality can be added later
        self.update_status("WAITING", f"Ready: {minigame.get('name', 'Unknown')}")

    def hide_activate_button(self):
        """Hide activate button"""
        self.update_status("INACTIVE", "No minigame detected")

    def show(self):
        """Show the overlay"""
        if self.root:
            self.root.deiconify()
            self.root.lift()

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

    def show_context_menu(self, event):
        """Show right-click context menu"""
        try:
            print(f"Right-click detected at {event.x_root}, {event.y_root}")

            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="Show Debug Console", command=self.show_debug_console
            )
            context_menu.add_separator()
            context_menu.add_command(label="Close", command=self.destroy)

            # Show menu at cursor position
            context_menu.tk_popup(event.x_root, event.y_root)
            print("Context menu shown")
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def show_debug_console(self):
        """Show debug console from overlay"""
        try:
            # Try to access debug GUI through widget manager's main app
            if (
                hasattr(self.widget_manager, "main_app")
                and self.widget_manager.main_app
            ):
                main_app = self.widget_manager.main_app
                if hasattr(main_app, "debug_gui") and main_app.debug_gui:
                    main_app.debug_gui.root.deiconify()
                    main_app.debug_gui.root.lift()
                    main_app.debug_gui.root.focus_force()
                    return

            # Alternative: try to find main app through global reference
            # This would need to be set when overlay is created
            print("Debug console access not available from overlay")
        except Exception as e:
            print(f"Error showing debug console: {e}")

    def cycle_startup_states(self):
        """Cycle through all available states on startup"""

        def cycle_states():
            states = [
                ("STARTING", "Initializing..."),
                ("SEARCHING", "Looking for WidgetInc..."),
                ("READY", "WidgetInc found"),
                ("ACTIVE", "Game detected"),
                ("WAITING", "Ready for automation"),
                ("INACTIVE", "No minigame detected"),
            ]

            # Start expanded for better visibility
            if not self.is_expanded:
                self.expand_overlay()

            # Cycle through states with delays
            for i, (status, detail) in enumerate(states):

                def update_state(s=status, d=detail):
                    self.update_status(s, d)

                self.root.after(i * 1000, update_state)  # 1 second intervals

            # Return to appropriate final state after cycling
            def final_state():
                self.update_status("INACTIVE", "No minigame detected")
                if not self.is_pinned:
                    self.collapse_overlay()

            self.root.after(len(states) * 1000 + 500, final_state)

        # Start cycling after a short delay
        self.root.after(500, cycle_states)

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

    def check_state_flags(self):
        """Check and process state change flags (call from main thread)"""
        if self.should_expand:
            self.should_expand = False
            self.expand_overlay()

        if self.should_collapse:
            self.should_collapse = False
            self.collapse_overlay()

        # Schedule next check
        if self.root:
            self.root.after(50, self.check_state_flags)  # Check every 50ms


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
