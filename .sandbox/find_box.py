# type: ignore

from termcolor import colored

from PIL import ImageGrab


class FindPixel:
    def __init__(self):
        # Set offset due to left monitor
        self.x_offset = 2560
        self.start = (-1280, 720)
        self.target_color = (15, 15, 15)
        self.tolerance = 10
        self.max_y = 1400
        self.pos = (self.start[0] + self.x_offset, self.start[1])
        self.all_matches = []
        self.screenshot = ImageGrab.grab(all_screens=True)
        self.pixel = None
        self.match = False

    def match_pixel(self):
        # self.pixel should be [self.pos, (r, g, b)]
        if isinstance(self.pixel, (int, float)):
            self.pixel = (int(self.pixel),) * 3
        # Accept both [pos, (r,g,b)] and (r,g,b)
        rgb = None
        if isinstance(self.pixel, (list, tuple)):
            if len(self.pixel) == 2 and isinstance(self.pixel[1], (list, tuple)):
                rgb = self.pixel[1]
            elif len(self.pixel) >= 3 and all(isinstance(x, int) for x in self.pixel[:3]):
                rgb = self.pixel[:3]
        if rgb is None or len(rgb) < 3:
            print(f"Scanned: {self.pos} -> {self.pixel} Match: False")
            return False
        # Compare each channel with tolerance
        self.match = all(abs(int(rgb[i]) - self.target_color[i]) <= self.tolerance for i in range(3))
        actual_pos = (self.pos[0] - self.x_offset, self.pos[1])
        if self.match:
            print(colored(f"Scanned: {actual_pos} -> {rgb} Match: True", "green"))
        else:
            print(f"Scanned: {actual_pos} -> {rgb} Match: False")
        return self.match

    def scan_pixel(self):
        scan = self.screenshot.getpixel(self.pos)
        self.pixel = [self.pos, (scan[0], scan[1], scan[2])]
        self.match_pixel()

    def down(self, pixels=1):
        x, y = self.pos
        self.pos = (x, y + pixels)
        self.scan_pixel()

    def up(self, pixels=1):
        x, y = self.pos
        self.pos = (x, y - pixels)
        self.scan_pixel()

    def left(self, pixels=1):
        x, y = self.pos
        self.pos = (x - pixels, y)
        self.scan_pixel()

    def right(self, pixels=1):
        x, y = self.pos
        self.pos = (x + pixels, y)
        self.scan_pixel()


if __name__ == "__main__":
    fp = FindPixel()

    while not fp.match:
        fp.down(4)

    while fp.match:
        fp.up(1)

    while not fp.match:
        fp.down(1)

    while fp.match:
        fp.left(16)

    while not fp.match:
        fp.right(1)
        top_left = fp.pos

    while fp.match:
        fp.down(4)

    while not fp.match:
        fp.up(1)
        bottom_left = fp.pos

    while fp.match:
        fp.right(16)

    while not fp.match:
        fp.left(1)
        bottom_right = fp.pos

    while fp.match:
        fp.up(4)

    while not fp.match:
        fp.down(1)
        top_right = fp.pos

    x1, y1 = top_left
    x2, y2 = bottom_right

    x = x1 - fp.x_offset

    width = x2 - x1 + 1
    height = y2 - y1 + 1

    center_x = ((x1 + x2 + 1) / 2) - fp.x_offset
    center_y = (y1 + y2 + 1) / 2

    print(f"Box starts at ({x}, {y1} and dimensions of {width} by {height}.)")
    print(f"Center is at ({center_x}, {center_y}).")
