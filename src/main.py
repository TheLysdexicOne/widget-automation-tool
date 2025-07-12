import json
import time
import sys
import tkinter as tk
import threading
import importlib
import argparse
from widget_inc_manager import WidgetIncManager
from mouse_control import click_mouse_percent, move_mouse_to_percent
from overlay_gui import OverlayGUI
from minigame_detector import MinigameDetector
from debug_gui import create_debug_gui


class MainApplication:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.monitoring_active = False
        self.overlay = None
        self.detector = None
        self.widget_manager = None
        self.monitoring_thread = None
        self.debug_gui = None
        self.system_tray = None
        self.stats = {
            "detections_today": 0,
            "automation_runs": 0,
            "errors": 0,
            "start_time": time.time(),
        }

        # Modules to reload
        self.modules_to_reload = [
            "overlay_gui",
            "widget_inc_manager",
            "minigame_detector",
            "mouse_control",
            "screen_capture",
            "text_recognition",
            "debug_gui",
        ]

    def schedule_gui_update(self, callback):
        """Schedule a GUI update to run in the main thread"""
        if self.debug_gui and hasattr(self.debug_gui, "root"):
            try:
                # Check if GUI is still valid
                if self.debug_gui.root.winfo_exists():
                    self.debug_gui.root.after(0, self._safe_gui_callback(callback))
            except:
                pass  # Ignore if GUI is not ready or destroyed

    def _safe_gui_callback(self, callback):
        """Wrap GUI callback with error handling"""

        def safe_callback():
            try:
                # Double-check GUI is still valid before executing
                if (
                    self.debug_gui
                    and hasattr(self.debug_gui, "root")
                    and self.debug_gui.root.winfo_exists()
                ):
                    callback()
            except Exception as e:
                # GUI might have been destroyed, ignore silently
                pass

        return safe_callback

    def reload_modules(self):
        """Reload Python modules"""
        for module_name in self.modules_to_reload:
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    if self.debug_gui:
                        self.debug_gui.log("DEBUG", f"Reloaded module: {module_name}")
            except Exception as e:
                if self.debug_gui:
                    self.debug_gui.log("ERROR", f"Failed to reload {module_name}: {e}")

    def start(self):
        """Start the main application"""
        print("=" * 50)
        print("Widget Automation Tool - Starting...")
        print("=" * 50)

        # Initialize tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window

        # Create debug GUI
        self.debug_gui = create_debug_gui(self)

        # Show GUI based on mode
        if self.debug_mode:
            print("Debug mode: Showing GUI")
            self.debug_gui.log("INFO", "Starting in DEBUG mode with GUI...")
        else:
            print("Normal mode: Starting in system tray")
            self.debug_gui.log("INFO", "Starting in NORMAL mode with system tray...")
            self.debug_gui.root.withdraw()  # Hide debug GUI initially
            self.create_system_tray()

        # Log startup
        self.debug_gui.update_status("Application Status", "STARTING")

        # Load configuration
        if not self.load_config():
            self.debug_gui.log("ERROR", "Failed to load configuration")
            return False

        # Initialize components
        if not self.initialize_components():
            self.debug_gui.log("ERROR", "Failed to initialize components")
            return False

        # Start monitoring
        self.start_monitoring()

        # Setup hotkeys
        self.setup_hotkeys()

        # Start GUI loop
        self.start_gui_loop()

        return True

    def load_config(self):
        """Load configuration files"""
        try:
            self.minigames_config = load_minigames_config()
            self.settings = load_settings()

            if not self.minigames_config or not self.settings:
                return False

            self.debug_gui.log("SUCCESS", "Configuration loaded successfully")
            return True
        except Exception as e:
            self.debug_gui.log("ERROR", f"Failed to load configuration: {e}")
            return False

    def initialize_components(self):
        """Initialize application components"""
        try:
            # Initialize widget manager
            self.widget_manager = WidgetIncManager()
            self.debug_gui.log("INFO", "Widget manager initialized")

            # Check for WidgetInc
            self.debug_gui.update_status("WidgetInc Status", "SEARCHING...")
            if not self.widget_manager.wait_for_widget_inc():
                self.debug_gui.log(
                    "WARNING", "WidgetInc not found - running in test mode"
                )
                self.debug_gui.update_status("WidgetInc Status", "NOT FOUND")
            else:
                self.debug_gui.log("SUCCESS", "WidgetInc found and ready")
                self.debug_gui.update_status("WidgetInc Status", "READY")

            # Initialize overlay
            self.overlay = OverlayGUI()
            self.overlay.widget_manager = self.widget_manager
            self.overlay.widget_manager.main_app = (
                self  # Link to main app for debug console access
            )
            self.overlay.show()
            self.debug_gui.log("SUCCESS", "Overlay initialized")
            self.debug_gui.update_status("Overlay Status", "ACTIVE")

            # Initialize detector
            self.detector = MinigameDetector(self.widget_manager)
            self.debug_gui.log("SUCCESS", "Minigame detector initialized")

            # Link debug GUI to overlay
            self.link_debug_gui_to_overlay()

            return True
        except Exception as e:
            self.debug_gui.log("ERROR", f"Failed to initialize components: {e}")
            return False

    def link_debug_gui_to_overlay(self):
        """Link debug GUI settings to overlay"""
        # Only set attributes that exist on the overlay
        if hasattr(self.overlay, "hide_activate_button_setting"):
            self.overlay.hide_activate_button_setting = self.debug_gui.settings.get(
                "hide_activate_button", False
            )

        # Store debug settings reference for overlay to use
        self.overlay.debug_settings = self.debug_gui.settings

    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self.monitor_minigames, daemon=True
        )
        self.monitoring_thread.start()

        self.debug_gui.log("SUCCESS", "Monitoring thread started")
        self.debug_gui.update_status("Monitoring Active", "TRUE")

    def monitor_minigames(self):
        """Monitor for minigames and update overlay status"""
        while self.monitoring_active:
            try:
                # Detect current minigame
                current_game = self.detector.detect_current_minigame()

                if current_game:
                    # Schedule GUI updates in main thread
                    self.schedule_gui_update(
                        lambda: self.overlay.update_status(
                            "WAITING", f"Detected: {current_game['name']}"
                        )
                    )
                    self.schedule_gui_update(
                        lambda: self.overlay.show_activate_button(current_game)
                    )

                    # Update debug GUI
                    self.schedule_gui_update(
                        lambda: self.debug_gui.update_status(
                            "Current Minigame", current_game["name"]
                        )
                    )
                    self.schedule_gui_update(
                        lambda: self.debug_gui.update_status(
                            "Last Detection", time.strftime("%H:%M:%S")
                        )
                    )

                    # Update statistics
                    self.stats["detections_today"] += 1
                    self.schedule_gui_update(
                        lambda: self.debug_gui.update_stats(
                            "Detections Today", self.stats["detections_today"]
                        )
                    )

                    # Log detection
                    try:
                        if self.debug_gui.settings["enable_logging"]:
                            confidence = current_game.get("confidence", 0)
                            self.schedule_gui_update(
                                lambda: self.debug_gui.log(
                                    "INFO",
                                    f"Detected: {current_game['name']} (confidence: {confidence:.2f})",
                                )
                            )
                    except:
                        pass  # Skip logging if GUI not ready

                else:
                    # No minigame detected
                    if (
                        hasattr(self.overlay, "status_text")
                        and self.overlay.status_text != "ACTIVE"
                    ):
                        self.schedule_gui_update(
                            lambda: self.overlay.update_status(
                                "INACTIVE", "No minigame detected"
                            )
                        )
                        self.schedule_gui_update(
                            lambda: self.overlay.hide_activate_button()
                        )
                        self.schedule_gui_update(
                            lambda: self.debug_gui.update_status(
                                "Current Minigame", "None"
                            )
                        )

                # Update uptime
                uptime = time.time() - self.stats["start_time"]
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.schedule_gui_update(
                    lambda: self.debug_gui.update_stats("Uptime", uptime_str)
                )

                time.sleep(1)

            except Exception as e:
                self.stats["errors"] += 1
                try:
                    self.schedule_gui_update(
                        lambda: self.debug_gui.update_stats(
                            "Errors", self.stats["errors"]
                        )
                    )
                    self.schedule_gui_update(
                        lambda: self.debug_gui.log("ERROR", f"Monitoring error: {e}")
                    )
                    self.schedule_gui_update(
                        lambda: self.overlay.update_status("ERROR", f"Monitoring error")
                    )
                except:
                    print(f"Monitoring error: {e}")  # Fallback to console
                time.sleep(5)

    def setup_hotkeys(self):
        """Setup hotkeys"""
        try:
            # Setup Ctrl+R for reload
            self.root.bind("<Control-r>", lambda e: self.reload_application())
            self.debug_gui.log("SUCCESS", "Hotkeys registered: Ctrl+R")
        except Exception as e:
            self.debug_gui.log("WARNING", f"Could not setup hotkeys: {e}")

    def reload_application(self):
        """Reload the application"""
        self.schedule_gui_update(
            lambda: self.debug_gui.log(
                "INFO", "🔄 Starting application reload process..."
            )
        )

        try:
            # Reload modules
            self.schedule_gui_update(
                lambda: self.debug_gui.log("INFO", "📦 Reloading Python modules...")
            )
            self.reload_modules()

            # Reload configuration
            self.schedule_gui_update(
                lambda: self.debug_gui.log("INFO", "⚙️ Reloading configuration files...")
            )
            self.load_config()

            # Reinitialize detector
            if self.detector:
                self.schedule_gui_update(
                    lambda: self.debug_gui.log(
                        "INFO", "🔍 Reinitializing minigame detector..."
                    )
                )
                self.detector.load_known_minigames()

            # Show reload notification on overlay
            if self.overlay:
                self.schedule_gui_update(
                    lambda: self.debug_gui.log("INFO", "🎯 Updating overlay status...")
                )
                self.schedule_gui_update(
                    lambda: self.overlay.update_status(
                        "RELOADED", "Application reloaded"
                    )
                )
                self.schedule_gui_update(
                    lambda: self.debug_gui.root.after(
                        2000,
                        lambda: self.overlay.update_status(
                            "INACTIVE", "No minigame detected"
                        ),
                    )
                )

            self.schedule_gui_update(
                lambda: self.debug_gui.log(
                    "SUCCESS", "✅ Application reloaded successfully!"
                )
            )
            self.schedule_gui_update(
                lambda: self.debug_gui.update_status("Application Status", "RUNNING")
            )

        except Exception as e:
            self.schedule_gui_update(
                lambda: self.debug_gui.log(
                    "ERROR", f"❌ Failed to reload application: {e}"
                )
            )

    def start_gui_loop(self):
        """Start the GUI main loop"""
        try:
            self.debug_gui.log("SUCCESS", "Application ready! Debug GUI is running.")
            self.debug_gui.log(
                "INFO", "Press Ctrl+R to reload, close debug window to exit"
            )
            self.debug_gui.update_status("Application Status", "RUNNING")

            # Run the debug GUI in the main thread
            self.debug_gui.run()

        except KeyboardInterrupt:
            self.debug_gui.log("INFO", "Shutting down application...")
            self.shutdown()
        except Exception as e:
            print(f"Error in GUI loop: {e}")
            self.shutdown()

    def shutdown(self):
        """Shutdown the application"""
        print("Shutting down application...")

        # Stop monitoring first
        self.monitoring_active = False
        print("Monitoring stopped")

        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            print("Waiting for monitoring thread to finish...")
            self.monitoring_thread.join(timeout=3)
            if self.monitoring_thread.is_alive():
                print("Warning: Monitoring thread did not finish cleanly")

        # Destroy components
        try:
            if self.overlay:
                print("Destroying overlay...")
                self.overlay.destroy()
        except Exception as e:
            print(f"Error destroying overlay: {e}")

        try:
            if self.debug_gui:
                print("Destroying debug GUI...")
                self.debug_gui.destroy()
        except Exception as e:
            print(f"Error destroying debug GUI: {e}")

        print("Application shutdown complete")
        sys.exit(0)

    def create_system_tray(self):
        """Create system tray functionality"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Create a simple icon
            def create_icon():
                # Create a simple red circle icon
                width = 64
                height = 64
                image = Image.new("RGB", (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(image)
                draw.ellipse([8, 8, width - 8, height - 8], fill=(255, 68, 68))
                return image

            # Create menu items
            menu = pystray.Menu(
                pystray.MenuItem("Show Debug Console", self.show_debug_console),
                pystray.MenuItem("Hide Debug Console", self.hide_debug_console),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.exit_application),
            )

            # Create system tray icon
            self.system_tray = pystray.Icon(
                "Widget Automation Tool",
                create_icon(),
                menu=menu,
            )

            # Start system tray in background thread
            def run_tray():
                self.system_tray.run()

            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()

            self.debug_gui.log("SUCCESS", "System tray created successfully")

        except ImportError:
            self.debug_gui.log(
                "WARNING",
                "pystray not available - install with: pip install pystray Pillow",
            )
        except Exception as e:
            self.debug_gui.log("ERROR", f"Failed to create system tray: {e}")

    def show_debug_console(self):
        """Show the debug console from system tray"""
        if self.debug_gui and hasattr(self.debug_gui, "root"):
            try:
                self.debug_gui.root.deiconify()
                self.debug_gui.root.lift()
                self.debug_gui.root.focus_force()
                self.debug_gui.log("INFO", "Debug console shown from system tray")
            except:
                pass

    def hide_debug_console(self):
        """Hide the debug console to system tray"""
        if self.debug_gui and hasattr(self.debug_gui, "root"):
            try:
                self.debug_gui.root.withdraw()
                self.debug_gui.log("INFO", "Debug console hidden to system tray")
            except:
                pass

    def exit_application(self):
        """Exit application from system tray"""
        try:
            if self.system_tray:
                self.system_tray.stop()
            self.shutdown()
        except:
            pass


def load_minigames_config():
    """Load the minigames configuration"""
    try:
        with open("config/minigames.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading minigames config: {e}")
        return None


def load_settings():
    """Load the application settings"""
    try:
        with open("config/settings.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return None


def run_static_ui_game(minigame, widget_manager):
    """Run a static UI-based minigame"""
    print(f"Running static UI game: {minigame['name']}")

    # Placeholder for UI detection and clicking
    # This would integrate with the UIDetector class
    automation_sequence = minigame.get("automation_sequence", [])

    for step in automation_sequence:
        action = step.get("action")

        if action == "detect_ui":
            print("Detecting UI elements...")
            time.sleep(step.get("wait", 1.0))

        elif action == "click_element":
            element = step.get("element")
            print(f"Clicking element: {element}")
            # Placeholder - would use UIDetector to find and click
            time.sleep(0.5)

        elif action == "wait":
            duration = step.get("duration", 1.0)
            print(f"Waiting {duration} seconds...")
            time.sleep(duration)

    return True


def run_vision_based_game(minigame, widget_manager):
    """Run a vision-based minigame (like sprite sorting)"""
    print(f"Running vision-based game: {minigame['name']}")

    # Placeholder for computer vision logic
    # This would integrate with the SpriteDetector class
    duration = minigame["parameters"].get("duration", 60)
    print(f"Running for {duration} seconds...")

    # Simulate automation
    time.sleep(duration)

    return True


def run_hybrid_game(minigame, widget_manager):
    """Run a hybrid game that uses both UI detection and computer vision"""
    print(f"Running hybrid game: {minigame['name']}")

    # Placeholder for hybrid logic
    duration = minigame["parameters"].get("duration", 45)
    print(f"Running for {duration} seconds...")

    # Simulate automation
    time.sleep(duration)

    return True


def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Widget Automation Tool")
    parser.add_argument(
        "--debug", action="store_true", help="Start in debug mode with GUI visible"
    )
    args = parser.parse_args()

    # Create application with debug mode flag
    app = MainApplication(debug_mode=args.debug)
    return app.start()


if __name__ == "__main__":
    sys.exit(main() if main() else 0)
