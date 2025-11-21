from typing import List, Tuple, TYPE_CHECKING
# Import đầy đủ các quân để check isinstance chuẩn xác
from .piece import King, Rook, Pawn, Knight, Bishop, Queen, Soldier, Horse, Cannon, Chariot, Elephant, Advisor, General

if TYPE_CHECKING:
    from .board import Board

class MoveValidator:
    def __init__(self, game_type: str = 'chess'):
        self.game_type = game_type

    def is_valid_move(self, board: 'Board', start_pos: Tuple[int, int], end_pos: Tuple[int, int], player_color: str) -> bool:
        piece = board.get_piece(start_pos)
        if not piece or piece.color != player_color:
            return False
        
        # Lấy danh sách nước đi chuẩn (đã lọc an toàn)
        valid_moves = self.get_valid_moves_for_piece(board, start_pos, player_color)
        return end_pos in valid_moves

    def get_valid_moves_for_piece(self, board: 'Board', pos: Tuple[int, int], player_color: str) -> List[Tuple[int, int]]:
        piece = board.get_piece(pos)
        if not piece or piece.color != player_color:
            return []

        # 1. Lấy nước đi cơ bản
        raw_moves = []
        if hasattr(piece, 'valid_moves'):
            raw_moves = piece.valid_moves(board, pos)

        # 2. LOGIC NHẬP THÀNH (CASTLING)
        if self.game_type == 'chess' and isinstance(piece, King):
            has_moved = getattr(piece, 'has_moved', False)
            if not has_moved and not self.is_in_check(board, player_color):
                row, col = pos
                opponent_color = 'black' if player_color == 'white' else 'white'
                
                # King-side (Cánh Vua)
                if self._can_castle_kingside(board, row, col, player_color):
                    middle_pos = (row, col + 1) # Ô f1/f8
                    # Check kỹ: Ô đi qua có bị tấn công không?
                    if not self.is_square_attacked(board, middle_pos, opponent_color):
                        raw_moves.append((row, col + 2)) 
                
                # Queen-side (Cánh Hậu)
                if self._can_castle_queenside(board, row, col, player_color):
                    middle_pos = (row, col - 1) # Ô d1/d8
                    if not self.is_square_attacked(board, middle_pos, opponent_color):
                        raw_moves.append((row, col - 2))

        # 3. LOGIC BẮT TỐT QUA ĐƯỜNG (EN PASSANT)
        if self.game_type == 'chess' and isinstance(piece, Pawn):
            ep_move = self._get_en_passant_move(board, pos, piece)
            if ep_move:
                raw_moves.append(ep_move)

        # 4. Lọc nước đi an toàn (Move Safety Check)
        valid_moves = []
        for move in raw_moves:
            if self._is_move_safe(board, pos, move, player_color):
                valid_moves.append(move)

        return valid_moves

    # --- [QUAN TRỌNG] HÀM CHECK BỊ TẤN CÔNG (HARDENED) ---
    def is_square_attacked(self, board: 'Board', pos: Tuple[int, int], attacker_color: str) -> bool:
        """Kiểm tra ô 'pos' có bị 'attacker_color' nhắm tới không."""
        target_r, target_c = pos
        
        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if not piece or piece.color != attacker_color:
                    continue
                
                # A. XỬ LÝ RIÊNG CHO TỐT (PAWN) - Fix lỗi Tốt không tính đe dọa ô trống
                if isinstance(piece, (Pawn, Soldier)):
                    if board.game_type == 'chess':
                        # Tốt đen đánh xuống (+1), Tốt trắng đánh lên (-1)
                        direction = 1 if piece.color == 'black' else -1
                        attack_r = r + direction
                        # Nếu cùng hàng tấn công và chênh lệch 1 cột -> BỊ CHIẾU
                        if attack_r == target_r and abs(c - target_c) == 1:
                            return True
                    # (Logic Cờ tướng cho Tốt có thể thêm ở đây nếu cần)
                    continue 

                # B. XỬ LÝ RIÊNG CHO MÃ (KNIGHT) - Tính toán hình học, không phụ thuộc valid_moves
                if isinstance(piece, (Knight, Horse)):
                    if board.game_type == 'chess':
                        dr = abs(r - target_r)
                        dc = abs(c - target_c)
                        if (dr == 1 and dc == 2) or (dr == 2 and dc == 1):
                            return True
                    elif board.game_type == 'chinese_chess':
                        # Cờ tướng phức tạp hơn (có cản), nên dùng valid_moves
                        pass
                    
                    if board.game_type == 'chess': continue

                # C. XỬ LÝ RIÊNG CHO VUA (KING)
                if isinstance(piece, (King, General)):
                    if abs(r - target_r) <= 1 and abs(c - target_c) <= 1:
                        return True
                    continue

                # D. CÁC QUÂN CÒN LẠI (Xe, Tượng, Hậu) - Dùng valid_moves là an toàn
                if hasattr(piece, 'valid_moves'):
                    moves = piece.valid_moves(board, (r, c))
                    if pos in moves:
                        return True
        
        return False

    # --- CÁC HÀM PHỤ TRỢ KHÁC (Giữ nguyên logic chuẩn) ---
    def _can_castle_kingside(self, board: 'Board', r, c, color):
        if board.board[r][5] is not None or board.board[r][6] is not None: return False
        rook = board.board[r][7]
        if not isinstance(rook, Rook) or rook.color != color or getattr(rook, 'has_moved', False): return False
        return True

    def _can_castle_queenside(self, board: 'Board', r, c, color):
        if board.board[r][1] is not None or board.board[r][2] is not None or board.board[r][3] is not None: return False
        rook = board.board[r][0]
        if not isinstance(rook, Rook) or rook.color != color or getattr(rook, 'has_moved', False): return False
        return True

    def _get_en_passant_move(self, board: 'Board', current_pos: Tuple[int, int], pawn: Pawn):
        last_move = getattr(board, 'last_move', None)
        if not last_move: return None
        r, c = current_pos
        lm_piece = last_move['piece']
        lm_start = last_move['start']
        lm_end = last_move['end']
        if isinstance(lm_piece, Pawn) and abs(lm_start[0] - lm_end[0]) == 2:
            if lm_end[0] == r and abs(lm_end[1] - c) == 1:
                direction = -1 if pawn.color == 'white' else 1 
                return (r + direction, lm_end[1])
        return None

    def _is_move_safe(self, board: 'Board', start: Tuple[int, int], end: Tuple[int, int], color: str) -> bool:
        target_piece = board.board[end[0]][end[1]]
        moving_piece = board.board[start[0]][start[1]]
        
        en_passant_victim_pos = None
        en_passant_victim = None
        if self.game_type == 'chess' and isinstance(moving_piece, Pawn) and start[1] != end[1] and target_piece is None:
            en_passant_victim_pos = (start[0], end[1]) 
            en_passant_victim = board.board[en_passant_victim_pos[0]][en_passant_victim_pos[1]]
            board.board[en_passant_victim_pos[0]][en_passant_victim_pos[1]] = None 

        board.board[end[0]][end[1]] = moving_piece
        board.board[start[0]][start[1]] = None
        
        original_pos = None
        if hasattr(moving_piece, 'pos'):
            original_pos = moving_piece.pos
            moving_piece.pos = end 
            
        is_safe = not self.is_in_check(board, color)
        
        board.board[start[0]][start[1]] = moving_piece
        board.board[end[0]][end[1]] = target_piece
        if original_pos and hasattr(moving_piece, 'pos'): moving_piece.pos = original_pos
        if en_passant_victim_pos: board.board[en_passant_victim_pos[0]][en_passant_victim_pos[1]] = en_passant_victim

        return is_safe

    def is_in_check(self, board: 'Board', color: str) -> bool:
        king_pos = board.find_king_pos(color)
        if not king_pos: return False 
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(board, king_pos, opponent_color)