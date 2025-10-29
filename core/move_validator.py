# core/move_validator.py
from typing import List, Tuple
from .board import Board
from .piece import Piece, King, General

class MoveValidator:
    """
    Validate nước đi, check, checkmate.
    """
    def __init__(self, game_type: str):
        self.game_type = game_type

    def is_valid_move(self, board: Board, from_pos: Tuple[int, int], to_pos: Tuple[int, int], player_color: str) -> bool:
        """Kiểm tra nước đi hợp lệ, không để Vua bị chiếu."""
        piece = board.get_piece(from_pos)
        if not piece or piece.color != player_color:
            return False

        # Lấy moves từ Piece
        possible_moves = piece.valid_moves(board.board, from_pos)
        if to_pos not in possible_moves:
            return False

        # Simulate move để kiểm tra check
        temp_board = Board(board.game_type)
        temp_board.board = [row[:] for row in board.board]  # Copy
        temp_board.move_piece(from_pos, to_pos)

        # Không được để Vua mình bị chiếu sau move
        if self.is_in_check(temp_board, player_color):
            return False

        return True

    def is_in_check(self, board: Board, color: str) -> bool:
        """Kiểm tra Vua/Tướng của color có bị chiếu không."""
        king_pos = board.find_king_pos(color)
        if not king_pos:
            return False

        opponent_color = 'black' if color == 'white' else 'white'
        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if piece and piece.color == opponent_color:
                    if king_pos in piece.valid_moves(board.board, (r, c)):
                        return True
        return False

    def is_checkmate(self, board: Board, color: str) -> bool:
        """Kiểm tra chiếu hết (không có move thoát check)."""
        if not self.is_in_check(board, color):
            return False

        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if piece and piece.color == color:
                    for to_pos in piece.valid_moves(board.board, (r, c)):
                        # Simulate
                        temp_board = Board(board.game_type)
                        temp_board.board = [row[:] for row in board.board]
                        temp_board.move_piece((r, c), to_pos)
                        if not self.is_in_check(temp_board, color):
                            return False
        return True

    # Thêm stalemate, draw nếu cần