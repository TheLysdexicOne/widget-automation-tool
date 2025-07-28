import pyautogui
import sys
import signal
import tkinter as tk

# =============================================
# CONFIGURATION VARIABLES - EDIT THESE
# =============================================
START_X = -1280
START_Y = 720
TARGET_COLOR = (15, 15, 15)  # RGB values for border color
FILL_COLOR = (0, 95, 149)  # RGB values for fill color
ENABLE_HIGHLIGHTING = True  # Set to False to disable visual highlights
TOLERANCE = 10  # Color matching tolerance
MIN_BOX_SIZE = 16  # Minimum box size requirement
MAX_SCAN_DISTANCE = 2000  # Maximum pixels to scan downward

# =============================================
# GLOBAL VARIABLES
# =============================================
stop_scanning = False
tk_root = None


def setup_tkinter():
    """Setup tkinter root window for highlighting."""
    global tk_root
    if tk_root is None:
        tk_root = tk.Tk()
        tk_root.withdraw()  # Hide the main window
        tk_root.attributes("-topmost", True)
    return tk_root


def signal_handler(sig, frame):
    """Handle Ctrl+C for immediate exit."""
    print("\nCtrl+C pressed - Exiting immediately!")
    sys.exit(0)


# Set up signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


class VisualScanner:
    """Visual scanning test with simple result highlighting."""

    def __init__(self, enable_highlighting=True):
        self.tolerance = TOLERANCE
        self.enable_highlighting = enable_highlighting
        self.highlight_windows = []  # Store highlight windows if needed

    def color_matches(self, pixel, target, tolerance=None):
        """Check if pixel color matches target within tolerance."""
        if tolerance is None:
            tolerance = self.tolerance
        return all(abs(pixel[i] - target[i]) <= tolerance for i in range(3))

    def create_simple_highlight(self, x, y, color=(255, 0, 0), size=4):
        """Create a simple colored square at the specified pixel (if highlighting enabled)."""
        if not self.enable_highlighting:
            return

        try:
            global tk_root
            if tk_root is None:
                setup_tkinter()

            # Create a 1-pixel highlight to avoid interfering with scanning
            highlight = tk.Toplevel(tk_root)
            highlight.overrideredirect(True)
            highlight.attributes("-topmost", True)
            highlight.attributes("-alpha", 1.0)  # Completely opaque

            # 1 pixel size to avoid interference
            pixel_size = 1
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            highlight.configure(bg=hex_color)

            # Position exactly at the pixel being scanned
            highlight.geometry(f"{pixel_size}x{pixel_size}+{x}+{y}")

            # Force it to show up immediately
            highlight.lift()
            highlight.focus_force()
            highlight.update_idletasks()
            highlight.update()

            # Store reference and schedule cleanup
            self.highlight_windows.append(highlight)

            def close_highlight():
                try:
                    if highlight.winfo_exists():
                        highlight.destroy()
                        if highlight in self.highlight_windows:
                            self.highlight_windows.remove(highlight)
                except Exception:
                    pass

            # Keep it visible for a shorter time
            if tk_root:
                tk_root.after(100, close_highlight)

        except Exception as e:
            print(f"  → Highlight FAILED at ({x}, {y}): {e}")
            # Console fallback
            print(f"  → Console highlight at ({x}, {y}) with color {color}")

    def cleanup_highlights(self):
        """Clean up any remaining highlight windows."""
        try:
            for window in self.highlight_windows:
                if window.winfo_exists():
                    window.destroy()
            self.highlight_windows.clear()
        except Exception:
            pass

    def scan_downward_for_color(self, start_x, start_y, target_color, max_distance=100):
        """Scan downward from start point until target color is found."""
        print(f"Scanning downward from ({start_x}, {start_y}) for color {target_color}")

        for distance in range(max_distance):
            global stop_scanning
            if stop_scanning:
                print("Scan stopped by user")
                return None

            scan_x = start_x
            scan_y = start_y + distance

            try:
                pixel_color = pyautogui.pixel(scan_x, scan_y)
                print(f"Pixel at ({scan_x}, {scan_y}): {pixel_color} (target: {target_color})")

                if self.color_matches(pixel_color, target_color):
                    print(f"Found target color at ({scan_x}, {scan_y})")
                    self.create_simple_highlight(scan_x, scan_y, color=(0, 255, 0))  # Green - found target
                    return (scan_x, scan_y)
                else:
                    self.create_simple_highlight(scan_x, scan_y, color=(255, 0, 0))  # Red - not target
            except Exception as e:
                print(f"Error scanning pixel: {e}")
                break

        print("Target color not found in downward scan")
        return None

    def find_box_optimized(self, start_x, start_y, target_color, min_size=16):
        """Trace perimeter: left → down → right → up → back to left."""
        print(f"Starting box search from ({start_x}, {start_y})")

        # Start tracing from the found point
        current_x = start_x
        current_y = start_y

        # Step 1: Go LEFT to find left edge
        print("Tracing LEFT...")
        while current_x > start_x - 300:  # Safety limit
            try:
                pixel_color = pyautogui.pixel(current_x - 1, current_y)
                if self.color_matches(pixel_color, target_color):
                    current_x -= 1
                    self.create_simple_highlight(current_x, current_y, color=(255, 255, 0))  # Yellow - tracing
                else:
                    break
            except Exception:
                break

        left_edge = current_x
        print(f"Found left edge at x={left_edge}")
        self.create_simple_highlight(left_edge, current_y, color=(255, 0, 255))  # Magenta - corner

        # Step 2: Go DOWN from left edge to find bottom-left corner
        print("Tracing DOWN from left edge...")
        while current_y < start_y + 100:  # Safety limit
            try:
                pixel_color = pyautogui.pixel(current_x, current_y + 1)
                if self.color_matches(pixel_color, target_color):
                    current_y += 1
                    self.create_simple_highlight(current_x, current_y, color=(255, 255, 0))  # Yellow - tracing
                else:
                    break
            except Exception:
                break

        bottom_edge = current_y
        print(f"Found bottom edge at y={bottom_edge}")
        self.create_simple_highlight(current_x, bottom_edge, color=(255, 0, 255))  # Magenta - corner

        # Step 3: Go RIGHT from bottom-left to find bottom-right corner
        print("Tracing RIGHT from bottom edge...")
        while current_x < start_x + 300:  # Safety limit
            try:
                pixel_color = pyautogui.pixel(current_x + 1, current_y)
                if self.color_matches(pixel_color, target_color):
                    current_x += 1
                    self.create_simple_highlight(current_x, current_y, color=(255, 255, 0))  # Yellow - tracing
                else:
                    break
            except Exception:
                break

        right_edge = current_x
        print(f"Found right edge at x={right_edge}")
        self.create_simple_highlight(right_edge, current_y, color=(255, 0, 255))  # Magenta - corner

        # Step 4: Go UP from bottom-right to find top-right corner
        print("Tracing UP from right edge...")
        while current_y > start_y - 100:  # Safety limit
            try:
                pixel_color = pyautogui.pixel(current_x, current_y - 1)
                if self.color_matches(pixel_color, target_color):
                    current_y -= 1
                    self.create_simple_highlight(current_x, current_y, color=(255, 255, 0))  # Yellow - tracing
                else:
                    break
            except Exception:
                break

        top_edge = current_y
        print(f"Found top edge at y={top_edge}")
        self.create_simple_highlight(current_x, top_edge, color=(255, 0, 255))  # Magenta - corner

        # Step 5: Go back LEFT from top-right to complete the perimeter (verification)
        print("Verifying by tracing LEFT along top edge...")
        verification_x = current_x
        while verification_x > left_edge:
            try:
                pixel_color = pyautogui.pixel(verification_x - 1, current_y)
                if self.color_matches(pixel_color, target_color):
                    verification_x -= 1
                    self.create_simple_highlight(verification_x, current_y, color=(0, 255, 0))  # Green - verification
                else:
                    print(f"Warning: Top edge verification failed at x={verification_x}")
                    break
            except Exception:
                break

        # Calculate final dimensions
        width = right_edge - left_edge + 1
        height = bottom_edge - top_edge + 1

        print(f"Perimeter traced box: ({left_edge}, {top_edge}) size {width}x{height}")

        # Check minimum size requirement
        if width < min_size or height < min_size:
            print(f"Box too small ({width}x{height}), minimum required: {min_size}x{min_size}")
            self.create_simple_highlight(start_x, start_y, color=(255, 165, 0))  # Orange - too small
            return None

        # Highlight all four corners of the final box
        corners = [
            (left_edge, top_edge),
            (right_edge, top_edge),
            (left_edge, bottom_edge),
            (right_edge, bottom_edge),
        ]
        for corner in corners:
            self.create_simple_highlight(corner[0], corner[1], color=(0, 255, 255))  # Cyan - final corners

        return (left_edge, top_edge, width, height)

    def validate_fill(self, box_bounds, acceptable_colors):
        """Check if box interior matches acceptable fill colors."""
        if not box_bounds:
            return False

        x, y, width, height = box_bounds
        sample_points = [
            (x + width // 4, y + height // 4),
            (x + width // 2, y + height // 2),
            (x + 3 * width // 4, y + 3 * height // 4),
        ]

        print("Validating fill colors...")
        for px, py in sample_points:
            try:
                pixel_color = pyautogui.pixel(px, py)
                matches_any = any(self.color_matches(pixel_color, color) for color in acceptable_colors)

                if not matches_any:
                    print(f"Fill validation failed at ({px}, {py}) - got {pixel_color}")
                    self.create_simple_highlight(px, py, color=(255, 100, 100))  # Light red for fail
                    return False
                else:
                    self.create_simple_highlight(px, py, color=(100, 255, 100))  # Light green for pass
            except Exception:
                continue

        print("Fill validation passed!")
        return True


def run_visual_scan_test():
    """Main test function."""
    print("=" * 60)
    print("VISUAL SCANNER TEST")
    print("=" * 60)
    print(f"Starting scan from: ({START_X}, {START_Y})")
    print(f"Target color: {TARGET_COLOR}")
    print(f"Fill color: {FILL_COLOR}")
    print(f"Highlighting enabled: {ENABLE_HIGHLIGHTING}")
    print(f"Tolerance: {TOLERANCE}")
    print(f"Min box size: {MIN_BOX_SIZE}x{MIN_BOX_SIZE}")
    print(f"Max scan distance: {MAX_SCAN_DISTANCE}")
    print("=" * 60)

    # Create acceptable fill colors (target color plus some variations)
    acceptable_fill_colors = [
        FILL_COLOR,
        TARGET_COLOR,  # Include target color as acceptable fill
        # Add some tolerance variations
        tuple(max(0, min(255, c + 10)) for c in FILL_COLOR),  # Slightly lighter
        tuple(max(0, min(255, c - 10)) for c in FILL_COLOR),  # Slightly darker
    ]

    # Create scanner
    scanner = VisualScanner(enable_highlighting=ENABLE_HIGHLIGHTING)

    print("Starting visual scan test...")
    if ENABLE_HIGHLIGHTING:
        print("Watch your screen - pixels will be highlighted as they're scanned!")

    try:
        # Step 1: Scan downward for target color and find valid box
        start_distance = 0
        found_point = None
        box_bounds = None

        while start_distance < MAX_SCAN_DISTANCE:
            found_point = scanner.scan_downward_for_color(
                START_X, START_Y + start_distance, TARGET_COLOR, max_distance=MAX_SCAN_DISTANCE - start_distance
            )

            if found_point:
                # Step 2: Measure box boundaries using optimized approach
                box_bounds = scanner.find_box_optimized(found_point[0], found_point[1], TARGET_COLOR)

                if box_bounds:
                    # Check if height is exactly 32px
                    _, _, width, height = box_bounds
                    if height == 32:
                        # Found a box with correct height - we're done!
                        print(f"✓ Found valid 32px height box: {width}x{height}")
                        break
                    else:
                        # Wrong height, continue scanning
                        print(f"✗ Box height {height}px (need 32px), continuing scan...")
                        box_bounds = None  # Reset so we keep looking
                        start_distance = found_point[1] - START_Y + 1
                        print(f"Continuing scan from distance {start_distance}")
                else:
                    # Box was too small, continue scanning from after this point
                    start_distance = found_point[1] - START_Y + 1
                    print(f"Box too small, continuing scan from distance {start_distance}")
            else:
                # No more target colors found
                break

        # Show results
        print("\n" + "=" * 60)
        print("SCAN RESULTS")
        print("=" * 60)

        if box_bounds:
            # Step 3: Validate height requirement (must be exactly 32 pixels)
            _, _, width, height = box_bounds
            if height != 32:
                print(f"✗ Height validation FAILED: Found {height}px, required exactly 32px")
                print(f"✗ Box rejected at: ({box_bounds[0]}, {box_bounds[1]})")
                print(f"✗ Size: {box_bounds[2]}x{box_bounds[3]}")
            else:
                # Step 4: Validate fill
                fill_valid = scanner.validate_fill(box_bounds, acceptable_fill_colors)

                print(f"✓ Box found at: ({box_bounds[0]}, {box_bounds[1]})")
                print(f"✓ Size: {box_bounds[2]}x{box_bounds[3]}")
                print("✓ Height validation: PASSED (32px)")
                print(f"✓ Fill validation: {'PASSED' if fill_valid else 'FAILED'}")
        elif found_point:
            print("✗ Found target color but no boxes met minimum size requirement")
        else:
            print("✗ Target color not found in downward scan")

    except KeyboardInterrupt:
        print("\nScan interrupted by user (Ctrl+C)")
    finally:
        # Clean up any remaining highlight windows
        scanner.cleanup_highlights()

    print("=" * 60)
    return True


def main():
    """Main function - run the scanner test."""
    print("Scanner Test Script")
    print("Press Ctrl+C at any time to exit immediately")
    print()

    # Initialize tkinter for highlighting (hidden root window)
    global tk_root
    if ENABLE_HIGHLIGHTING:
        try:
            tk_root = setup_tkinter()
            print("Visual highlighting enabled - you'll see colored squares during scanning")
        except Exception:
            print("Warning: Could not initialize GUI highlighting, falling back to console output")

    try:
        run_visual_scan_test()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up tkinter if it was initialized
        if tk_root:
            try:
                tk_root.destroy()
            except Exception:
                pass

    print("Test complete.")


if __name__ == "__main__":
    main()
