import pyautogui
import time
import json
import os
from PIL import ImageGrab

# Define scan area (change as needed)
x1, y1 = -2526, 100
x2, y2 = -2488, 800

x_offset = 2560


def rgb_key(rgb):
    return f"({rgb[0]:03},{rgb[1]:03},{rgb[2]:03})"


# Method 1: PIL ImageGrab with x_offset (for all_screens)
start1 = time.time()
full_img1 = ImageGrab.grab(all_screens=True)
region_box1 = (x1 + x_offset, y1, x2 + x_offset, y2)
region_img1 = full_img1.crop(region_box1)
pixels1 = {}
for y in range(y2 - y1):
    for x in range(x2 - x1):
        rgb = region_img1.getpixel((x, y))
        key = rgb_key(rgb)
        pixels1[key] = pixels1.get(key, 0) + 1
end1 = time.time()

# Save the region screenshot for visual comparison
img_dir = os.path.dirname(__file__)
region_img1.save(os.path.join(img_dir, "pag_offset.png"))
region_img1.convert("RGB").save(os.path.join(img_dir, "pag_offset.jpg"), quality=95)

# Method 2: PIL ImageGrab with bbox and all_screens=True, no offset
start2 = time.time()
bbox = (x1, y1, x2, y2)
region_img2 = ImageGrab.grab(bbox=bbox, all_screens=True)
pixels2 = {}
for y in range(y2 - y1):
    for x in range(x2 - x1):
        rgb = region_img2.getpixel((x, y))
        key = rgb_key(rgb)
        pixels2[key] = pixels2.get(key, 0) + 1
end2 = time.time()

# Save the region screenshot for visual comparison
region_img2.save(os.path.join(img_dir, "pag_bbox.png"))
region_img2.convert("RGB").save(os.path.join(img_dir, "pag_bbox.jpg"), quality=95)

# Raw pyautogui.pixel method
# start2 = time.time()
# pixels2 = {}
# for y in range(y1, y2):
#     for x in range(x1, x2):
#         rgb = pyautogui.pixel(x, y)
#         key = rgb_key(rgb)
#         pixels2[key] = pixels2.get(key, 0) + 1
# end2 = time.time()


result = {
    "imagegrab_offset": {
        "start": f"{x1 + x_offset}, {y1}",
        "end": f"{x2 + x_offset}, {y2}",
        "time": f"{end1 - start1:.4f}",
        "pixels": pixels1,
    },
    "imagegrab_bbox": {"start": f"{x1}, {y1}", "end": f"{x2}, {y2}", "time": f"{end2 - start2:.4f}", "pixels": pixels2},
}

out_path = os.path.join(os.path.dirname(__file__), "output.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
