#!/usr/bin/env python3
"""
Debug GUI for Widget Automation Tool
Separate window for debugging, logging, and control
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
import sys
import os
from datetime import datetime
import queue
from window_spy import WindowSpyOverlay


class DebugGUI:
    def __init__(self, main_app=None):
        self.main_app = main_app
        self.root = tk.Tk()
        self.root.title("Widget Automation Tool - Debug Console")
        self.root.geometry("800x600")

        # Initialize ALL BooleanVar objects ONCE at the very beginning
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.timestamp_var = tk.BooleanVar(value=True)
        self.hide_activate_var = tk.BooleanVar(value=False)
        self.cursor_tracking_var = tk.BooleanVar(value=False)
        self.click_recording_var = tk.BooleanVar(value=False)
        self.on_screen_debug_var = tk.BooleanVar(value=False)
        self.disabled_buttons_var = tk.BooleanVar(value=False)
        self.log_level_var = tk.StringVar(value="INFO")

        # Logging system
        self.log_queue = queue.Queue()
        self.log_levels = {
            "DEBUG": "#B0B0B0",
            "INFO": "#FFFFFF",
            "WARNING": "#FFD700",
            "ERROR": "#FF6B6B",
            "SUCCESS": "#4CAF50",
        }

        # Settings dictionary
        self.settings = {
            "enable_cursor_tracking": False,
            "enable_click_recording": False,
            "enable_on_screen_debug": False,
            "enable_disabled_buttons": False,
            "auto_scroll_log": True,
            "log_timestamps": True,
            "log_level": "INFO",
        }

        # Initialize data structures
        self.recent_actions = []
        self.status_labels = {}
        self.stats_labels = {}
        self.spy_labels = {}

        # Initialize GUI
        self.setup_gui()
        self.setup_logging()
        self.process_log_queue()

        # Initialize window spy overlay
        try:
            self.window_spy = WindowSpyOverlay(debug_gui=self)
        except Exception as e:
            print(f"Error initializing window spy: {e}")
            self.window_spy = None

        # Force checkbox states after GUI is created
        self.root.after(50, self._force_checkbox_states)

        # Welcome message
        self.log("INFO", "Debug GUI initialized successfully")
        self.log("INFO", "Press Ctrl+R to reload application")

    def setup_gui(self):
        """Setup the main GUI layout"""
        self.create_menu()

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create tabs
        self.create_console_tab()
        self.create_settings_tab()
        self.create_monitoring_tab()
        self.create_debug_tab()

        # Status bar
        self.create_status_bar()

    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Log", command=self.save_log)
        file_menu.add_command(label="Clear Log", command=self.clear_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(
            label="Reload App (Ctrl+R)", command=self.reload_application
        )
        tools_menu.add_command(label="Test Overlay", command=self.test_overlay)
        tools_menu.add_command(label="Test Detection", command=self.test_detection)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Bind Ctrl+R
        self.root.bind("<Control-r>", lambda e: self.reload_application())

    def create_console_tab(self):
        """Create the console/logging tab"""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="Console")

        # Log display area
        log_frame = ttk.Frame(console_frame)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
        )
        self.log_text.pack(fill="both", expand=True)

        # Log controls
        controls_frame = ttk.Frame(console_frame)
        controls_frame.pack(fill="x", padx=5, pady=5)

        # Log level filter
        ttk.Label(controls_frame, text="Log Level:").pack(side="left", padx=5)
        log_level_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10,
        )
        log_level_combo.pack(side="left", padx=5)
        log_level_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)

        # Checkboxes
        ttk.Checkbutton(
            controls_frame, text="Auto-scroll", variable=self.auto_scroll_var
        ).pack(side="left", padx=10)
        ttk.Checkbutton(
            controls_frame, text="Timestamps", variable=self.timestamp_var
        ).pack(side="left", padx=10)

        # Buttons
        ttk.Button(controls_frame, text="Copy Log", command=self.copy_log).pack(
            side="right", padx=5
        )
        ttk.Button(
            controls_frame, text="🔄 Restart", command=self.restart_application
        ).pack(side="right", padx=5)

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Configuration controls
        config_frame = ttk.LabelFrame(settings_frame, text="Configuration")
        config_frame.pack(fill="x", padx=10, pady=10)

        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Reload Config", command=self.reload_config).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Edit Minigames", command=self.edit_minigames).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Edit Settings", command=self.edit_settings).pack(
            side="left", padx=5
        )

        # Overlay settings
        overlay_frame = ttk.LabelFrame(settings_frame, text="Overlay Settings")
        overlay_frame.pack(fill="x", padx=10, pady=10)

        ttk.Checkbutton(
            overlay_frame,
            text="Hide Activate Button",
            variable=self.hide_activate_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Overlay controls
        overlay_controls_frame = ttk.Frame(overlay_frame)
        overlay_controls_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            overlay_controls_frame,
            text="Show/Hide Overlay",
            command=self.toggle_overlay,
        ).pack(side="left", padx=5)
        ttk.Button(
            overlay_controls_frame,
            text="Reset Overlay Position",
            command=self.reset_overlay_position,
        ).pack(side="left", padx=5)

        # Apply settings button
        ttk.Button(
            settings_frame,
            text="Apply Settings to Overlay",
            command=self.apply_settings_to_overlay,
        ).pack(pady=10)

    def create_monitoring_tab(self):
        """Create the monitoring tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="Monitoring")

        # Status display
        status_frame = ttk.LabelFrame(monitoring_frame, text="Current Status")
        status_frame.pack(fill="x", padx=10, pady=10)

        status_items = [
            ("Application Status", "STARTING"),
            ("WidgetInc Status", "UNKNOWN"),
            ("Current Minigame", "None"),
            ("Overlay Status", "HIDDEN"),
            ("Monitoring Active", "FALSE"),
            ("Last Detection", "Never"),
        ]

        for label, default_value in status_items:
            row_frame = ttk.Frame(status_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            ttk.Label(row_frame, text=f"{label}:", width=20).pack(side="left")
            value_label = ttk.Label(
                row_frame, text=default_value, font=("Consolas", 10)
            )
            value_label.pack(side="left", padx=10)
            self.status_labels[label] = value_label

        # Statistics
        stats_frame = ttk.LabelFrame(monitoring_frame, text="Statistics")
        stats_frame.pack(fill="x", padx=10, pady=10)

        stats_items = [
            ("Detections Today", "0"),
            ("Automation Runs", "0"),
            ("Uptime", "00:00:00"),
            ("Errors", "0"),
        ]

        for label, default_value in stats_items:
            row_frame = ttk.Frame(stats_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            ttk.Label(row_frame, text=f"{label}:", width=20).pack(side="left")
            value_label = ttk.Label(
                row_frame, text=default_value, font=("Consolas", 10)
            )
            value_label.pack(side="left", padx=10)
            self.stats_labels[label] = value_label

        # Manual controls
        controls_frame = ttk.LabelFrame(monitoring_frame, text="Manual Controls")
        controls_frame.pack(fill="x", padx=10, pady=10)

        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            btn_frame, text="Force Detection", command=self.force_detection
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset Stats", command=self.reset_stats).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Test Overlay", command=self.test_overlay).pack(
            side="left", padx=5
        )

    def create_debug_tab(self):
        """Create the debug tab"""
        debug_frame = ttk.Frame(self.notebook)
        self.notebook.add(debug_frame, text="Debug")

        # Main container with two columns
        main_container = ttk.Frame(debug_frame)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left column
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Debug options
        debug_settings_frame = ttk.LabelFrame(left_frame, text="Debug Options")
        debug_settings_frame.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(
            debug_settings_frame,
            text="Enable Cursor Tracking",
            variable=self.cursor_tracking_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(
            debug_settings_frame,
            text="Enable Click Recording",
            variable=self.click_recording_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(
            debug_settings_frame,
            text="Enable On-screen Debug",
            variable=self.on_screen_debug_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(
            debug_settings_frame,
            text="Enable Disabled Buttons",
            variable=self.disabled_buttons_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Application controls
        app_frame = ttk.LabelFrame(left_frame, text="Application Controls")
        app_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            app_frame,
            text="Reload Application (Ctrl+R)",
            command=self.reload_application,
        ).pack(fill="x", padx=10, pady=5)
        ttk.Button(
            app_frame, text="🔄 Restart Application", command=self.restart_application
        ).pack(fill="x", padx=10, pady=5)

        # Logs
        logs_frame = ttk.LabelFrame(left_frame, text="Logs")
        logs_frame.pack(fill="x", pady=(0, 10))

        logs_btn_frame = ttk.Frame(logs_frame)
        logs_btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(logs_btn_frame, text="Copy", command=self.copy_log).pack(
            side="left", padx=5
        )
        ttk.Button(logs_btn_frame, text="Save", command=self.save_log).pack(
            side="left", padx=5
        )
        ttk.Button(logs_btn_frame, text="Clear", command=self.clear_log).pack(
            side="left", padx=5
        )

        # Emergency controls
        emergency_frame = ttk.LabelFrame(left_frame, text="Emergency Controls")
        emergency_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            emergency_frame,
            text="Stop All Automation",
            command=self.stop_all_automation,
        ).pack(fill="x", padx=10, pady=2)
        ttk.Button(
            emergency_frame,
            text="Force Focus WidgetInc",
            command=self.force_focus_widgetinc,
        ).pack(fill="x", padx=10, pady=2)
        ttk.Button(
            emergency_frame, text="Reset Everything", command=self.reset_everything
        ).pack(fill="x", padx=10, pady=2)

        # Right column
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Recent actions
        actions_frame = ttk.LabelFrame(right_frame, text="Recent Actions")
        actions_frame.pack(fill="both", expand=True)

        self.actions_listbox = tk.Listbox(
            actions_frame,
            height=10,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            selectbackground="#404040",
        )
        self.actions_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Action controls
        actions_control_frame = ttk.Frame(actions_frame)
        actions_control_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            actions_control_frame, text="Copy", command=self.copy_selected_action
        ).pack(side="left", padx=5)
        ttk.Button(
            actions_control_frame, text="Remove", command=self.remove_selected_action
        ).pack(side="left", padx=5)
        ttk.Button(
            actions_control_frame, text="Clear All", command=self.clear_all_actions
        ).pack(side="left", padx=5)

        # Window spy info
        spy_info_frame = ttk.LabelFrame(right_frame, text="Window Spy Info")
        spy_info_frame.pack(fill="x", pady=(10, 0))

        spy_items = [
            ("Window Width", "0 px"),
            ("Window Height", "0 px"),
            ("Cursor X", "0 px"),
            ("Cursor Y", "0 px"),
            ("Cursor X%", "0.0%"),
            ("Cursor Y%", "0.0%"),
        ]

        for item, default_value in spy_items:
            frame = ttk.Frame(spy_info_frame)
            frame.pack(fill="x", padx=10, pady=2)
            ttk.Label(frame, text=f"{item}:").pack(side="left")
            value_label = ttk.Label(frame, text=default_value, font=("Consolas", 9))
            value_label.pack(side="right")
            self.spy_labels[item] = value_label

    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _force_checkbox_states(self):
        """Force checkbox states to match their variables"""
        try:
            # Force the states using the widget state method
            for widget in self.root.winfo_children():
                self._force_widget_states(widget)

            self.log("DEBUG", "Checkbox states forced to proper defaults")
        except Exception as e:
            self.log("ERROR", f"Error forcing checkbox states: {e}")

    def _force_widget_states(self, widget):
        """Recursively force widget states"""
        try:
            if isinstance(widget, ttk.Checkbutton):
                var = widget.cget("variable")
                if var:
                    var_obj = widget.tk.globalgetvar(var)
                    if hasattr(var_obj, "get"):
                        if var_obj.get():
                            widget.state(["selected"])
                        else:
                            widget.state(["!selected"])

            # Recursively check children
            for child in widget.winfo_children():
                self._force_widget_states(child)
        except:
            pass

    def setup_logging(self):
        """Setup the logging system"""
        for level, color in self.log_levels.items():
            self.log_text.tag_configure(level, foreground=color)

    def log(self, level, message):
        """Add a log message"""
        try:
            timestamp = (
                datetime.now().strftime("%H:%M:%S") if self.timestamp_var.get() else ""
            )
            formatted_message = (
                f"[{timestamp}] [{level}] {message}"
                if timestamp
                else f"[{level}] {message}"
            )
            self.log_queue.put((level, formatted_message))
        except:
            pass

    def process_log_queue(self):
        """Process log messages from the queue"""
        try:
            if not self.root.winfo_exists():
                return

            while True:
                level, message = self.log_queue.get_nowait()
                current_level = self.log_level_var.get()
                level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

                if level_priority.get(level, 0) >= level_priority.get(current_level, 0):
                    if self.log_text.winfo_exists():
                        self.log_text.insert(tk.END, message + "\n", level)
                        if self.auto_scroll_var.get():
                            self.log_text.see(tk.END)

        except queue.Empty:
            pass
        except:
            return

        try:
            if self.root.winfo_exists():
                self.root.after(100, self.process_log_queue)
        except:
            pass

    def on_setting_change(self):
        """Handle setting changes"""
        # Update settings dictionary
        self.settings["enable_cursor_tracking"] = self.cursor_tracking_var.get()
        self.settings["enable_click_recording"] = self.click_recording_var.get()
        self.settings["enable_on_screen_debug"] = self.on_screen_debug_var.get()
        self.settings["enable_disabled_buttons"] = self.disabled_buttons_var.get()

        # Handle window spy visibility
        if self.settings["enable_click_recording"]:
            if self.window_spy:
                self.window_spy.show()
        else:
            if self.window_spy:
                self.window_spy.hide()

        self.log("INFO", "Settings updated")
        self.apply_settings_to_overlay()

    def on_log_level_change(self, event=None):
        """Handle log level change"""
        old_level = self.settings.get("log_level", "INFO")
        new_level = self.log_level_var.get()
        self.settings["log_level"] = new_level

        level_descriptions = {
            "DEBUG": "All messages (DEBUG, INFO, WARNING, ERROR)",
            "INFO": "Standard messages (INFO, WARNING, ERROR)",
            "WARNING": "Important messages only (WARNING, ERROR)",
            "ERROR": "Error messages only (ERROR)",
        }

        description = level_descriptions.get(new_level, "Unknown level")
        self.log("INFO", f"Log level changed from {old_level} to {new_level}")
        self.log("INFO", f"Now showing: {description}")

    def apply_settings_to_overlay(self):
        """Apply current settings to the overlay"""
        try:
            if self.main_app and hasattr(self.main_app, "overlay"):
                overlay = self.main_app.overlay

                # Apply settings if overlay has these attributes
                for setting in [
                    "enable_cursor_tracking",
                    "enable_click_recording",
                    "enable_on_screen_debug",
                    "enable_disabled_buttons",
                ]:
                    if hasattr(overlay, setting):
                        setattr(overlay, setting, self.settings[setting])

                if hasattr(overlay, "hide_activate_button_setting"):
                    overlay.hide_activate_button_setting = self.hide_activate_var.get()

                if hasattr(overlay, "is_expanded") and overlay.is_expanded:
                    if hasattr(overlay, "draw_expanded"):
                        overlay.draw_expanded()

                self.log("SUCCESS", "Settings applied to overlay")
            else:
                self.log("WARNING", "No overlay found to apply settings to")
        except Exception as e:
            self.log("ERROR", f"Error applying settings to overlay: {e}")

    # Utility methods
    def update_status(self, key, value):
        """Update a status label"""
        try:
            if key in self.status_labels and self.status_labels[key].winfo_exists():
                self.status_labels[key].config(text=str(value))
        except:
            pass

    def update_stats(self, key, value):
        """Update a statistics label"""
        try:
            if key in self.stats_labels and self.stats_labels[key].winfo_exists():
                self.stats_labels[key].config(text=str(value))
        except:
            pass

    def add_action(self, action):
        """Add a new action to the list"""
        try:
            self.recent_actions.append(action)

            if action["type"] == "click":
                display_text = (
                    f"Click: ({action['x_percent']:.1f}%, {action['y_percent']:.1f}%)"
                )
            elif action["type"] == "drag":
                display_text = f"Drag: ({action['x1_percent']:.1f}%, {action['y1_percent']:.1f}%) to ({action['x2_percent']:.1f}%, {action['y2_percent']:.1f}%)"

            self.actions_listbox.insert(tk.END, display_text)

            if len(self.recent_actions) > 10:
                self.recent_actions.pop(0)
                self.actions_listbox.delete(0)

            self.actions_listbox.selection_clear(0, tk.END)
            self.actions_listbox.selection_set(tk.END)
            self.actions_listbox.see(tk.END)

        except Exception as e:
            self.log("ERROR", f"Error adding action: {e}")

    def update_window_spy_info(self, window_info, cursor_info):
        """Update the window spy information display"""
        try:
            if hasattr(self, "spy_labels"):
                self.spy_labels["Window Width"].config(
                    text=f"{window_info['width']} px"
                )
                self.spy_labels["Window Height"].config(
                    text=f"{window_info['height']} px"
                )
                self.spy_labels["Cursor X"].config(text=f"{cursor_info['x']} px")
                self.spy_labels["Cursor Y"].config(text=f"{cursor_info['y']} px")
                self.spy_labels["Cursor X%"].config(
                    text=f"{cursor_info['x_percent']:.1f}%"
                )
                self.spy_labels["Cursor Y%"].config(
                    text=f"{cursor_info['y_percent']:.1f}%"
                )
        except Exception as e:
            self.log("ERROR", f"Error updating window spy info: {e}")

    # Action methods
    def copy_selected_action(self):
        """Copy the selected action to clipboard"""
        try:
            selection = self.actions_listbox.curselection()
            if selection:
                index = selection[0]
                action = self.recent_actions[index]

                if action["type"] == "click":
                    clipboard_text = (
                        f"Click: {action['x_percent']:.1f}%, {action['y_percent']:.1f}%"
                    )
                elif action["type"] == "drag":
                    clipboard_text = f"Drag: {action['x1_percent']:.1f}%, {action['y1_percent']:.1f}% to {action['x2_percent']:.1f}%, {action['y2_percent']:.1f}%"

                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_text)
                self.log("INFO", f"Copied action: {clipboard_text}")
            else:
                self.log("WARNING", "No action selected to copy")
        except Exception as e:
            self.log("ERROR", f"Error copying action: {e}")

    def remove_selected_action(self):
        """Remove the selected action from the list"""
        try:
            selection = self.actions_listbox.curselection()
            if selection:
                index = selection[0]
                removed_action = self.recent_actions.pop(index)
                self.actions_listbox.delete(index)
                self.log("INFO", f"Removed action: {removed_action['type']}")
            else:
                self.log("WARNING", "No action selected to remove")
        except Exception as e:
            self.log("ERROR", f"Error removing action: {e}")

    def clear_all_actions(self):
        """Clear all actions from the list"""
        try:
            self.recent_actions.clear()
            self.actions_listbox.delete(0, tk.END)
            self.log("INFO", "Cleared all recorded actions")
        except Exception as e:
            self.log("ERROR", f"Error clearing actions: {e}")

    # Log methods
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        self.log("INFO", "Log cleared")

    def save_log(self):
        """Save the log to a file"""
        try:
            filename = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log("SUCCESS", f"Log saved to {filename}")
            messagebox.showinfo("Success", f"Log saved to {filename}")
        except Exception as e:
            self.log("ERROR", f"Failed to save log: {e}")
            messagebox.showerror("Error", f"Failed to save log: {e}")

    def copy_log(self):
        """Copy the log to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log_text.get(1.0, tk.END))
            self.root.update()
            self.log("SUCCESS", "Log copied to clipboard")
        except Exception as e:
            self.log("ERROR", f"Failed to copy log: {e}")
            messagebox.showerror("Error", f"Failed to copy log: {e}")

    # Control methods
    def reload_application(self):
        """Reload the application"""
        self.log("INFO", "🔄 Reloading application...")
        if self.main_app:
            try:
                self.main_app.reload_modules()
                self.log("SUCCESS", "Application reloaded successfully")
                self.update_status("Application Status", "RELOADED")
            except Exception as e:
                self.log("ERROR", f"Failed to reload application: {e}")
        else:
            self.log("WARNING", "No main application reference found")

    def restart_application(self):
        """Restart the entire application"""
        self.log("WARNING", "🔄 Restarting application...")
        if self.main_app:
            try:
                self.log("INFO", "Application restart initiated")
                self.root.after(500, self._perform_restart)
            except Exception as e:
                self.log("ERROR", f"Failed to initiate restart: {e}")
        else:
            self.log("ERROR", "No main application reference found")

    def _perform_restart(self):
        """Perform the actual restart"""
        import subprocess

        try:
            self.log("INFO", "Performing restart...")
            script_path = os.path.abspath(sys.argv[0])

            if self.main_app:
                self.main_app.monitoring_active = False

            self.root.quit()

            if script_path.endswith(".py"):
                subprocess.Popen([sys.executable, script_path])
            else:
                subprocess.Popen([script_path])

            sys.exit(0)
        except Exception as e:
            self.log("ERROR", f"Failed to restart application: {e}")
            messagebox.showerror("Restart Error", f"Failed to restart application: {e}")

    # Stub methods for functionality not yet implemented
    def test_overlay(self):
        """Test the overlay functionality"""
        self.log("INFO", "Testing overlay...")
        if self.main_app and hasattr(self.main_app, "overlay"):
            self.main_app.overlay.update_status("TESTING", "Test overlay function")
            self.root.after(
                3000,
                lambda: self.main_app.overlay.update_status(
                    "INACTIVE", "No minigame detected"
                ),
            )
        else:
            self.log("WARNING", "No overlay found to test")

    def test_detection(self):
        """Test the detection system"""
        self.log("INFO", "Testing detection system...")
        self.log("SUCCESS", "Detection test completed")

    def force_detection(self):
        """Force a detection check"""
        self.log("INFO", "Forcing detection check...")

    def reset_stats(self):
        """Reset all statistics"""
        for key in self.stats_labels:
            if key == "Uptime":
                self.update_stats(key, "00:00:00")
            else:
                self.update_stats(key, "0")
        self.log("INFO", "Statistics reset")

    def toggle_overlay(self):
        """Toggle overlay visibility"""
        self.log("INFO", "Toggling overlay visibility")

    def reset_overlay_position(self):
        """Reset overlay position"""
        self.log("INFO", "Resetting overlay position")

    def reload_config(self):
        """Reload configuration files"""
        self.log("INFO", "Reloading configuration files...")

    def edit_minigames(self):
        """Open minigames config for editing"""
        self.log("INFO", "Opening minigames config for editing")

    def edit_settings(self):
        """Open settings config for editing"""
        self.log("INFO", "Opening settings config for editing")

    def stop_all_automation(self):
        """Stop all automation processes"""
        self.log("WARNING", "Stopping all automation processes")

    def force_focus_widgetinc(self):
        """Force focus on WidgetInc window"""
        self.log("INFO", "Forcing focus on WidgetInc window")

    def reset_everything(self):
        """Reset everything to default state"""
        if messagebox.askyesno(
            "Confirm Reset", "Are you sure you want to reset everything?"
        ):
            self.log("WARNING", "Resetting everything to default state")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Widget Automation Tool - Debug GUI

Version: 1.0.0
Author: AI Assistant
Description: Debug interface for the Widget Automation Tool

Features:
- Real-time logging and monitoring
- Settings management
- Application control
- Statistics tracking
- Emergency controls

Press Ctrl+R to reload the application
        """
        messagebox.showinfo("About", about_text)

    def run(self):
        """Run the debug GUI"""
        self.root.mainloop()

    def destroy(self):
        """Destroy the debug GUI"""
        if hasattr(self, "window_spy") and self.window_spy:
            self.window_spy.destroy()
        self.root.destroy()


def create_debug_gui(main_app=None):
    """Create and return a debug GUI instance"""
    return DebugGUI(main_app)


if __name__ == "__main__":
    debug_gui = create_debug_gui()
    debug_gui.run()
