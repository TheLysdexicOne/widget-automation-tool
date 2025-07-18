"""
Screenshot analysis script to understand text placement and optimize detection zones.
"""

import os
from PIL import Image
import json

def analyze_screenshot(image_path):
    """Analyze a screenshot to understand its dimensions and potential text regions."""
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        print(f"\n📸 {os.path.basename(image_path)}")
        print(f"   Resolution: {width}x{height}")
        print(f"   Aspect ratio: {width/height:.2f}")
        
        # Check if this matches our expected playable area ratio (3:2 = 1.5)
        if abs(width/height - 1.5) < 0.1:
            print("   ✅ Matches 3:2 playable area ratio")
        else:
            print("   ⚠️  Different aspect ratio - might be full window")
        
        # Look for potential text regions by examining pixel brightness
        # Convert to grayscale for analysis
        gray = img.convert('L')
        
        # Sample some regions where text might appear
        regions = {
            'top_left': (0, 0, width//4, height//4),
            'top_center': (width//4, 0, 3*width//4, height//4),
            'top_right': (3*width//4, 0, width, height//4),
            'center': (width//4, height//4, 3*width//4, 3*height//4),
            'bottom': (0, 3*height//4, width, height)
        }
        
        for region_name, (x1, y1, x2, y2) in regions.items():
            region_img = gray.crop((x1, y1, x2, y2))
            # Calculate average brightness
            avg_brightness = sum(region_img.getdata()) / len(region_img.getdata())
            print(f"   {region_name}: avg brightness {avg_brightness:.1f}")
        
        return {
            'filename': os.path.basename(image_path),
            'width': width,
            'height': height,
            'aspect_ratio': width/height
        }
        
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")
        return None

def main():
    """Analyze all sample screenshots."""
    screenshots_dir = "assets/backgrounds/sample_screenshots"
    
    if not os.path.exists(screenshots_dir):
        print(f"❌ Directory not found: {screenshots_dir}")
        return
    
    print("🔍 Analyzing sample screenshots for text detection optimization...")
    
    screenshots = []
    for filename in os.listdir(screenshots_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(screenshots_dir, filename)
            result = analyze_screenshot(path)
            if result:
                screenshots.append(result)
    
    print(f"\n📊 Analysis Summary:")
    print(f"   Total screenshots: {len(screenshots)}")
    
    if screenshots:
        widths = [s['width'] for s in screenshots]
        heights = [s['height'] for s in screenshots]
        print(f"   Resolution range: {min(widths)}x{min(heights)} to {max(widths)}x{max(heights)}")
        
        # Check for common resolutions
        common_resolutions = {}
        for s in screenshots:
            res = f"{s['width']}x{s['height']}"
            common_resolutions[res] = common_resolutions.get(res, 0) + 1
        
        print(f"   Common resolutions:")
        for res, count in sorted(common_resolutions.items()):
            print(f"     {res}: {count} screenshot(s)")

if __name__ == "__main__":
    main()
