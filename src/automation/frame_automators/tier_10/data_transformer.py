"""
Data Transformer Automator (Frame ID: 10.2)
Handles automation for the Data Transformer frame in WidgetInc.
"""

from typing import Any, Dict, List, Optional
from automation.base_automator import BaseAutomator


class DataTransformerAutomator(BaseAutomator):
    """Tic-Tac-Toe automation."""

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
        # Safety check: don't place O on occupied squares
        if self.board[idx] is not None:
            self.log_error(f"Attempted to place O on occupied square {idx} (contains: {self.board[idx]})")
            return

        x, y = list(self.grid_centers)[idx]
        self.moveTo(x, y)
        self.click()
        self.board[idx] = "O"

    """Automation logic for Data Transformer (Frame 10.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def scan_board(self):
        # Scan for Xs; Os are tracked by our own moves
        for i, (x, y) in enumerate(self.grid_centers):
            # Skip positions where we placed O - never overwrite our own moves
            if self.board[i] == "O":
                continue

            color = self.pixel(x, y)
            if color in self.x_colors:
                self.board[i] = "X"
            else:
                # No X detected - this position is empty
                self.board[i] = None

    def run_automation(self):
        self.grid_centers = list(self.frame_data["interactions"]["board"].values())
        self.x_colors = self.frame_data["colors"]["x_colors"]
        self.board: List[Optional[str]] = [None] * 9

        while self.should_continue:
            self.scan_board()

            # Check for win or draw
            if (
                self.is_winner(self.board, "O")
                or self.is_winner(self.board, "X")
                or all(v is not None for v in self.board)
            ):
                if self.is_winner(self.board, "O"):
                    self.log_info("We won!")
                elif self.is_winner(self.board, "X"):
                    self.log_info("Computer won!")
                else:
                    self.log_info("Draw!")

                self.board = [None] * 9
                if not self.sleep(0.5):
                    break
                continue

            # If it's our turn (there are more Xs or equal Xs to Os, we play O)
            x_count = self.board.count("X")
            o_count = self.board.count("O")

            if o_count <= x_count:
                _, move = self.minimax(self.board[:], True)
                if move is not None:
                    self.place_o(move)
                else:
                    self.log_error("Minimax returned no valid move")

            if not self.sleep(0.5):
                break
