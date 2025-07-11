import json
import time
import sys
import tkinter as tk
import threading
from widget_inc_manager import WidgetIncManager
from mouse_control import click_mouse_percent, move_mouse_to_percent
from overlay_gui import create_overlay


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
    print("=" * 50)
    print("Widget Automation Tool - Starting...")
    print("=" * 50)

    # Initialize tkinter root (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide main window

    # Create overlay GUI
    overlay = create_overlay()
    overlay.show()
    overlay.update_status("STARTING", "Initializing...")

    # Load configuration
    config = load_minigames_config()
    settings = load_settings()

    if not config or not settings:
        print("Failed to load configuration files. Exiting.")
        overlay.update_status("ERROR", "Config load failed")
        time.sleep(2)
        overlay.destroy()
        return 1

    # Initialize WidgetInc manager
    widget_manager = WidgetIncManager()
    overlay.update_status("WAITING", "Looking for WidgetInc...")

    # Wait for WidgetInc to be ready
    if not widget_manager.wait_for_widget_inc():
        print("WidgetInc not found. Please start WidgetInc.exe and try again.")
        overlay.update_status("ERROR", "WidgetInc not found")
        time.sleep(2)
        overlay.destroy()
        return 1

    # Ensure WidgetInc is focused and ready
    if not widget_manager.ensure_widget_inc_ready():
        print("Could not prepare WidgetInc for automation.")
        overlay.update_status("ERROR", "Failed to focus WidgetInc")
        time.sleep(2)
        overlay.destroy()
        return 1

    # Display window information
    window_info = widget_manager.get_window_info()
    if window_info:
        print(
            f"WidgetInc Window: {window_info['width']}x{window_info['height']} at ({window_info['left']}, {window_info['top']})"
        )

    # Update overlay to show ready state
    overlay.update_status("INACTIVE", "No minigame detected")

    print("\nWidget Automation Tool initialized successfully!")
    print("The tool is now monitoring for minigames...")
    print("Overlay will display current status. Click to pin/unpin.")
    print("Press Ctrl+C to exit.")
    print("-" * 50)

    # Background monitoring function (placeholder for future minigame detection)
    def monitor_minigames():
        """Monitor for minigames and update overlay status"""
        while True:
            try:
                # Placeholder for minigame detection logic
                # This is where you would implement:
                # - Screen capture analysis
                # - Template matching
                # - UI element detection
                # - Game state recognition

                # For now, just maintain inactive state
                # Future implementation would check for active minigames
                # and update overlay status accordingly

                time.sleep(1)  # Check every second

            except Exception as e:
                print(f"Monitoring error: {e}")
                overlay.update_status("ERROR", f"Monitoring error: {e}")
                time.sleep(5)  # Wait before retrying

    # Start monitoring in background
    monitor_thread = threading.Thread(target=monitor_minigames, daemon=True)
    monitor_thread.start()

    # Start tkinter main loop (keeps overlay running)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        overlay.destroy()

    return 0


if __name__ == "__main__":
    sys.exit(main())
