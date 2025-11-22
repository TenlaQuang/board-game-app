from typing import List, Tuple, Optional
import copy
from core.piece import (
    Piece, Pawn, Rook, Knight, Bishop, Queen, King,
    General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier,
    create_piece 
)

# --- [FIX QUAN TRỌNG] IMPORT ĐÚNG FILE CỦA BẠN ---
try:
    from core.move_validator import MoveValidator
except ImportError:
    print("Lỗi Import: Không tìm thấy core/move_validator.py (Sẽ cập nhật sau)")
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

        # --- LOGIC PHONG CẤP ---
        self.promotion_pending = False
        self.promotion_pos = None

        # --- [MỚI] LƯU TRỮ LỊCH SỬ ĐỂ BẮT TỐT QUA ĐƯỜNG ---
        # Lưu nước đi cuối cùng: {'start': (r,c), 'end': (r,c), 'piece': obj, 'color': str}
        self.last_move = None 
        # --------------------------------------------------

        if self.game_type == 'chess':
            self.rows, self.cols = 8, 8
        else:
            self.rows, self.cols = 10, 9 # Cờ tướng
            
        self.board: List[List[Optional[Piece]]] = []
        self.setup_board()
        
        # --- KHỞI TẠO VALIDATOR ---
        if MoveValidator:
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

    # --- LOGIC DI CHUYỂN & PHONG CẤP ---
    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], promotion: str = None) -> bool:
        """
        Thực hiện nước đi. 
        - promotion: Ký tự quân muốn phong cấp (ví dụ 'Q').
        """
        # 0. Chặn nếu đang chờ phong cấp
        if self.promotion_pending and self.promotion_pos != to_pos:
            return False

        if self.game_over: return False
        
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.get_piece(from_pos)
        target_piece = self.get_piece(to_pos)
        
        if piece:
            # --- [MỚI] CHECK NHẬP THÀNH (CASTLING) ---
            # Phát hiện Vua đi 2 bước
            is_castling = False
            if self.game_type == 'chess' and isinstance(piece, King) and abs(from_col - to_col) == 2:
                is_castling = True

            # --- [MỚI] CHECK BẮT TỐT QUA ĐƯỜNG (EN PASSANT) ---
            # Phát hiện Tốt đi chéo sang ô trống
            is_en_passant = False
            en_passant_capture_pos = None
            if self.game_type == 'chess' and isinstance(piece, Pawn):
                if from_col != to_col and target_piece is None:
                    is_en_passant = True
                    # Quân bị bắt nằm ở hàng cũ (from_row), cột mới (to_col)
                    en_passant_capture_pos = (from_row, to_col)

            # 1. Xử lý ăn quân (Bình thường)
            if target_piece and target_piece.symbol.upper() in ['K', 'G']:
                self.winner = self.current_turn 
                self.game_over = True
                print(f"GAME OVER! {self.winner.upper()} thắng!")

            # 2. Di chuyển quân chính (Vua/Tốt/...)
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            
            # 3. Cập nhật trạng thái quân (has_moved cho King/Rook)
            if hasattr(piece, 'update_position'): piece.update_position((to_row, to_col))
            elif hasattr(piece, 'has_moved'): piece.has_moved = True
            
            # --- [MỚI] THỰC HIỆN SIDE-EFFECTS ---
            
            # A. Nếu là Nhập thành -> Di chuyển Xe
            if is_castling:
                if to_col > from_col: # Nhập thành cánh Vua (phải)
                    rook_from = (from_row, 7); rook_to = (from_row, 5)
                else: # Nhập thành cánh Hậu (trái)
                    rook_from = (from_row, 0); rook_to = (from_row, 3)
                
                rook = self.board[rook_from[0]][rook_from[1]]
                if rook:
                    self.board[rook_to[0]][rook_to[1]] = rook
                    self.board[rook_from[0]][rook_from[1]] = None
                    if hasattr(rook, 'has_moved'): rook.has_moved = True
                    print("Backend: Đã di chuyển Xe nhập thành.")

            # B. Nếu là En Passant -> Xóa tốt đối phương
            if is_en_passant and en_passant_capture_pos:
                self.board[en_passant_capture_pos[0]][en_passant_capture_pos[1]] = None
                print("Backend: Đã bắt tốt qua đường.")

            # -------------------------------------

            # --- XỬ LÝ PHONG CẤP (PAWN PROMOTION) ---
            if self.game_type == 'chess' and isinstance(piece, Pawn):
                if piece.can_promote(to_row):
                    if promotion:
                         self.apply_promotion(promotion, pos_override=(to_row, to_col))
                         self._update_last_move(from_pos, to_pos, piece) # Lưu move
                         return True
                    
                    self.promotion_pending = True
                    self.promotion_pos = (to_row, to_col)
                    print("Chờ phong cấp...")
                    return True

            if not self.game_over:
                self._update_last_move(from_pos, to_pos, piece)
                self.switch_turn()
                print(f"Đã đi: {from_pos}->{to_pos}. Lượt: {self.current_turn}")
                # --- [QUAN TRỌNG] KIỂM TRA CHIẾU BÍ / HẾT NƯỚC ---
                self.check_game_status()
                # -------------------------------------------------
            else:
                print("Game đã kết thúc.")
            return True
        else:
            print(f"Lỗi: Không có quân tại {from_pos}")
            return False
    

    def _update_last_move(self, start, end, piece):
        """Lưu lại nước đi vừa thực hiện để check En Passant."""
        self.last_move = {
            'start': start,
            'end': end,
            'piece': piece,
            'color': piece.color,
            'symbol': piece.symbol
        }

    def apply_promotion(self, promotion_symbol: str, pos_override: Tuple[int, int] = None) -> bool:
        """Biến Tốt thành quân khác (Hậu, Xe...)."""
        pos = pos_override if pos_override else self.promotion_pos
        if not pos: return False

        row, col = pos
        pawn = self.board[row][col]
        
        if pawn:
            try:
                new_piece = create_piece(promotion_symbol, pawn.color)
                self.board[row][col] = new_piece
                # piece mới cũng coi như đã di chuyển
                if hasattr(new_piece, 'has_moved'): new_piece.has_moved = True 
                print(f"Đã phong cấp thành {new_piece.symbol} tại {pos}")
            except Exception as e:
                print(f"Lỗi phong cấp: {e}")
        
        self.promotion_pending = False
        self.promotion_pos = None
        
        if not self.game_over:
            # Lưu last move cho promotion (quan trọng nếu muốn undo)
            self._update_last_move(pos, pos, self.board[row][col]) 
            self.switch_turn()
            print(f"Hoàn tất phong cấp. Lượt: {self.current_turn}")
        
        return True
    # --- THÊM VÀO CUỐI CLASS BOARD (core/board.py) ---

    def uci_to_coords(self, uci_move: str):
        """
        Chuyển nước đi UCI (ví dụ 'e2e4') thành tọa độ ((6,4), (4,4))
        """
        if not uci_move: return None, None
        
        files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        
        # Tọa độ bắt đầu
        c1 = files[uci_move[0]]
        r1 = 8 - int(uci_move[1])
        
        # Tọa độ kết thúc
        c2 = files[uci_move[2]]
        r2 = 8 - int(uci_move[3])
        
        # Kiểm tra phong cấp (ví dụ a7a8q)
        promotion = uci_move[4].upper() if len(uci_move) > 4 else None
        
        return (r1, c1), (r2, c2), promotion

    def to_fen(self):
        """
        Chuyển trạng thái bàn cờ hiện tại thành chuỗi FEN chuẩn để gửi cho Stockfish.
        Ví dụ: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        """
        if self.game_type != 'chess':
            return "" # Stockfish không chơi cờ tướng

        fen = ""
        # 1. Duyệt bàn cờ để xây dựng vị trí quân
        for r in range(8):
            empty_count = 0
            for c in range(8):
                p = self.board[r][c]
                if p is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    # Quân trắng viết hoa, đen viết thường (Code Piece của bạn đã xử lý việc này chưa? 
                    # Nếu piece.symbol trả về 'K' cho đen thì cần sửa. 
                    # Giả sử: Trắng Hoa, Đen thường chuẩn FEN)
                    symbol = p.symbol
                    if p.color == 'white': symbol = symbol.upper()
                    else: symbol = symbol.lower()
                    fen += symbol
            if empty_count > 0:
                fen += str(empty_count)
            if r < 7:
                fen += "/"

        # 2. Lượt đi ('w' hoặc 'b')
        fen += " w " if self.current_turn == 'white' else " b "

        # 3. Quyền nhập thành (Castling Rights)
        # Logic đơn giản: Kiểm tra Vua và Xe có ở vị trí gốc và chưa di chuyển
        castling = ""
        # Check Trắng
        k_w = self.get_piece((7, 4))
        if k_w and k_w.symbol.upper() == 'K' and k_w.color == 'white' and not getattr(k_w, 'has_moved', True):
            r_w_k = self.get_piece((7, 7)) # Xe cánh vua
            if r_w_k and r_w_k.symbol.upper() == 'R' and not getattr(r_w_k, 'has_moved', True):
                castling += "K"
            r_w_q = self.get_piece((7, 0)) # Xe cánh hậu
            if r_w_q and r_w_q.symbol.upper() == 'R' and not getattr(r_w_q, 'has_moved', True):
                castling += "Q"
        
        # Check Đen
        k_b = self.get_piece((0, 4))
        if k_b and k_b.symbol.upper() == 'K' and k_b.color == 'black' and not getattr(k_b, 'has_moved', True):
            r_b_k = self.get_piece((0, 7))
            if r_b_k and r_b_k.symbol.upper() == 'R' and not getattr(r_b_k, 'has_moved', True):
                castling += "k"
            r_b_q = self.get_piece((0, 0))
            if r_b_q and r_b_q.symbol.upper() == 'R' and not getattr(r_b_q, 'has_moved', True):
                castling += "q"
        
        fen += castling if castling else "-"

        # 4. En Passant Target
        # Logic: Nếu nước vừa rồi là Tốt đi 2 ô, thì ô ở giữa là en passant target
        en_passant = "-"
        if self.last_move:
            p = self.last_move['piece']
            start = self.last_move['start']
            end = self.last_move['end']
            if p.symbol.upper() == 'P' and abs(start[0] - end[0]) == 2:
                # Tính ô target (hàng giữa)
                r_target = (start[0] + end[0]) // 2
                c_target = start[1]
                # Đổi sang tọa độ đại số (ví dụ e3)
                files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                en_passant = f"{files[c_target]}{8 - r_target}"
        
        fen += f" {en_passant}"

        # 5. Halfmove và Fullmove (Để tạm mặc định vì không ảnh hưởng nhiều logic cơ bản)
        fen += " 0 1"
        
        return fen
    
    # --- THÊM VÀO CLASS BOARD ---

    def move_piece_dry_run(self, start, end):
        """Đi thử: Di chuyển quân nhưng không vẽ, trả về quân bị ăn (nếu có)"""
        r1, c1 = start
        r2, c2 = end
        
        piece = self.board[r1][c1]
        target = self.board[r2][c2] # Quân bị ăn (có thể là None)
        
        # Di chuyển
        self.board[r2][c2] = piece
        self.board[r1][c1] = None
        
        # Cập nhật tọa độ nội bộ của quân cờ (nếu có)
        if hasattr(piece, 'update_position'):
            piece.update_position((r2, c2))
            
        # Đổi lượt (để sinh FEN đúng lượt tiếp theo)
        self.switch_turn()
        
        return target # Trả về để tí nữa còn hoàn tác

    def undo_move_dry_run(self, start, end, captured_piece):
        """Hoàn tác: Trả quân về vị trí cũ"""
        r1, c1 = start
        r2, c2 = end
        
        piece = self.board[r2][c2] # Quân vừa đi đến đích
        
        # Trả về chỗ cũ
        self.board[r1][c1] = piece
        self.board[r2][c2] = captured_piece # Trả lại quân bị ăn (hoặc None)
        
        # Cập nhật lại tọa độ
        if hasattr(piece, 'update_position'):
            piece.update_position((r1, c1))
            
        # Đổi lại lượt
        self.switch_turn()
    def copy(self):
        """Tạo một bản sao độc lập của bàn cờ"""
        # Tạo instance mới
        new_board = Board(self.game_type)
        
        # Copy trạng thái bàn cờ (Deepcopy để không dính dáng gì bộ nhớ cũ)
        # Lưu ý: Nếu Piece của bạn có chứa 'pygame.Surface' (ảnh), deepcopy sẽ lỗi.
        # Code Piece chuẩn thường chỉ chứa data (color, symbol), ảnh load ở UI.
        try:
            new_board.board = copy.deepcopy(self.board)
        except Exception:
            # Fallback nếu deepcopy lỗi (do dính ảnh): Copy tay
            new_board.board = [[copy.copy(p) if p else None for p in row] for row in self.board]
            
        new_board.current_turn = self.current_turn
        new_board.game_over = self.game_over
        new_board.winner = self.winner
        
        # Copy validator (quan trọng)
        new_board.validator = self.validator 
        
        return new_board
    # --- THÊM HÀM NÀY VÀO CUỐI CLASS BOARD ---
    def check_game_status(self):
        """
        Kiểm tra xem phe hiện tại (current_turn) có bị Chiếu bí hoặc Hết nước đi không.
        Hàm này được gọi ngay sau switch_turn.
        """
        if self.game_over: return

        # 1. Kiểm tra xem phe hiện tại còn nước đi hợp lệ nào không?
        has_valid_move = False
        
        # Duyệt toàn bộ bàn cờ để tìm quân của phe hiện tại
        for r in range(self.rows):
            for c in range(self.cols):
                p = self.board[r][c]
                if p and p.color == self.current_turn:
                    # Nếu tìm thấy ít nhất 1 nước đi hợp lệ -> Chưa thua
                    if self.validator:
                        moves = self.validator.get_valid_moves_for_piece(self, (r, c), self.current_turn)
                        if moves:
                            has_valid_move = True
                            break
            if has_valid_move: break
        
        # 2. Xử lý kết quả nếu không còn nước đi
        if not has_valid_move:
            self.game_over = True
            
            # Kiểm tra xem có đang bị chiếu không?
            is_in_check = False
            if self.validator:
                is_in_check = self.validator.is_in_check(self, self.current_turn)
            
            # Xác định người thắng (là người vừa đi xong -> ngược lại với current_turn)
            winner_color = 'white' if self.current_turn == 'black' else 'black'
            
            if is_in_check:
                # [CHIẾU BÍ - CHECKMATE]
                self.winner = winner_color
                print(f"🏁 CHIẾU BÍ! {winner_color.upper()} Thắng!")
            else:
                # [HẾT NƯỚC - STALEMATE]
                if self.game_type == 'chinese_chess':
                    # Luật Cờ Tướng: Hết nước đi là THUA
                    self.winner = winner_color
                    print(f"🏁 HẾT NƯỚC (Cờ Tướng)! {winner_color.upper()} Thắng!")
                else:
                    # Luật Cờ Vua: Hết nước đi (nhưng không bị chiếu) là HÒA
                    self.winner = 'draw'
                    print(f"🏁 HẾT NƯỚC (Cờ Vua)! HÒA (Stalemate)!")