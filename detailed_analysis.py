"""
Detailed screenshot analysis to find actual text regions and optimize detection zones.
"""

import os
from PIL import Image, ImageDraw
import json


def calculate_playable_area(window_width, window_height):
    """Calculate the playable area coordinates within a window."""
    # Playable area maintains 3:2 aspect ratio and is centered
    target_ratio = 3.0 / 2.0  # 1.5
    window_ratio = window_width / window_height

    if window_ratio > target_ratio:
        # Window is wider than target - black bars on sides
        playable_height = window_height
        playable_width = int(playable_height * target_ratio)
        playable_x = (window_width - playable_width) // 2
        playable_y = 0
    else:
        # Window is taller than target - black bars on top/bottom
        playable_width = window_width
        playable_height = int(playable_width / target_ratio)
        playable_x = 0
        playable_y = (window_height - playable_height) // 2

    return {
        "x": playable_x,
        "y": playable_y,
        "width": playable_width,
        "height": playable_height,
    }


def analyze_for_text_regions(image_path, output_dir="analysis_output"):
    """Analyze screenshot for potential text regions and create visual overlay."""
    try:
        img = Image.open(image_path)
        width, height = img.size

        # Calculate playable area
        playable = calculate_playable_area(width, height)

        print(f"\n📸 {os.path.basename(image_path)}")
        print(f"   Window: {width}x{height}")
        print(
            f"   Playable area: {playable['width']}x{playable['height']} at ({playable['x']}, {playable['y']})"
        )

        # Create a copy for drawing overlay
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)

        # Draw playable area boundary
        draw.rectangle(
            [
                playable["x"],
                playable["y"],
                playable["x"] + playable["width"],
                playable["y"] + playable["height"],
            ],
            outline="red",
            width=3,
        )

        # Crop to playable area for text analysis
        playable_img = img.crop(
            (
                playable["x"],
                playable["y"],
                playable["x"] + playable["width"],
                playable["y"] + playable["height"],
            )
        )

        # Convert to grayscale for analysis
        gray = playable_img.convert("L")

        # Look for bright text regions (assuming white text on darker backgrounds)
        # White text would have high brightness values
        pixels = list(gray.getdata())
        bright_pixels = [p for p in pixels if p > 200]  # Bright pixels (potential text)

        print(
            f"   Bright pixels (potential text): {len(bright_pixels)}/{len(pixels)} ({len(bright_pixels)/len(pixels)*100:.1f}%)"
        )

        # Analyze potential text regions within playable area
        pw, ph = playable_img.size
        regions = {
            "top_ui": (0, 0, pw, ph // 8),  # Top UI bar
            "title_area": (pw // 4, ph // 8, 3 * pw // 4, ph // 3),  # Title/dialog area
            "center_content": (
                pw // 8,
                ph // 3,
                7 * pw // 8,
                2 * ph // 3,
            ),  # Main content
            "bottom_ui": (0, 7 * ph // 8, pw, ph),  # Bottom UI
            "left_panel": (0, ph // 4, pw // 4, 3 * ph // 4),  # Left sidebar
            "right_panel": (3 * pw // 4, ph // 4, pw, 3 * ph // 4),  # Right sidebar
        }

        text_regions = {}
        for region_name, (x1, y1, x2, y2) in regions.items():
            region_img = gray.crop((x1, y1, x2, y2))
            pixels = list(region_img.getdata())

            # Count bright pixels (potential text)
            bright_count = sum(1 for p in pixels if p > 200)
            bright_percent = bright_count / len(pixels) * 100

            # Count very bright pixels (definitely text)
            very_bright_count = sum(1 for p in pixels if p > 240)
            very_bright_percent = very_bright_count / len(pixels) * 100

            text_regions[region_name] = {
                "bright_percent": bright_percent,
                "very_bright_percent": very_bright_percent,
                "coordinates": (x1, y1, x2, y2),
            }

            print(
                f"   {region_name}: {bright_percent:.1f}% bright, {very_bright_percent:.1f}% very bright"
            )

            # Draw region boundaries on overlay
            abs_x1 = playable["x"] + x1
            abs_y1 = playable["y"] + y1
            abs_x2 = playable["x"] + x2
            abs_y2 = playable["y"] + y2

            color = "yellow" if very_bright_percent > 2 else "blue"
            draw.rectangle([abs_x1, abs_y1, abs_x2, abs_y2], outline=color, width=2)

        # Save analysis overlay
        os.makedirs(output_dir, exist_ok=True)
        overlay_path = os.path.join(
            output_dir, f"analysis_{os.path.basename(image_path)}"
        )
        overlay.save(overlay_path)
        print(f"   Overlay saved: {overlay_path}")

        return {
            "filename": os.path.basename(image_path),
            "playable_area": playable,
            "text_regions": text_regions,
        }

    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")
        return None


def main():
    """Analyze all screenshots and suggest optimal detection zones."""
    screenshots_dir = "assets/backgrounds/sample_screenshots"

    if not os.path.exists(screenshots_dir):
        print(f"❌ Directory not found: {screenshots_dir}")
        return

    print("🔍 Analyzing screenshots for text detection zones...")

    results = []
    for filename in os.listdir(screenshots_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(screenshots_dir, filename)
            result = analyze_for_text_regions(path)
            if result:
                results.append(result)

    # Aggregate results to suggest optimal zones
    if results:
        print(f"\n📊 Optimization Suggestions:")

        # Find regions with consistently high text content
        region_names = results[0]["text_regions"].keys()
        for region_name in region_names:
            avg_bright = sum(
                r["text_regions"][region_name]["bright_percent"] for r in results
            ) / len(results)
            avg_very_bright = sum(
                r["text_regions"][region_name]["very_bright_percent"] for r in results
            ) / len(results)

            if avg_very_bright > 1.0:  # Good text candidate
                print(
                    f"   ✅ {region_name}: {avg_bright:.1f}% bright, {avg_very_bright:.1f}% very bright - Good for text detection"
                )
            elif avg_bright > 5.0:  # Potential text area
                print(
                    f"   ⚠️  {region_name}: {avg_bright:.1f}% bright, {avg_very_bright:.1f}% very bright - Potential text area"
                )
            else:
                print(
                    f"   ❌ {region_name}: {avg_bright:.1f}% bright, {avg_very_bright:.1f}% very bright - Low text probability"
                )


if __name__ == "__main__":
    main()
