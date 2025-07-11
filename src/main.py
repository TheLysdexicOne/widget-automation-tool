import sys
import time
from src.gui.menu import MinigameMenu
from src.mouse_control import move_mouse_to, click_mouse
from src.screen_capture import capture_screen
from src.text_recognition import extract_text
from src.game_logic import determine_minigame

def main():
    menu = MinigameMenu()
    menu.show()

    while True:
        screen_image = capture_screen()
        recognized_text = extract_text(screen_image)
        current_minigame = determine_minigame(recognized_text)

        if current_minigame:
            menu.select_mini_game(current_minigame)
            # Simulate mouse movements and clicks for the selected minigame
            # This is where you would implement the specific logic for each minigame
            # For example:
            # move_mouse_to(x, y)
            # click_mouse()

        time.sleep(1)  # Adjust the sleep time as necessary

        if menu.escape_pressed():
            break

if __name__ == "__main__":
    main()