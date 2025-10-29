# core/board.py
from typing import List, Tuple, Optional
from .piece import create_piece, Piece

class Board:
    """
    Lớp quản lý bàn cờ cho cả Chess và Chinese Chess.
    - board: Ma trận 2D chứa Piece hoặc None.
    - size: (rows, cols) khác nhau tùy game_type.
    """
    def __init__(self, game_type: str = 'chess'):
        if game_type not in ['chess', 'chinese_chess']:
            raise ValueError("Game type must be 'chess' or 'chinese_chess'")
        self.game_type = game_type
        self.rows = 8 if game_type == 'chess' else 10
        self.cols = 8 if game_type == 'chess' else 9
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self._setup_pieces()

    def _setup_pieces(self) -> None:
        """Khởi tạo vị trí quân cờ ban đầu."""
        if self.game_type == 'chess':
            # Hàng black (row 0: back rank)
            black_back = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
            for c, symbol in enumerate(black_back):
                self.board[0][c] = create_piece(symbol, 'black')
                self.board[7][c] = create_piece(symbol, 'white')  # White back rank
            # Pawns
            for c in range(self.cols):
                self.board[1][c] = create_piece('P', 'black')
                self.board[6][c] = create_piece('P', 'white')

        elif self.game_type == 'chinese_chess':
            # Black (top, row 0)
            black_back = ['C', 'H', 'E', 'A', 'G', 'A', 'E', 'H', 'C']
            for c, symbol in enumerate(black_back):
                self.board[0][c] = create_piece(symbol, 'black')
            # Cannons (Pháo)
            self.board[2][1] = create_piece('O', 'black')
            self.board[2][7] = create_piece('O', 'black')
            # Soldiers (Tốt)
            for c in [0, 2, 4, 6, 8]:
                self.board[3][c] = create_piece('S', 'black')

            # White (bottom, row 9, đối xứng)
            white_back = ['C', 'H', 'E', 'A', 'G', 'A', 'E', 'H', 'C']
            for c, symbol in enumerate(white_back):
                self.board[9][c] = create_piece(symbol, 'white')
            # Cannons
            self.board[7][1] = create_piece('O', 'white')
            self.board[7][7] = create_piece('O', 'white')
            # Soldiers
            for c in [0, 2, 4, 6, 8]:
                self.board[6][c] = create_piece('S', 'white')

    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """Lấy Piece tại vị trí (row, col)."""
        row, col = pos
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.board[row][col]
        return None

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Di chuyển Piece từ from_pos đến to_pos, nếu hợp lệ (không validate ở đây)."""
        piece = self.get_piece(from_pos)
        if piece:
            self.board[to_pos[0]][to_pos[1]] = piece
            self.board[from_pos[0]][from_pos[1]] = None
            piece.has_moved = True
            return True
        return False

    def get_board_state(self) -> List[List[str]]:
        """Trả về trạng thái bàn cờ dưới dạng list of lists với symbol hoặc ''."""
        return [[str(piece) if piece else '' for piece in row] for row in self.board]

    def find_king_pos(self, color: str) -> Optional[Tuple[int, int]]:
        """Tìm vị trí Vua/Tướng của color."""
        target_class = King if self.game_type == 'chess' else General
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if isinstance(piece, target_class) and piece.color == color:
                    return (r, c)
        return None