from typing import List, Tuple, Dict, Optional
from .board import Board
from .move_validator import MoveValidator

class GameState:
    """
    Quản lý trạng thái game: Wrapper kết hợp logic của Board + Luật chơi (Lượt, Thắng thua).
    """
    def __init__(self, game_type: str = 'chess'):
        self.board = Board(game_type)
        self.current_turn = 'white'  # White/Red đi trước
        
        # --- LOGIC ONLINE ---
        self.my_color: Optional[str] = None # 'white' hoặc 'black'. None = Chơi 2 người 1 máy
        
        self.history: List[Dict[str, Tuple[int, int]]] = [] 
        self.validator = MoveValidator(game_type)
        self.winner: str = None  # 'white', 'black', or 'draw'
        self.is_check = False
        self.is_checkmate = False

    # =========================================================================
    # [QUAN TRỌNG] CÁC HÀM ỦY QUYỀN (PROXY) CHO BOARD UI GỌI KHÔNG BỊ LỖI
    # =========================================================================
    @property
    def rows(self):
        return self.board.rows

    @property
    def cols(self):
        return self.board.cols

    @property
    def game_type(self):
        return self.board.game_type

    @property
    def game_over(self):
        # [GIẢI THÍCH] Đây là thuộc tính chỉ đọc (Read-only).
        # Nó tự động trả về True nếu winner có giá trị.
        return self.winner is not None

    def get_piece(self, pos):
        return self.board.get_piece(pos)

    def get_board_state(self):
        return self.board.get_board_state()

    # BoardUI gọi 'move_piece', ta trỏ nó về hàm xử lý logic 'make_move'
    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        return self.make_move(from_pos, to_pos)
    # =========================================================================

    # --- CÁC HÀM HỖ TRỢ ONLINE ---
    def set_player_color(self, color: str):
        """Thiết lập màu cho người chơi trên máy này."""
        self.my_color = color

    def is_my_turn(self) -> bool:
        """Kiểm tra xem có phải lượt của người chơi local không."""
        if self.my_color is None:
            return True
        return self.current_turn == self.my_color

    # -----------------------------------

    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Thực hiện nước đi nếu hợp lệ, cập nhật trạng thái."""
        
        # 1. Kiểm tra game over
        if self.winner:
            return False

        # 2. Kiểm tra quân cờ có tồn tại và đúng màu lượt đi không
        piece = self.board.get_piece(from_pos)
        if not piece:
            return False
        
        # Logic chặt chẽ: Phải đúng lượt (current_turn) mới được đi
        if piece.color != self.current_turn:
            return False

        # 3. Kiểm tra nước đi hợp lệ (MoveValidator)
        if self.validator.is_valid_move(self.board, from_pos, to_pos, self.current_turn):
            # Lưu lịch sử
            self.history.append({'from': from_pos, 'to': to_pos})
            
            # Xác định quân bị ăn (nếu có)
            captured = self.board.get_piece(to_pos)
            
            # Di chuyển quân cờ
            self.board.move_piece(from_pos, to_pos)

            # --- [FIX LỖI .type] LOGIC ĂN VUA LÀ THẮNG LUÔN ---
            # Sửa .type thành .symbol
            if captured and captured.symbol.upper() in ['K', 'G']:
                self.winner = self.current_turn
                return True
            # ----------------------------------------

            # Kiểm tra check/checkmate (Nếu chưa thắng do ăn vua)
            if not self.winner:
                opponent = self.opponent_color()
                self.is_check = self.validator.is_in_check(self.board, opponent)
                
                # Nếu muốn logic Checkmate chuẩn thì bật dòng này
                self.is_checkmate = self.is_check and self.validator.is_checkmate(self.board, opponent)

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
        current_type = self.board.game_type
        current_color = self.my_color
        self.__init__(current_type)
        self.my_color = current_color