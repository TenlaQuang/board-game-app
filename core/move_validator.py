from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .board import Board

class MoveValidator:
    def __init__(self, game_type: str = 'chess'):
        self.game_type = game_type

    def is_valid_move(self, board: 'Board', start_pos: Tuple[int, int], end_pos: Tuple[int, int], player_color: str) -> bool:
        """
        Kiểm tra xem một nước đi từ start -> end có hợp lệ hay không.
        Bao gồm cả việc kiểm tra: Quân cờ có được đi thế không? Có bị chiếu tướng sau khi đi không?
        """
        # 1. Lấy quân cờ
        piece = board.get_piece(start_pos)
        if not piece or piece.color != player_color:
            return False

        # 2. Kiểm tra xem nước đi có nằm trong danh sách đi được của quân cờ không (Geometric check)
        # Hàm valid_moves của Piece trả về các nước đi 'có thể' về mặt hình học
        if hasattr(piece, 'valid_moves'):
            possible_moves = piece.valid_moves(board, start_pos)
        else:
            return False
            
        if end_pos not in possible_moves:
            return False

        # 3. [QUAN TRỌNG] SAFETY CHECK - Kiểm tra xem đi xong có bị chiếu không?
        if not self._is_move_safe(board, start_pos, end_pos, player_color):
            return False

        return True

    def get_valid_moves_for_piece(self, board: 'Board', pos: Tuple[int, int], player_color: str) -> List[Tuple[int, int]]:
        """
        Hàm này được BoardUI gọi để lấy danh sách các chấm xanh (gợi ý nước đi).
        Nó sẽ lọc bỏ các nước đi tự sát (đi xong vẫn bị chiếu).
        """
        piece = board.get_piece(pos)
        if not piece or piece.color != player_color:
            return []

        # 1. Lấy các nước đi cơ bản
        if hasattr(piece, 'valid_moves'):
            raw_moves = piece.valid_moves(board, pos)
        else:
            return []

        valid_moves = []
        # 2. Lọc các nước đi không an toàn
        for move in raw_moves:
            if self._is_move_safe(board, pos, move, player_color):
                valid_moves.append(move)

        return valid_moves

    def _is_move_safe(self, board: 'Board', start: Tuple[int, int], end: Tuple[int, int], color: str) -> bool:
        """
        Giả lập nước đi để kiểm tra xem Vua có bị chiếu không.
        """
        # --- BƯỚC 1: GIẢ LẬP NƯỚC ĐI (SIMULATION) ---
        target_piece = board.board[end[0]][end[1]] # Lưu quân bị ăn (nếu có)
        moving_piece = board.board[start[0]][start[1]]
        
        # Di chuyển tạm thời
        board.board[end[0]][end[1]] = moving_piece
        board.board[start[0]][start[1]] = None
        
        # Cập nhật vị trí tạm thời cho quân cờ (nếu quân cờ lưu vị trí nội tại)
        original_pos = None
        if hasattr(moving_piece, 'pos'):
            original_pos = moving_piece.pos
            moving_piece.pos = end # Cập nhật giả
            
        # --- BƯỚC 2: KIỂM TRA AN TOÀN (CHECK) ---
        is_safe = not self.is_in_check(board, color)
        
        # --- BƯỚC 3: HOÀN TÁC (UNDO) ---
        # Trả lại mọi thứ như cũ
        board.board[start[0]][start[1]] = moving_piece
        board.board[end[0]][end[1]] = target_piece
        
        if original_pos and hasattr(moving_piece, 'pos'):
            moving_piece.pos = original_pos

        return is_safe

    def is_in_check(self, board: 'Board', color: str) -> bool:
        """Kiểm tra xem phe 'color' có đang bị chiếu không."""
        king_pos = board.find_king_pos(color)
        if not king_pos:
            return False # Không thấy Vua thì coi như không bị chiếu (hoặc game lỗi)

        opponent_color = 'black' if color == 'white' else 'white'
        
        # Duyệt tất cả quân đối phương, xem có quân nào ăn được Vua không
        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if piece and piece.color == opponent_color:
                    # Lấy các nước đi của quân địch
                    if hasattr(piece, 'valid_moves'):
                        moves = piece.valid_moves(board, (r, c))
                        if king_pos in moves:
                            return True
        return False

    def is_checkmate(self, board: 'Board', color: str) -> bool:
        """
        Kiểm tra chiếu bí:
        1. Đang bị chiếu.
        2. Không còn nước đi nào hợp lệ để thoát chiếu.
        """
        if not self.is_in_check(board, color):
            return False

        # Duyệt tất cả quân mình, thử đi tất cả các nước
        # Nếu tìm thấy bất kỳ nước nào "Safe", nghĩa là chưa thua.
        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if piece and piece.color == color:
                    valid_moves = self.get_valid_moves_for_piece(board, (r, c), color)
                    if valid_moves:
                        return False # Còn nước cứu
        
        return True