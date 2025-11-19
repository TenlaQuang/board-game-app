from typing import List, Tuple, Optional
from core.piece import (
    Piece, Pawn, Rook, Knight, Bishop, Queen, King,
    General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier
)

# --- [FIX QUAN TRỌNG] IMPORT ĐÚNG FILE CỦA BẠN ---
# Dùng 'core.move_validator' thay vì 'core.validator'
try:
    from core.move_validator import MoveValidator
except ImportError:
    print("Lỗi Import: Không tìm thấy core/move_validator.py")
    MoveValidator = None 
# -------------------------------------------------

class Board:
    def __init__(self, game_type: str = 'chess'):
        self.game_type = game_type
        
        # --- LOGIC ONLINE & LƯỢT CHƠI ---
        self.current_turn = 'white'   
        self.my_color = None  
        
        # --- TRẠNG THÁI WIN/LOSS ---
        self.winner = None    
        self.game_over = False
        # ----------------------------------

        if self.game_type == 'chess':
            self.rows, self.cols = 8, 8
        else:
            self.rows, self.cols = 10, 9 # Cờ tướng
            
        self.board: List[List[Optional[Piece]]] = []
        self.setup_board()
        
        # --- KHỞI TẠO VALIDATOR ---
        if MoveValidator:
            # Truyền self.game_type (chuỗi) thay vì self (object)
            self.validator = MoveValidator(self.game_type)
        else:
            print("CẢNH BÁO: Không tìm thấy MoveValidator. Tính năng gợi ý nước đi sẽ lỗi.")
            self.validator = None
        # --------------------------------

    # --- MAGIC METHODS ---
    def __len__(self):
        return self.rows

    def __getitem__(self, index):
        return self.board[index]

    def setup_board(self):
        """Khởi tạo bàn cờ."""
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        if self.game_type == 'chess':
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
            # Đen
            self.board[0] = [
                Chariot('black', 'C'), Horse('black', 'H'), Elephant('black', 'E'), Advisor('black', 'A'),
                General('black', 'G'), Advisor('black', 'A'), Elephant('black', 'E'), Horse('black', 'H'), Chariot('black', 'C')
            ]
            self.board[2] = [None, Cannon('black', 'O'), None, None, None, None, None, Cannon('black', 'O'), None]
            self.board[3] = [Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S'), None, Soldier('black', 'S')]
            
            # Đỏ (white)
            self.board[9] = [
                Chariot('white', 'C'), Horse('white', 'H'), Elephant('white', 'E'), Advisor('white', 'A'),
                General('white', 'G'), Advisor('white', 'A'), Elephant('white', 'E'), Horse('white', 'H'), Chariot('white', 'C')
            ]
            self.board[7] = [None, Cannon('white', 'O'), None, None, None, None, None, Cannon('white', 'O'), None]
            self.board[6] = [Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S'), None, Soldier('white', 'S')]

    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        row, col = pos
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.board[row][col]
        return None

    def find_king_pos(self, color: str) -> Optional[Tuple[int, int]]:
        target_symbols = ['K', 'G'] 
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if piece and piece.color == color:
                    if piece.symbol.upper() in target_symbols:
                        return (r, c)
        return None

    def get_board_state(self):
        state = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if piece:
                    state[r][c] = piece.symbol
        return state

    # --- LOGIC ONLINE ---
    def set_player_color(self, color: str):
        self.my_color = color

    def is_my_turn(self) -> bool:
        if self.my_color is None: return True
        return self.current_turn == self.my_color 

    def switch_turn(self):
        self.current_turn = 'black' if self.current_turn == 'white' else 'white' 

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        if self.game_over: return False
        
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.get_piece(from_pos)
        target_piece = self.get_piece(to_pos)
        
        if piece:
            # Check win
            if target_piece and target_piece.symbol.upper() in ['K', 'G']:
                self.winner = self.current_turn 
                self.game_over = True
                print(f"GAME OVER! {self.winner.upper()} thắng!")

            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            
            if hasattr(piece, 'update_position'): piece.update_position((to_row, to_col))
            elif hasattr(piece, 'has_moved'): piece.has_moved = True
            
            if not self.game_over:
                self.switch_turn()
                print(f"Đã đi: {from_pos}->{to_pos}. Lượt: {self.current_turn}")
            else:
                print("Game đã kết thúc.")
            return True
        else:
            print(f"Lỗi: Không có quân tại {from_pos}")
            return False