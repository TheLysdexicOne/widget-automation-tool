import tkinter as tk
from tkinter import ttk
import time
import threading
import win32gui
import win32api
from widget_inc_manager import WidgetIncManager


class WindowSpyOverlay:
    def __init__(self, debug_gui=None):
        self.debug_gui = debug_gui
        self.root = None
        self.widget_manager = WidgetIncManager()
        self.is_visible = False
        self.is_tracking = False

        # Dimensions
        self.width = 250
        self.height = 150

        # Colors
        self.bg_color = "#2C2C2C"
        self.text_color = "#FFFFFF"
        self.border_color = "#404040"

        # Mouse tracking
        self.mouse_start_pos = None
        self.mouse_start_time = None
        self.click_threshold_distance = 5  # pixels
        self.click_threshold_time = 0.5  # seconds

        # Window info
        self.window_info = {"width": 0, "height": 0}
        self.cursor_info = {"x": 0, "y": 0, "x_percent": 0.0, "y_percent": 0.0}

        self.setup_gui()

    def setup_gui(self):
        """Initialize the window spy overlay"""
        self.root = tk.Toplevel()
        self.root.title("Window Spy")

        # Make window transparent and always on top
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.overrideredirect(True)  # Remove window decorations

        # Set initial size
        self.root.geometry(f"{self.width}x{self.height}")

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, relief="solid", bd=2)
        self.main_frame.pack(fill="both", expand=True)

        # Title
        title_label = tk.Label(
            self.main_frame,
            text="Window Spy",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Arial", 10, "bold"),
        )
        title_label.pack(pady=5)

        # Info labels
        self.info_labels = {}
        info_items = [
            ("Window Size", "0 x 0"),
            ("Cursor (px)", "0, 0"),
            ("Cursor (%)", "0.0, 0.0"),
        ]

        for item, default_value in info_items:
            frame = tk.Frame(self.main_frame, bg=self.bg_color)
            frame.pack(fill="x", padx=10, pady=2)

            label = tk.Label(
                frame,
                text=f"{item}:",
                bg=self.bg_color,
                fg=self.text_color,
                font=("Arial", 8),
            )
            label.pack(side="left")

            value_label = tk.Label(
                frame,
                text=default_value,
                bg=self.bg_color,
                fg="#00FF00",
                font=("Consolas", 8),
            )
            value_label.pack(side="right")

            self.info_labels[item] = value_label

        # Status label
        self.status_label = tk.Label(
            self.main_frame,
            text="Ready",
            bg=self.bg_color,
            fg="#FFD700",
            font=("Arial", 8, "italic"),
        )
        self.status_label.pack(pady=5)

        # Initially hide the overlay
        self.root.withdraw()

    def show(self):
        """Show the window spy overlay"""
        if not self.is_visible:
            self.position_window()
            self.root.deiconify()
            self.is_visible = True
            self.start_tracking()

    def hide(self):
        """Hide the window spy overlay"""
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
            self.stop_tracking()

    def position_window(self):
        """Position the spy overlay relative to the main overlay"""
        if self.widget_manager.find_widget_inc_window():
            widget_window = self.widget_manager.window

            if widget_window:
                try:
                    # Position at bottom-right of the main overlay
                    # Main overlay is typically 32x32 at top-right
                    main_overlay_x = widget_window.left + widget_window.width - 32
                    main_overlay_y = widget_window.top + 32

                    # Position spy overlay below and to the right
                    spy_x = main_overlay_x + 32 + 10  # 10px gap
                    spy_y = main_overlay_y

                    self.root.geometry(f"{self.width}x{self.height}+{spy_x}+{spy_y}")
                    return
                except Exception as e:
                    print(f"Error positioning window spy: {e}")

        # Fallback positioning
        self.root.geometry(f"{self.width}x{self.height}+100+100")

    def start_tracking(self):
        """Start tracking mouse and window info"""
        if not self.is_tracking:
            self.is_tracking = True
            self.track_info()

    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False

    def track_info(self):
        """Track mouse and window information"""
        if not self.is_tracking:
            return

        try:
            # Get widget window info
            if self.widget_manager.find_widget_inc_window():
                widget_window = self.widget_manager.window
                if widget_window:
                    self.window_info["width"] = widget_window.width
                    self.window_info["height"] = widget_window.height

                    # Get cursor position relative to widget window
                    cursor_x, cursor_y = win32gui.GetCursorPos()
                    relative_x = cursor_x - widget_window.left
                    relative_y = cursor_y - widget_window.top

                    # Calculate percentages
                    if widget_window.width > 0 and widget_window.height > 0:
                        x_percent = (relative_x / widget_window.width) * 100
                        y_percent = (relative_y / widget_window.height) * 100
                    else:
                        x_percent = 0.0
                        y_percent = 0.0

                    self.cursor_info = {
                        "x": relative_x,
                        "y": relative_y,
                        "x_percent": x_percent,
                        "y_percent": y_percent,
                    }

                    # Update GUI
                    self.update_display()

                    # Update debug GUI if available
                    if self.debug_gui:
                        self.debug_gui.update_window_spy_info(
                            self.window_info, self.cursor_info
                        )

                    # Check for mouse actions
                    self.check_mouse_actions()

        except Exception as e:
            print(f"Error tracking info: {e}")

        # Schedule next update
        if self.is_tracking:
            self.root.after(50, self.track_info)  # 20 FPS

    def update_display(self):
        """Update the display with current information"""
        try:
            self.info_labels["Window Size"].config(
                text=f"{self.window_info['width']} x {self.window_info['height']}"
            )
            self.info_labels["Cursor (px)"].config(
                text=f"{self.cursor_info['x']}, {self.cursor_info['y']}"
            )
            self.info_labels["Cursor (%)"].config(
                text=f"{self.cursor_info['x_percent']:.1f}, {self.cursor_info['y_percent']:.1f}"
            )
        except Exception as e:
            print(f"Error updating display: {e}")

    def check_mouse_actions(self):
        """Check for mouse click/drag actions"""
        try:
            # Check if left mouse button is pressed
            left_button_state = win32api.GetKeyState(0x01)
            is_pressed = left_button_state < 0

            if is_pressed:
                if self.mouse_start_pos is None:
                    # Mouse button just pressed
                    self.mouse_start_pos = (
                        self.cursor_info["x"],
                        self.cursor_info["y"],
                    )
                    self.mouse_start_time = time.time()
                    self.status_label.config(text="Tracking...")
            else:
                if self.mouse_start_pos is not None:
                    # Mouse button just released
                    end_pos = (self.cursor_info["x"], self.cursor_info["y"])
                    end_time = time.time()

                    # Calculate distance and time
                    distance = (
                        (end_pos[0] - self.mouse_start_pos[0]) ** 2
                        + (end_pos[1] - self.mouse_start_pos[1]) ** 2
                    ) ** 0.5
                    duration = end_time - self.mouse_start_time

                    # Determine if it's a click or drag
                    if (
                        distance < self.click_threshold_distance
                        and duration < self.click_threshold_time
                    ):
                        # It's a click
                        self.record_click(end_pos)
                    else:
                        # It's a drag
                        self.record_drag(self.mouse_start_pos, end_pos)

                    # Reset tracking
                    self.mouse_start_pos = None
                    self.mouse_start_time = None
                    self.status_label.config(text="Ready")

        except Exception as e:
            print(f"Error checking mouse actions: {e}")

    def record_click(self, pos):
        """Record a click action"""
        try:
            if self.window_info["width"] > 0 and self.window_info["height"] > 0:
                x_percent = (pos[0] / self.window_info["width"]) * 100
                y_percent = (pos[1] / self.window_info["height"]) * 100

                action = {
                    "type": "click",
                    "x": pos[0],
                    "y": pos[1],
                    "x_percent": x_percent,
                    "y_percent": y_percent,
                    "timestamp": time.time(),
                }

                # Add to debug GUI
                if self.debug_gui:
                    self.debug_gui.add_action(action)

                self.status_label.config(text="Click recorded!")
                self.root.after(1000, lambda: self.status_label.config(text="Ready"))

        except Exception as e:
            print(f"Error recording click: {e}")

    def record_drag(self, start_pos, end_pos):
        """Record a drag action"""
        try:
            if self.window_info["width"] > 0 and self.window_info["height"] > 0:
                x1_percent = (start_pos[0] / self.window_info["width"]) * 100
                y1_percent = (start_pos[1] / self.window_info["height"]) * 100
                x2_percent = (end_pos[0] / self.window_info["width"]) * 100
                y2_percent = (end_pos[1] / self.window_info["height"]) * 100

                action = {
                    "type": "drag",
                    "x1": start_pos[0],
                    "y1": start_pos[1],
                    "x2": end_pos[0],
                    "y2": end_pos[1],
                    "x1_percent": x1_percent,
                    "y1_percent": y1_percent,
                    "x2_percent": x2_percent,
                    "y2_percent": y2_percent,
                    "timestamp": time.time(),
                }

                # Add to debug GUI
                if self.debug_gui:
                    self.debug_gui.add_action(action)

                self.status_label.config(text="Drag recorded!")
                self.root.after(1000, lambda: self.status_label.config(text="Ready"))

        except Exception as e:
            print(f"Error recording drag: {e}")

    def destroy(self):
        """Destroy the window spy overlay"""
        self.stop_tracking()
        if self.root:
            self.root.destroy()
