def determine_minigame(recognized_text):
    minigames = {
        "Minigame 1": "action_for_minigame_1",
        "Minigame 2": "action_for_minigame_2",
        "Minigame 3": "action_for_minigame_3",
        # Add more minigames as needed
    }

    for minigame_name, action in minigames.items():
        if minigame_name in recognized_text:
            return action

    return None