from typing import List, Tuple, Optional
# Import các quân cờ (đảm bảo file piece.py của bạn vẫn như cũ)
from core.piece import (
    Piece, Pawn, Rook, Knight, Bishop, Queen, King,
    General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier
)

class Board:
    def __init__(self, game_type: str = 'chess'):
        self.game_type = game_type
        self.board: List[List[Optional[Piece]]] = []
        
        # --- [NEW] LOGIC ONLINE & LƯỢT CHƠI ---
        self.turn = 'white'   # Lượt hiện tại ('white' hoặc 'black')
        self.my_color = None  # Màu của người chơi trên máy này
        # --------------------------------------

        if self.game_type == 'chess':
            self.rows, self.cols = 8, 8
        else:
            self.rows, self.cols = 10, 9 # Cờ tướng
            
        self.setup_board()

    def setup_board(self):
        """Khởi tạo bàn cờ với vị trí ban đầu của các quân cờ."""
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        if self.game_type == 'chess':
            # === ĐẶT QUÂN CỜ VUA ===
            self.board[0] = [
                Rook('black', 'R'), Knight('black', 'N'), Bishop('black', 'B'), Queen('black', 'Q'),
                King('black', 'K'), Bishop('black', 'B'), Knight('black', 'N'), Rook('black', 'R')
            ]
            self.board[1] = [Pawn('black', 'P') for _ in range(self.cols)]
            
            self.board[6] = [Pawn('white', 'P') for _ in range(self.cols)]
            self.board[7] = [
                Rook('white', 'R'), Knight('white', 'N'), Bishop('white', 'B'), Queen('white', 'Q'),
                King('white', 'K'), Bishop('white', 'B'), Knight('white', 'N'), Rook('white', 'R')
            ]
        
        elif self.game_type == 'chinese_chess':
            # === ĐẶT QUÂN CỜ TƯỚNG ===
            # Đen (hàng 0-4)
            self.board[0] = [
                Chariot('black', 'C'), Horse('black', 'H'), Elephant('black', 'E'), Advisor('black', 'A'),
                General('black', 'G'), Advisor('black', 'A'), Elephant('black', 'E'), Horse('black', 'H'), Chariot('black', 'C')
            ]
            self.board[2] = [None, Cannon('black', 'O'), None, None, None, None, None, Cannon('black', 'O'), None]
            self.board[3] = [Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S')]
            
            # Đỏ ('white') (hàng 5-9)
            self.board[9] = [
                Chariot('white', 'C'), Horse('white', 'H'), Elephant('white', 'E'), Advisor('white', 'A'),
                General('white', 'G'), Advisor('white', 'A'), Elephant('white', 'E'), Horse('white', 'H'), Chariot('white', 'C')
            ]
            self.board[7] = [None, Cannon('white', 'O'), None, None, None, None, None, Cannon('white', 'O'), None]
            self.board[6] = [Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S')]

    # --- CÁC HÀM HELPER ---
    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """Lấy quân cờ tại vị trí (row, col)."""
        row, col = pos
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.board[row][col]
        return None

    def get_board_state(self):
        """Trả về lưới ký tự đại diện cho bàn cờ (để vẽ)."""
        state = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if piece:
                    state[r][c] = piece.symbol
        return state

    # --- [NEW] LOGIC ONLINE & LƯỢT CHƠI ---
    def set_player_color(self, color: str):
        """Thiết lập màu cho người chơi này."""
        self.my_color = color

    def is_my_turn(self) -> bool:
        """Kiểm tra có phải lượt của mình không."""
        # Nếu chưa set màu (chơi offline), luôn cho phép đi
        if self.my_color is None:
            return True
        return self.turn == self.my_color

    def switch_turn(self):
        """Đổi lượt chơi."""
        self.turn = 'black' if self.turn == 'white' else 'white'

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Di chuyển quân cờ và đổi lượt."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.get_piece(from_pos)
        
        if piece:
            # Di chuyển quân
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            piece.has_moved = True
            
            # Đổi lượt
            self.switch_turn()
            print(f"Đã đi từ {from_pos} đến {to_pos}. Lượt tiếp theo: {self.turn}")
        else:
            print(f"Lỗi: Không có quân cờ tại {from_pos}")