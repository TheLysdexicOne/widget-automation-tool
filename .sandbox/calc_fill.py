## bottom = 146, 98
## top = 146, 56
## voltage can be between 1 and 15

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PIL import ImageGrab
from src.utility.window_utils import grid_to_screen_coords


class CalcFill:
    def __init__(self):
        self.vtop = grid_to_screen_coords(146, 56)
        self.vbot = grid_to_screen_coords(146, 98)
        self.fill_color = (72, 237, 56)
        self.x_offset = 2560
        self.screenshot = ImageGrab.grab(all_screens=True)
        self.vtop_coords = (self.vtop[0] + self.x_offset, self.vtop[1])
        self.vbot_coords = (self.vbot[0] + self.x_offset, self.vbot[1])

        self.bar_height = self.vbot_coords[1] - self.vtop_coords[1]

    def fill_level(self):
        for y in range(self.vtop_coords[1], self.vbot_coords[1]):
            print(f"{self.screenshot.getpixel((self.vtop_coords[0], y))}")
            print(f"Checking fill level from {self.vtop_coords} to {self.vbot_coords}")
            if self.screenshot.getpixel((self.vtop_coords[0], y)) == self.fill_color:
                return self.bar_height - (y - self.vtop_coords[1])

    def fill_level_percentage(self):
        level = self.fill_level()
        if level is None:
            return 0
        return (level / self.bar_height) * 100

    def calc_voltage(self):
        charge = round(15 * self.fill_level_percentage() / 100)
        return charge


if __name__ == "__main__":
    cf = CalcFill()
    height = cf.bar_height
    print(f"Height of the fill area: {height} pixels")
    print(f"Actual fill coordinates: {cf.vtop} to {cf.vbot}")
    print(f"Calculated fill coordinates: {cf.vtop_coords} to {cf.vbot_coords}")
    print(f"Fill level: {cf.fill_level()} pixels")
    print(f"Fill level percentage: {cf.fill_level_percentage()}%")
    print(f"Calculated charge: {cf.calc_voltage()}")
