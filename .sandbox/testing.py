from typing import Dict


def convert_grid(grid: Dict) -> Dict:
    playable_area = get_playable_area()
    return grid


def get_playable_area():
    return playable_area


miner_btns = {
    "miner1": (32, 33, "red"),  # miner1
    "miner2": (33, 99, "red"),  # miner2
    "miner3": (155, 24, "red"),  # miner3
    "miner4": (158, 98, "red"),  # miner4
}

miner_grid = {key: value[:-1] for key, value in miner_btns.items()}

print(miner_grid)

miner_coords = convert_grid(miner_grid)

print(miner_coords)
