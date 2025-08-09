"""
Data Transformer Automator (Frame ID: 10.2)
Handles automation for the Data Transformer frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict, List, Optional
from automation.base_automator import BaseAutomator


class DataTransformerAutomator(BaseAutomator):
    def is_winner(self, board, player):
        wins = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],  # rows
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],  # cols
            [0, 4, 8],
            [2, 4, 6],  # diags
        ]
        for line in wins:
            if all(board[i] == player for i in line):
                return True
        return False

    def available_moves(self, board):
        return [i for i, v in enumerate(board) if v is None]

    def minimax(self, board, is_bot):
        # Bot is 'O', opponent is 'X'
        if self.is_winner(board, "O"):
            return 1, None
        if self.is_winner(board, "X"):
            return -1, None
        if all(v is not None for v in board):
            return 0, None
        moves = self.available_moves(board)
        if is_bot:
            best = -float("inf")
            best_move = None
            for move in moves:
                board[move] = "O"
                score, _ = self.minimax(board, False)
                board[move] = None
                if score > best:
                    best = score
                    best_move = move
            return best, best_move
        else:
            best = float("inf")
            best_move = None
            for move in moves:
                board[move] = "X"
                score, _ = self.minimax(board, True)
                board[move] = None
                if score < best:
                    best = score
                    best_move = move
            return best, best_move

    def place_o(self, idx):
        x, y = list(self.grid_centers)[idx]
        pyautogui.moveTo(x, y)
        pyautogui.click()
        self.board[idx] = "O"

    """Automation logic for Data Transformer (Frame 10.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def scan_board(self):
        # Only scan for Xs; Os are tracked by our own moves
        for i, (x, y) in enumerate(self.grid_centers):
            color = pyautogui.pixel(x, y)
            if color in self.x_colors:
                self.board[i] = "X"
            elif self.board[i] != "O":
                self.board[i] = None

    def run_automation(self):
        start_time = time.time()

        self.grid_centers = list(self.frame_data["interactions"].values())
        self.x_colors = self.frame_data["colors"]["x_colors"]
        self.board: List[Optional[str]] = [None] * 9

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            self.scan_board()

            # Check for win or draw
            if (
                self.is_winner(self.board, "O")
                or self.is_winner(self.board, "X")
                or all(v is not None for v in self.board)
            ):
                self.board = [None] * 9
                if not self.sleep(0.5):
                    break
                continue

            # If it's our turn (there are more Xs or equal Xs to Os, we play O)
            if self.board.count("O") <= self.board.count("X"):
                _, move = self.minimax(self.board[:], True)
                if move is not None:
                    self.place_o(move)
            if not self.sleep(0.1):
                break
