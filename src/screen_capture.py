import cv2
import numpy as np
from PIL import ImageGrab

def capture_screen(region=None):
    if region:
        x, y, width, height = region
        screen = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    else:
        screen = ImageGrab.grab()
    
    screen_np = np.array(screen)
    screen_rgb = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)
    return screen_rgb