import tkinter as tk
import pyautogui
import PIL.ImageGrab
import time

x, y = -300, 400
border_size = 10  # Size of the border around the pixel

root = tk.Tk()
root.attributes("-topmost", True)
root.overrideredirect(True)
root.geometry(f"{border_size}x{border_size}+{x-border_size//2}+{y-border_size//2}")
root.wm_attributes("-transparentcolor", "white")

canvas = tk.Canvas(
    root, width=border_size, height=border_size, highlightthickness=0, bg="white"
)
canvas.pack()
canvas.create_rectangle(0, 0, border_size, border_size, outline="red", width=2)
# Grab color using pyautogui
start_time = time.time()
pixel_color_pg = pyautogui.pixel(x, y)
time_pg = time.time() - start_time

# Grab color using PIL
start_time = time.time()
img = PIL.ImageGrab.grab(bbox=(x, y, x + 2, y + 2))
pixel_color_pil = img.getpixel((0, 0))
time_pil = time.time() - start_time


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


print("pyautogui:")
print(f"  RGB: {pixel_color_pg}")
print(f"  HEX: {rgb_to_hex(pixel_color_pg)}")
print(f"  Time: {time_pg:.6f} seconds")

print("PIL:")
print(f"  RGB: {pixel_color_pil}")
print(f"  HEX: {rgb_to_hex(pixel_color_pil)}")
print(f"  Time: {time_pil:.6f} seconds")
root.after(10000, root.destroy)
root.mainloop()
