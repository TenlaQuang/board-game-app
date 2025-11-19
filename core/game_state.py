# core/game_state.py
from typing import List, Tuple, Dict, Optional
from .board import Board
from .move_validator import MoveValidator

class GameState:
    """
    Quản lý trạng thái game: board, lượt chơi, lịch sử, check/mate.
    """
    def __init__(self, game_type: str = 'chess'):
        self.board = Board(game_type)
        self.current_turn = 'white'  # White/Red đi trước
        
        # --- [NEW] LOGIC ONLINE ---
        self.my_color: Optional[str] = None # 'white' hoặc 'black'. None = Chơi 2 người 1 máy
        # --------------------------

        self.history: List[Dict[str, Tuple[int, int]]] = []  # [{'from': (r,c), 'to': (r,c)}]
        self.validator = MoveValidator(game_type)
        self.winner: str = None  # 'white', 'black', or 'draw'
        self.is_check = False
        self.is_checkmate = False

    # --- [NEW] CÁC HÀM HỖ TRỢ ONLINE ---
    def set_player_color(self, color: str):
        """
        Thiết lập màu cho người chơi trên máy này.
        - Host: thường là 'white' (Cờ vua) hoặc 'red' (Cờ tướng - logic mapping là white)
        - Client: thường là 'black'
        """
        self.my_color = color

    def is_my_turn(self) -> bool:
        """
        Kiểm tra xem có phải lượt của người chơi local không.
        Dùng để chặn click chuột khi chưa đến lượt.
        """
        # Nếu chưa set màu (chơi offline 1 máy), thì ai đi cũng được (luôn True)
        if self.my_color is None:
            return True
        return self.current_turn == self.my_color
    # -----------------------------------

    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Thực hiện nước đi nếu hợp lệ, cập nhật trạng thái."""
        
        # Kiểm tra game over
        if self.winner:
            return False

        # Kiểm tra quân cờ có tồn tại và đúng màu lượt đi không
        piece = self.board.get_piece(from_pos)
        if not piece:
            return False
        if piece.color != self.current_turn:
            return False

        # Kiểm tra nước đi hợp lệ (MoveValidator)
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
        # Giữ lại game_type và my_color khi reset
        current_type = self.board.game_type
        current_color = self.my_color
        self.__init__(current_type)
        self.my_color = current_color