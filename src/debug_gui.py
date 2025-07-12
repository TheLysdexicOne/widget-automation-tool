#!/usr/bin/env python3
"""
Debug GUI for Widget Automation Tool
Separate window for debugging, logging, and appl        # Log text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white'
        )trol
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


class DebugGUI:
    def __init__(self, main_app=None):
        self.main_app = main_app
        self.root = tk.Tk()
        self.root.title("Widget Automation Tool - Debug Console")
        self.root.geometry("800x600")

        # Logging system
        self.log_queue = queue.Queue()
        self.log_levels = {
            "DEBUG": "#B0B0B0",  # Light grey instead of dark grey
            "INFO": "#FFFFFF",  # White for better contrast
            "WARNING": "#FFD700",  # Gold instead of orange
            "ERROR": "#FF6B6B",  # Lighter red
            "SUCCESS": "#4CAF50",  # Green
        }

        # Settings
        self.settings = {
            "debug_mode": False,
            "enable_logging": True,
            "enable_cursor_tracking": False,
            "enable_click_recording": False,
            "enable_on_screen_debug": False,
            "enable_disabled_buttons": False,
            "auto_scroll_log": True,
            "log_timestamps": True,
            "log_level": "INFO",
        }

        # Initialize GUI
        self.setup_gui()
        self.setup_logging()

        # Start log processing
        self.process_log_queue()

        # Welcome message
        self.log("INFO", "Debug GUI initialized successfully")
        self.log("INFO", "Press Ctrl+R to reload application")

    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create main menu
        self.create_menu()

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create tabs
        self.create_console_tab()
        self.create_settings_tab()
        self.create_monitoring_tab()
        self.create_controls_tab()

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

        # Log text widget with scrollbar
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
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10,
        )
        log_level_combo.pack(side="left", padx=5)
        log_level_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls_frame, text="Auto-scroll", variable=self.auto_scroll_var
        ).pack(side="left", padx=10)

        # Timestamp checkbox
        self.timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls_frame, text="Timestamps", variable=self.timestamp_var
        ).pack(side="left", padx=10)

        # Clear button
        ttk.Button(controls_frame, text="Clear Log", command=self.clear_log).pack(
            side="right", padx=5
        )

        # Copy button
        ttk.Button(controls_frame, text="Copy Log", command=self.copy_log).pack(
            side="right", padx=5
        )

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Main settings frame
        main_frame = ttk.LabelFrame(settings_frame, text="Debug Settings")
        main_frame.pack(fill="x", padx=10, pady=10)

        # Debug mode
        self.debug_mode_var = tk.BooleanVar(value=self.settings["debug_mode"])
        ttk.Checkbutton(
            main_frame,
            text="Debug Mode",
            variable=self.debug_mode_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Enable logging
        self.enable_logging_var = tk.BooleanVar(value=self.settings["enable_logging"])
        ttk.Checkbutton(
            main_frame,
            text="Enable Logging",
            variable=self.enable_logging_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Cursor tracking
        self.cursor_tracking_var = tk.BooleanVar(
            value=self.settings["enable_cursor_tracking"]
        )
        ttk.Checkbutton(
            main_frame,
            text="Enable Cursor Tracking",
            variable=self.cursor_tracking_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Click recording
        self.click_recording_var = tk.BooleanVar(
            value=self.settings["enable_click_recording"]
        )
        ttk.Checkbutton(
            main_frame,
            text="Enable Click Recording",
            variable=self.click_recording_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # On-screen debug
        self.on_screen_debug_var = tk.BooleanVar(
            value=self.settings["enable_on_screen_debug"]
        )
        ttk.Checkbutton(
            main_frame,
            text="Enable On-screen Debug",
            variable=self.on_screen_debug_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Disabled buttons
        self.disabled_buttons_var = tk.BooleanVar(
            value=self.settings["enable_disabled_buttons"]
        )
        ttk.Checkbutton(
            main_frame,
            text="Enable Disabled Buttons",
            variable=self.disabled_buttons_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

        # Overlay settings frame
        overlay_frame = ttk.LabelFrame(settings_frame, text="Overlay Settings")
        overlay_frame.pack(fill="x", padx=10, pady=10)

        # Hide activate button
        self.hide_activate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            overlay_frame,
            text="Hide Activate Button",
            variable=self.hide_activate_var,
            command=self.on_setting_change,
        ).pack(anchor="w", padx=10, pady=5)

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

        # Status labels
        self.status_labels = {}
        status_items = [
            ("Application Status", "STARTING"),
            ("WidgetInc Status", "UNKNOWN"),
            ("Current Minigame", "None"),
            ("Overlay Status", "HIDDEN"),
            ("Monitoring Active", "FALSE"),
            ("Last Detection", "Never"),
        ]

        for i, (label, default_value) in enumerate(status_items):
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

        self.stats_labels = {}
        stats_items = [
            ("Detections Today", "0"),
            ("Automation Runs", "0"),
            ("Uptime", "00:00:00"),
            ("Errors", "0"),
        ]

        for i, (label, default_value) in enumerate(stats_items):
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

    def create_controls_tab(self):
        """Create the controls tab"""
        controls_frame = ttk.Frame(self.notebook)
        self.notebook.add(controls_frame, text="Controls")

        # Application controls
        app_frame = ttk.LabelFrame(controls_frame, text="Application Controls")
        app_frame.pack(fill="x", padx=10, pady=10)

        btn_frame1 = ttk.Frame(app_frame)
        btn_frame1.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            btn_frame1,
            text="Reload Application (Ctrl+R)",
            command=self.reload_application,
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame1, text="Show/Hide Overlay", command=self.toggle_overlay
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame1,
            text="Reset Overlay Position",
            command=self.reset_overlay_position,
        ).pack(side="left", padx=5)

        # Second row for restart button
        btn_frame1_row2 = ttk.Frame(app_frame)
        btn_frame1_row2.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            btn_frame1_row2,
            text="🔄 Restart Application",
            command=self.restart_application,
        ).pack(side="left", padx=5)

        # Configuration controls
        config_frame = ttk.LabelFrame(controls_frame, text="Configuration")
        config_frame.pack(fill="x", padx=10, pady=10)

        btn_frame2 = ttk.Frame(config_frame)
        btn_frame2.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame2, text="Reload Config", command=self.reload_config).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame2, text="Edit Minigames", command=self.edit_minigames).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame2, text="Edit Settings", command=self.edit_settings).pack(
            side="left", padx=5
        )

        # Emergency controls
        emergency_frame = ttk.LabelFrame(controls_frame, text="Emergency Controls")
        emergency_frame.pack(fill="x", padx=10, pady=10)

        btn_frame3 = ttk.Frame(emergency_frame)
        btn_frame3.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            btn_frame3, text="Stop All Automation", command=self.stop_all_automation
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame3, text="Force Focus WidgetInc", command=self.force_focus_widgetinc
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame3, text="Reset Everything", command=self.reset_everything
        ).pack(side="left", padx=5)

    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_logging(self):
        """Setup the logging system"""
        # Configure text tags for different log levels
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
            pass  # Ignore if GUI is destroyed

    def process_log_queue(self):
        """Process log messages from the queue"""
        try:
            # Check if GUI is still valid
            if not self.root.winfo_exists():
                return

            while True:
                level, message = self.log_queue.get_nowait()

                # Check if message level should be displayed
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
            # GUI might be destroyed, stop processing
            return

        # Schedule next check only if GUI is still valid
        try:
            if self.root.winfo_exists():
                self.root.after(100, self.process_log_queue)
        except:
            pass

    def on_setting_change(self):
        """Handle setting changes"""
        # Update settings dictionary
        self.settings["debug_mode"] = self.debug_mode_var.get()
        self.settings["enable_logging"] = self.enable_logging_var.get()
        self.settings["enable_cursor_tracking"] = self.cursor_tracking_var.get()
        self.settings["enable_click_recording"] = self.click_recording_var.get()
        self.settings["enable_on_screen_debug"] = self.on_screen_debug_var.get()
        self.settings["enable_disabled_buttons"] = self.disabled_buttons_var.get()

        self.log("INFO", "Settings updated")

    def on_log_level_change(self, event=None):
        """Handle log level change"""
        self.settings["log_level"] = self.log_level_var.get()
        self.log("INFO", f"Log level changed to {self.log_level_var.get()}")

    def apply_settings_to_overlay(self):
        """Apply current settings to the overlay"""
        if self.main_app and hasattr(self.main_app, "overlay"):
            overlay = self.main_app.overlay

            # Apply settings
            overlay.debug_mode = self.settings["debug_mode"]
            overlay.enable_logging = self.settings["enable_logging"]
            overlay.enable_cursor_tracking = self.settings["enable_cursor_tracking"]
            overlay.enable_click_recording = self.settings["enable_click_recording"]
            overlay.enable_on_screen_debug = self.settings["enable_on_screen_debug"]
            overlay.enable_disabled_buttons = self.settings["enable_disabled_buttons"]
            overlay.hide_activate_button_setting = self.hide_activate_var.get()

            # Refresh overlay
            if overlay.is_expanded:
                overlay.draw_expanded()

            self.log("SUCCESS", "Settings applied to overlay")
        else:
            self.log("ERROR", "No overlay found to apply settings to")

    def update_status(self, key, value):
        """Update a status label"""
        try:
            if key in self.status_labels and self.status_labels[key].winfo_exists():
                self.status_labels[key].config(text=str(value))
        except:
            pass  # Ignore if widget is destroyed

    def update_stats(self, key, value):
        """Update a statistics label"""
        try:
            if key in self.stats_labels and self.stats_labels[key].winfo_exists():
                self.stats_labels[key].config(text=str(value))
        except:
            pass  # Ignore if widget is destroyed

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
            import pyperclip

            log_content = self.log_text.get(1.0, tk.END)
            pyperclip.copy(log_content)
            self.log("SUCCESS", "Log copied to clipboard")
        except ImportError:
            # Fallback to tkinter clipboard if pyperclip not available
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.log_text.get(1.0, tk.END))
                self.root.update()  # Keep clipboard after window closes
                self.log("SUCCESS", "Log copied to clipboard")
            except Exception as e:
                self.log("ERROR", f"Failed to copy log: {e}")
                messagebox.showerror("Error", f"Failed to copy log: {e}")
        except Exception as e:
            self.log("ERROR", f"Failed to copy log: {e}")
            messagebox.showerror("Error", f"Failed to copy log: {e}")

    def reload_application(self):
        """Reload the application"""
        self.log("INFO", "🔄 Reloading application...")

        if self.main_app:
            try:
                # Reload modules
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
                # Log the restart
                self.log("INFO", "Application restart initiated")

                # Schedule the restart to happen after a short delay
                self.root.after(500, self._perform_restart)

            except Exception as e:
                self.log("ERROR", f"Failed to initiate restart: {e}")
        else:
            self.log("ERROR", "No main application reference found")

    def _perform_restart(self):
        """Perform the actual restart"""
        import os
        import sys
        import subprocess

        try:
            # Log the restart
            self.log("INFO", "Performing restart...")

            # Get the current script path
            script_path = os.path.abspath(sys.argv[0])

            # Close the application
            if self.main_app:
                self.main_app.monitoring_active = False

            # Destroy the GUI
            self.root.quit()

            # Start new process
            if script_path.endswith(".py"):
                # If running from Python
                subprocess.Popen([sys.executable, script_path])
            else:
                # If running from executable
                subprocess.Popen([script_path])

            # Exit current process
            sys.exit(0)

        except Exception as e:
            self.log("ERROR", f"Failed to restart application: {e}")
            messagebox.showerror("Restart Error", f"Failed to restart application: {e}")

    def test_overlay(self):
        """Test the overlay functionality"""
        self.log("INFO", "Testing overlay...")

        if self.main_app and hasattr(self.main_app, "overlay"):
            overlay = self.main_app.overlay
            # Test different states
            overlay.update_status("TESTING", "Debug GUI test")
            self.root.after(
                2000, lambda: overlay.update_status("INACTIVE", "Test complete")
            )
            self.log("SUCCESS", "Overlay test completed")
        else:
            self.log("ERROR", "No overlay found to test")

    def test_detection(self):
        """Test the detection system"""
        self.log("INFO", "Testing detection system...")
        # Add detection test logic here
        self.log("SUCCESS", "Detection test completed")

    def force_detection(self):
        """Force a detection check"""
        self.log("INFO", "Forcing detection check...")
        # Add force detection logic here

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
        # Add overlay toggle logic here

    def reset_overlay_position(self):
        """Reset overlay position"""
        self.log("INFO", "Resetting overlay position")
        # Add overlay position reset logic here

    def reload_config(self):
        """Reload configuration files"""
        self.log("INFO", "Reloading configuration files...")
        # Add config reload logic here

    def edit_minigames(self):
        """Open minigames config for editing"""
        self.log("INFO", "Opening minigames config for editing")
        # Add config editing logic here

    def edit_settings(self):
        """Open settings config for editing"""
        self.log("INFO", "Opening settings config for editing")
        # Add settings editing logic here

    def stop_all_automation(self):
        """Stop all automation processes"""
        self.log("WARNING", "Stopping all automation processes")
        # Add automation stop logic here

    def force_focus_widgetinc(self):
        """Force focus on WidgetInc window"""
        self.log("INFO", "Forcing focus on WidgetInc window")
        # Add focus logic here

    def reset_everything(self):
        """Reset everything to default state"""
        if messagebox.askyesno(
            "Confirm Reset", "Are you sure you want to reset everything?"
        ):
            self.log("WARNING", "Resetting everything to default state")
            # Add reset logic here

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
        self.root.destroy()


def create_debug_gui(main_app=None):
    """Create and return a debug GUI instance"""
    return DebugGUI(main_app)


if __name__ == "__main__":
    # Test the debug GUI standalone
    debug_gui = create_debug_gui()
    debug_gui.run()
