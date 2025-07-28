#!/usr/bin/env python3
"""
Simple highlight test to see if tkinter windows show up on screen.
"""

import tkinter as tk
import sys


def test_highlighting():
    """Test if we can create visible highlight windows."""
    print("Testing highlighting system...")

    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)

    # Create a bright, large highlight in the center of screen
    highlight = tk.Toplevel(root)
    highlight.overrideredirect(True)
    highlight.attributes("-topmost", True)
    highlight.attributes("-alpha", 0.9)  # Very opaque

    # Make it big and bright so we can definitely see it
    size = 50
    x, y = 200, 200  # Screen coordinates
    highlight.geometry(f"{size}x{size}+{x}+{y}")
    highlight.configure(bg="#FF0000")  # Bright red

    print(f"Created bright red {size}x{size} highlight at ({x}, {y})")
    print("You should see a bright red square on your screen for 3 seconds...")

    # Force immediate display
    highlight.lift()
    highlight.focus_force()
    root.update_idletasks()
    root.update()

    # Wait 3 seconds
    root.after(3000, sys.exit)
    root.mainloop()


if __name__ == "__main__":
    test_highlighting()
