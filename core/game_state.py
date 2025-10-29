# core/game_state.py
from typing import List, Tuple, Dict
from .board import Board
from .move_validator import MoveValidator

class GameState:
    """
    Quản lý trạng thái game: board, lượt chơi, lịch sử, check/mate.
    """
    def __init__(self, game_type: str = 'chess'):
        self.board = Board(game_type)
        self.current_turn = 'white'  # White/Red đi trước
        self.history: List[Dict[str, Tuple[int, int]]] = []  # [{'from': (r,c), 'to': (r,c)}]
        self.validator = MoveValidator(game_type)
        self.winner: str = None  # 'white', 'black', or 'draw'
        self.is_check = False
        self.is_checkmate = False

    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Thực hiện nước đi nếu hợp lệ, cập nhật trạng thái."""
        if self.winner or self.current_turn != self.board.get_piece(from_pos).color if self.board.get_piece(from_pos) else True:
            return False

        if self.validator.is_valid_move(self.board, from_pos, to_pos, self.current_turn):
            # Lưu lịch sử
            self.history.append({'from': from_pos, 'to': to_pos})
            # Di chuyển
            captured = self.board.get_piece(to_pos)
            self.board.move_piece(from_pos, to_pos)

            # Xử lý đặc biệt (promotion, castling, en passant) - thêm sau nếu cần

            # Kiểm tra check/checkmate
            self.is_check = self.validator.is_in_check(self.board, self.opponent_color())
            self.is_checkmate = self.is_check and self.validator.is_checkmate(self.board, self.opponent_color())

            if self.is_checkmate:
                self.winner = self.current_turn

            # Đổi lượt
            self.current_turn = self.opponent_color()
            return True
        return False

    def opponent_color(self) -> str:
        return 'black' if self.current_turn == 'white' else 'white'

    def get_state(self) -> Dict:
        """Trả về trạng thái hiện tại để serialize (network)."""
        return {
            'board': self.board.get_board_state(),
            'turn': self.current_turn,
            'is_check': self.is_check,
            'is_checkmate': self.is_checkmate,
            'winner': self.winner
        }

    def reset(self) -> None:
        """Reset game."""
        self.__init__(self.board.game_type)
        
    