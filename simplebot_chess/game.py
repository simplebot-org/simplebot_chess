"""Game board."""

from io import StringIO

import chess
import chess.pgn

pieces = {
    "r": "♜",
    "n": "♞",
    "b": "♝",
    "q": "♛",
    "k": "♚",
    "p": "♟",
    "R": "♖",
    "N": "♘",
    "B": "♗",
    "Q": "♕",
    "K": "♔",
    "P": "♙",
    ".": " ",
}


class Board:
    """Class representing a chess board."""

    def __init__(self, game: str = None, p1: str = None, p2: str = None) -> None:
        if game:
            self.game = chess.pgn.read_game(StringIO(game))
            self.board = self.game.board()
            for move in self.game.mainline_moves():
                self.board.push(move)
        else:
            assert None not in (p1, p2)
            self.game = chess.pgn.Game()
            self.game.headers["White"] = p1
            self.game.headers["Black"] = p2
            self.board = self.game.board()

    def __str__(self) -> str:
        return self.export()

    @property
    def white(self) -> str:
        return self.game.headers["White"]

    @property
    def black(self) -> str:
        return self.game.headers["Black"]

    @property
    def turn(self) -> str:
        if self.board.turn == chess.WHITE:
            return self.white
        return self.black

    def to_array(self) -> list:
        return [ln.split() for ln in str(self.board).splitlines()]

    def export(self) -> str:
        return str(self.game)

    def move(self, mv: str) -> None:
        try:
            m = self.board.push_san(mv)
        except ValueError:
            m = self.board.push_uci(mv)
        self.game.end().add_variation(m)

    def result(self) -> str:
        return self.board.result()
