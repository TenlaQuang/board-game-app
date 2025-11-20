from abc import ABC, abstractmethod
from typing import List, Tuple

class Piece(ABC):
    """
    Lớp cơ sở cho tất cả quân cờ.
    - color: 'white' (trắng/đỏ) hoặc 'black' (đen).
    - symbol: Ký tự đại diện (ví dụ: 'K' cho Vua).
    """
    def __init__(self, color: str, symbol: str):
        if color not in ['white', 'black']:
            raise ValueError("Color must be 'white' or 'black'")
        self.color = color
        self.symbol = symbol.upper() if color == 'white' else symbol.lower()
        self.has_moved = False  # Dùng cho nhập thành (Chess) hoặc các quy tắc đặc biệt

    @abstractmethod
    def valid_moves(self, board: List[List['Piece']], pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Trả về list các vị trí (row, col) hợp lệ từ pos."""
        pass

    def __repr__(self) -> str:
        return self.symbol

    def is_enemy(self, other: 'Piece') -> bool:
        """Kiểm tra có phải địch không."""
        return other is not None and other.color != self.color

    def is_ally(self, other: 'Piece') -> bool:
        """Kiểm tra có phải đồng minh không."""
        return other is not None and other.color == self.color

    def is_empty(self, board: List[List['Piece']], row: int, col: int) -> bool:
        """Kiểm tra ô có trống không."""
        rows, cols = len(board), len(board[0]) if board else 0
        return 0 <= row < rows and 0 <= col < cols and board[row][col] is None

    def _slide_moves(self, board: List[List['Piece']], pos: Tuple[int, int], directions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Hàm hỗ trợ cho di chuyển trượt (Rook, Bishop, Queen, Chariot)."""
        moves = []
        row, col = pos
        rows, cols = len(board), len(board[0])
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < rows and 0 <= c < cols:
                if self.is_empty(board, r, c):
                    moves.append((r, c))
                elif self.is_enemy(board[r][c]):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves

# ----------------- Quân cờ Chess -----------------

class Pawn(Piece):  # Tốt (Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        direction = -1 if self.color == 'white' else 1
        start_row = 6 if self.color == 'white' else 1

        # Tiến thẳng
        if self.is_empty(board, row + direction, col):
            moves.append((row + direction, col))
            # Tiến 2 từ vị trí đầu
            if not self.has_moved and row == start_row and self.is_empty(board, row + 2 * direction, col):
                moves.append((row + 2 * direction, col))

        # Ăn chéo
        for dc in [-1, 1]:
            nr, nc = row + direction, col + dc
            if 0 <= nc < len(board[0]) and not self.is_empty(board, nr, nc) and self.is_enemy(board[nr][nc]):
                moves.append((nr, nc))

        # En passant (cần thêm logic từ game_state nếu cần)
        return moves

    def can_promote(self, row: int) -> bool:
        """
        Kiểm tra xem Tốt có ở vị trí phong cấp không.
        - White phong cấp ở hàng 0.
        - Black phong cấp ở hàng 7 (với bàn cờ 8x8).
        """
        if self.color == 'white':
            return row == 0
        else:
            # Giả định bàn cờ chuẩn 8x8, hàng cuối là 7
            return row == 7

    def promote(self, new_symbol: str) -> 'Piece':
        """
        Trả về một quân cờ mới dựa trên lựa chọn phong cấp.
        new_symbol: 'Q', 'R', 'B', 'N'
        """
        # Gọi factory method create_piece (được định nghĩa bên dưới)
        return create_piece(new_symbol, self.color)


class Rook(Piece):  # Xe (Chess)
    def valid_moves(self, board, pos):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return self._slide_moves(board, pos, directions)


class Knight(Piece):  # Mã (Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        moves = []
        for dr, dc in deltas:
            r, c = row + dr, col + dc
            if 0 <= r < len(board) and 0 <= c < len(board[0]) and (self.is_empty(board, r, c) or self.is_enemy(board[r][c])):
                moves.append((r, c))
        return moves


class Bishop(Piece):  # Tượng (Chess)
    def valid_moves(self, board, pos):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self._slide_moves(board, pos, directions)


class Queen(Piece):  # Hậu (Chess)
    def valid_moves(self, board, pos):
        directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        return self._slide_moves(board, pos, directions)


class King(Piece):  # Vua (Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        deltas = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        moves = []
        for dr, dc in deltas:
            r, c = row + dr, col + dc
            if 0 <= r < len(board) and 0 <= c < len(board[0]) and (self.is_empty(board, r, c) or self.is_enemy(board[r][c])):
                moves.append((r, c))

        # Nhập thành (castling) - cần kiểm tra an toàn, nhưng đơn giản hóa
        if not self.has_moved:
            # Kingside (O-O)
            if self.is_empty(board, row, col + 1) and self.is_empty(board, row, col + 2):
                rook = board[row][col + 3]
                if isinstance(rook, Rook) and rook.color == self.color and not rook.has_moved:
                    moves.append((row, col + 2))
            # Queenside (O-O-O)
            if self.is_empty(board, row, col - 1) and self.is_empty(board, row, col - 2) and self.is_empty(board, row, col - 3):
                rook = board[row][col - 4]
                if isinstance(rook, Rook) and rook.color == self.color and not rook.has_moved:
                    moves.append((row, col - 2))

        return moves

# ----------------- Quân cờ Chinese Chess -----------------

class General(Piece):  # Tướng (Chinese Chess)
    def __init__(self, color: str, symbol: str = 'G'):
        super().__init__(color, symbol)

    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        # Cung điện: black (hàng 0-2, cột 3-5), white/red (hàng 7-9, cột 3-5)
        palace_min_row = 0 if self.color == 'black' else 7
        palace_max_row = 2 if self.color == 'black' else 9
        palace_min_col, palace_max_col = 3, 5

        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in deltas:
            r, c = row + dr, col + dc
            if (palace_min_row <= r <= palace_max_row and palace_min_col <= c <= palace_max_col and
                (self.is_empty(board, r, c) or self.is_enemy(board[r][c]))):
                # Kiểm tra không đối mặt Tướng địch (cần tìm Tướng địch)
                if not self._is_facing_general(board, (r, c)):
                    moves.append((r, c))
        return moves

    def _is_facing_general(self, board, new_pos):
        # Tìm vị trí Tướng địch và kiểm tra cột thẳng, không có chắn
        enemy_color = 'white' if self.color == 'black' else 'black'
        enemy_general_pos = None
        for r in range(len(board)):
            for c in range(len(board[0])):
                piece = board[r][c]
                if isinstance(piece, General) and piece.color == enemy_color:
                    enemy_general_pos = (r, c)
                    break
            if enemy_general_pos:
                break

        if not enemy_general_pos or new_pos[1] != enemy_general_pos[1]:
            return False

        min_r, max_r = min(new_pos[0], enemy_general_pos[0]), max(new_pos[0], enemy_general_pos[0])
        for r in range(min_r + 1, max_r):
            if board[r][new_pos[1]] is not None:
                return False
        return True


class Advisor(Piece):  # Sĩ (Chinese Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        palace_min_row = 0 if self.color == 'black' else 7
        palace_max_row = 2 if self.color == 'black' else 9
        palace_min_col, palace_max_col = 3, 5

        deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in deltas:
            r, c = row + dr, col + dc
            if (palace_min_row <= r <= palace_max_row and palace_min_col <= c <= palace_max_col and
                (self.is_empty(board, r, c) or self.is_enemy(board[r][c]))):
                moves.append((r, c))
        return moves


class Elephant(Piece):  # Tượng (Chinese Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        deltas = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        river_row = 4 if self.color == 'black' else 5  # Không qua sông

        for dr, dc in deltas:
            r, c = row + dr, col + dc
            block_r, block_c = row + dr // 2, col + dc // 2  # Ô chắn (điền tâm)
            if (0 <= r < 10 and 0 <= c < 9 and
                (self.color == 'black' and r < 5 or self.color == 'white' and r > 4) and  # Không qua sông
                self.is_empty(board, block_r, block_c) and
                (self.is_empty(board, r, c) or self.is_enemy(board[r][c]))):
                moves.append((r, c))
        return moves


class Horse(Piece):  # Mã (Chinese Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        # Chân mã: hướng chắn
        leg_deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        jump_deltas = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]

        for i in range(4):  # 4 hướng chính
            leg_dr, leg_dc = leg_deltas[i]
            for j in [0, 1]:  # 2 nhánh mỗi hướng
                jump_dr, jump_dc = jump_deltas[i * 2 + j]
                leg_r, leg_c = row + leg_dr, col + leg_dc
                r, c = row + jump_dr, col + jump_dc
                if (0 <= r < 10 and 0 <= c < 9 and
                    self.is_empty(board, leg_r, leg_c) and
                    (self.is_empty(board, r, c) or self.is_enemy(board[r][c]))):
                    moves.append((r, c))
        return moves


class Chariot(Piece):  # Xe (Chinese Chess)
    def valid_moves(self, board, pos):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return self._slide_moves(board, pos, directions)


class Cannon(Piece):  # Pháo (Chinese Chess)
    def valid_moves(self, board, pos):
        moves = []
        row, col = pos
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            jumped = False
            while 0 <= r < 10 and 0 <= c < 9:
                if self.is_empty(board, r, c):
                    if not jumped:
                        moves.append((r, c))  # Di chuyển không ăn
                else:
                    if jumped and self.is_enemy(board[r][c]):
                        moves.append((r, c))  # Ăn sau khi nhảy
                        break
                    elif not jumped:
                        jumped = True  # Nhảy qua đồng minh hoặc địch
                    else:
                        break
                r += dr
                c += dc
        return moves


class Soldier(Piece):  # Tốt (Chinese Chess)
    def valid_moves(self, board, pos):
        row, col = pos
        moves = []
        direction = 1 if self.color == 'black' else -1  # Black đi xuống (tăng row), white đi lên (giảm row)
        # Giả định board row 0 là black, row 9 là white

        # Tiến thẳng
        nr = row + direction
        if 0 <= nr < 10 and (self.is_empty(board, nr, col) or self.is_enemy(board[nr][col])):
            moves.append((nr, col))

        # Sang ngang sau khi qua sông
        crossed_river = (self.color == 'black' and row >= 5) or (self.color == 'white' and row <= 4)
        if crossed_river:
            for dc in [-1, 1]:
                nc = col + dc
                if 0 <= nc < 9 and (self.is_empty(board, row, nc) or self.is_enemy(board[row][nc])):
                    moves.append((row, nc))

        return moves

# ----------------- Factory để tạo quân cờ -----------------

def create_piece(symbol: str, color: str) -> Piece:
    """
    Factory để tạo quân cờ dựa trên symbol.
    - Chess: P (Pawn), R (Rook), N (Knight), B (Bishop), Q (Queen), K (King)
    - Chinese Chess: G (General), A (Advisor), E (Elephant), H (Horse), C (Chariot), N (Cannon), S (Soldier)
    Symbol không phân biệt hoa/thường, nhưng color quyết định.
    """
    symbol = symbol.upper()
    pieces_map = {
        # Chess
        'P': Pawn,
        'R': Rook,
        'N': Knight,
        'B': Bishop,
        'Q': Queen,
        'K': King,
        # Chinese Chess
        'G': General,
        'A': Advisor,
        'E': Elephant,
        'H': Horse,
        'C': Chariot,
        'O': Cannon,  # 'O' cho Cannon để tránh trùng N
        'S': Soldier
    }
    cls = pieces_map.get(symbol)
    if cls:
        return cls(color, symbol)
    raise ValueError(f"Unknown piece symbol: {symbol}")