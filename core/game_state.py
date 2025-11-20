from typing import List, Tuple, Dict, Optional
from .board import Board
from .move_validator import MoveValidator
from .piece import Pawn  # Import để kiểm tra quân Tốt

class GameState:
    """
    Quản lý trạng thái game: Wrapper kết hợp logic của Board + Luật chơi (Lượt, Thắng thua).
    """
    def __init__(self, game_type: str = 'chess'):
        self.board = Board(game_type)
        self.current_turn = 'white' # White/Red đi trước
        
        # --- LOGIC ONLINE ---
        self.my_color: Optional[str] = None # 'white' hoặc 'black'. None = Chơi 2 người 1 máy
        
        self.history: List[Dict[str, Tuple[int, int]]] = [] 
        self.validator = MoveValidator(game_type)
        self.winner: str = None  # 'white', 'black', or 'draw'
        self.is_check = False
        self.is_checkmate = False

        # --- LOGIC PHONG CẤP (PAWN PROMOTION) ---
        self.promotion_pending: bool = False  # True khi có Tốt chờ phong cấp
        self.promotion_pos: Optional[Tuple[int, int]] = None # Vị trí Tốt chờ phong cấp

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
        
        # 0. Nếu đang chờ phong cấp, không cho đi nước khác
        if self.promotion_pending:
            return False

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
            
            # Xác định quân bị ăn (nếu có) - logic kiểm tra ăn Vua ở bên dưới
            
            # Di chuyển quân cờ
            self.board.move_piece(from_pos, to_pos)

            # --- LOGIC PHONG CẤP ---
            # Kiểm tra nếu quân vừa đi là Tốt và đến hàng cuối
            if isinstance(piece, Pawn) and piece.can_promote(to_pos[0]):
                self.promotion_pending = True
                self.promotion_pos = to_pos
                # [QUAN TRỌNG] Chưa đổi lượt, chưa checkmate, chờ người chơi chọn quân
                return True 

            # Nếu không phong cấp, kết thúc lượt bình thường
            self._finalize_turn(to_pos)
            return True
        
        return False

    def apply_promotion(self, promotion_symbol: str) -> bool:
        """
        Xử lý khi người chơi chọn quân để phong cấp (từ UI).
        promotion_symbol: 'Q', 'R', 'B', 'N'
        """
        if not self.promotion_pending or not self.promotion_pos:
            return False

        row, col = self.promotion_pos
        pawn = self.board.get_piece(self.promotion_pos)
        
        if pawn:
            # Tạo quân mới (Hậu, Xe, ...) giữ nguyên màu của Tốt
            new_piece = pawn.promote(promotion_symbol)
            # Cập nhật thẳng vào board (truy cập trực tiếp mảng 2 chiều của object Board)
            self.board.board[row][col] = new_piece
        
        # Reset trạng thái phong cấp
        self.promotion_pending = False
        self.promotion_pos = None

        # Kết thúc lượt (kiểm tra checkmate, đổi lượt)
        self._finalize_turn((row, col))
        return True

    def _finalize_turn(self, last_move_dest: Tuple[int, int]):
        """Logic chung để xử lý sau khi một nước đi hoàn tất (Move hoặc Promote)."""
        
        # --- [LOGIC ĂN VUA LÀ THẮNG LUÔN] ---
        # Kiểm tra xem nước đi vừa rồi có ăn mất Vua/Tướng địch không (dựa vào trạng thái hiện tại của bàn cờ)
        # Tuy nhiên, thông thường logic "bị ăn" đã xử lý lúc move. 
        # Ở đây ta kiểm tra lại nếu cần, hoặc logic cũ kiểm tra captured.
        # Để đơn giản và nhất quán, ta check xem Vua đối phương còn trên bàn cờ không.
        
        opponent_color = self.opponent_color()
        enemy_king_found = False
        for r in range(self.rows):
            for c in range(self.cols):
                p = self.board.get_piece((r, c))
                if p and p.color == opponent_color and p.symbol.upper() in ['K', 'G']:
                    enemy_king_found = True
                    break
            if enemy_king_found:
                break
        
        if not enemy_king_found:
            self.winner = self.current_turn
            return

        # Kiểm tra check/checkmate
        self.is_check = self.validator.is_in_check(self.board, opponent_color)
        
        # Checkmate
        if self.is_check and self.validator.is_checkmate(self.board, opponent_color):
            self.winner = self.current_turn

        # Đổi lượt
        if not self.winner:
            self.current_turn = opponent_color

    def opponent_color(self) -> str:
        return 'black' if self.current_turn == 'white' else 'white'

    def get_state(self) -> Dict:
        """Trả về trạng thái hiện tại để serialize (network)."""
        return {
            'board': self.board.get_board_state(),
            'turn': self.current_turn,
            'is_check': self.is_check,
            'is_checkmate': self.is_checkmate,
            'winner': self.winner,
            'promotion_pending': self.promotion_pending, # Gửi thêm trạng thái này
            'promotion_pos': self.promotion_pos
        }

    def reset(self) -> None:
        """Reset game."""
        current_type = self.board.game_type
        current_color = self.my_color
        self.__init__(current_type)
        self.my_color = current_color