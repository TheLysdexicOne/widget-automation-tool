#!/usr/bin/env python3
"""
Test highlighting visibility without pixel scanning.
"""

import tkinter as tk


def test_multiple_highlights():
    """Test creating multiple highlights at different screen positions."""
    print("Testing multiple highlights across the screen...")

    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes("-topmost", True)

    highlights = []

    # Create highlights at various screen positions
    test_positions = [
        (100, 100),  # Top-left area
        (500, 300),  # Center area
        (900, 500),  # Right side
        (200, 700),  # Bottom area
        (600, 200),  # Top-center
    ]

    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]

    print(f"Creating {len(test_positions)} bright highlights...")

    for i, (x, y) in enumerate(test_positions):
        highlight = tk.Toplevel(root)
        highlight.overrideredirect(True)
        highlight.attributes("-topmost", True)
        highlight.attributes("-alpha", 1.0)  # Completely opaque

        # Make them big and bright
        size = 40
        color = colors[i]
        highlight.geometry(f"{size}x{size}+{x}+{y}")
        highlight.configure(bg=color)

        # Force immediate display
        highlight.lift()
        highlight.focus_force()

        highlights.append(highlight)
        print(f"  Created {size}x{size} {color} highlight at ({x}, {y})")

    # Update display
    root.update_idletasks()
    root.update()

    print("\nYou should see 5 bright colored squares on your screen.")
    print("They will disappear after 5 seconds...")

    # Wait 5 seconds then cleanup
    def cleanup():
        print("Cleaning up highlights...")
        for highlight in highlights:
            try:
                highlight.destroy()
            except Exception:
                pass
        root.quit()

    root.after(5000, cleanup)
    root.mainloop()

    print("Test complete.")


if __name__ == "__main__":
    test_multiple_highlights()
