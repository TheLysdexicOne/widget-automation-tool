import pyautogui
import time

def move_mouse_to(x, y, duration=0.25):
    pyautogui.moveTo(x, y, duration)

def click_mouse(x=None, y=None, button='left'):
    if x is not None and y is not None:
        move_mouse_to(x, y)
    pyautogui.click(button=button)

def scroll_mouse(amount):
    pyautogui.scroll(amount)

def double_click_mouse(x=None, y=None):
    if x is not None and y is not None:
        move_mouse_to(x, y)
    pyautogui.doubleClick()