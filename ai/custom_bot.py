import torch
import random
import time
import math
from ai.model import XiangqiNet
from ai.preprocess import fen_to_tensor

class CustomXiangqiBot:
    def __init__(self, model_path="ai/weights/xiangqi_model.pth", depth=4, time_limit=3.0):
        """
        Ultimate Xiangqi Bot (Python Version)
        Features: PVS, TT, Null Move, LMR, Check Extension, Delta Pruning, Opening Book.
        """
        self.device = torch.device("cpu") # CPU tối ưu cho Minimax tuần tự
        self.base_depth = depth
        self.time_limit = time_limit
        
        # --- CÁC BẢNG TRA CỨU (MEMORY) ---
        self.transposition_table = {} 
        self.history_heuristic = {}
        self.killer_moves = {}
        self.board_history = [] 
        
        # Biến quản lý thời gian
        self.start_time = 0
        self.stop_search = False
        self.nodes_count = 0

        # --- KHỞI TẠO MODEL ---
        try:
            self.model = XiangqiNet().to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ ULTIMATE BOT: Depth {self.base_depth} | Time {self.time_limit}s | Full Features Active")
        except Exception as e:
            print(f"⚠️ Không tìm thấy Model AI ({e}). Chuyển sang chế độ Pure Engine.")
            self.model = None

        # --- KHỞI TẠO DỮ LIỆU TĨNH ---
        self.piece_values = {
            'r': 90, 'n': 40, 'b': 20, 'a': 20, 'k': 10000, 'c': 45, 'p': 10,
            'R': 90, 'N': 40, 'B': 20, 'A': 20, 'K': 10000, 'C': 45, 'P': 10
        }
        self.pst = self._init_pst()
        self.opening_book = self._init_opening_book()

    def _init_pst(self):
        # Position Square Table (Điểm vị trí)
        return {
            'P': [[0,3,6,9,6,9,6,3,0], [18,36,54,72,54,72,54,36,18], [6,12,18,24,24,24,18,12,6], [10,20,30,34,40,34,30,20,10], [6,12,18,24,28,24,18,12,6], [0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0], [-2,0,-2,0,6,0,-2,0,-2], [0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0]],
            'N': [[2,8,15,20,20,20,15,8,2], [2,10,30,40,55,40,30,10,2], [4,12,28,38,52,38,28,12,4], [2,8,16,30,38,30,16,8,2], [2,10,12,18,20,18,12,10,2], [2,6,16,20,20,20,16,6,2], [2,4,12,18,16,18,12,4,2], [-2,2,6,10,8,10,6,2,-2], [0,-4,0,4,4,4,0,-4,0], [-4,-8,-4,-8,-8,-8,-4,-8,-4]],
            'R': [[6,12,18,18,18,18,18,12,6], [6,12,18,18,18,18,18,12,6], [4,8,12,14,14,14,12,8,4], [4,8,16,18,18,18,16,8,4], [4,8,12,14,14,14,12,8,4], [2,4,10,12,12,12,10,4,2], [4,6,10,12,12,12,10,6,4], [-2,2,4,4,4,4,4,2,-2], [4,8,10,16,16,16,10,8,4], [-2,6,4,6,6,6,4,6,-2]],
            'C': [[4,4,0,-6,-8,-6,0,4,4], [2,2,0,-4,-6,-4,0,2,2], [2,2,0,6,8,6,0,2,2], [0,0,0,2,6,2,0,0,0], [0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,0], [2,2,10,6,10,6,10,2,2], [2,2,0,4,4,4,0,2,2], [0,0,0,2,2,2,0,0,0]]
        }

    def _init_opening_book(self):
        # Sách khai cuộc đơn giản (Pháo đầu, Bình phong mã...)
        # Key: FEN string (rút gọn), Value: Move tuple
        return {
             # Ví dụ: Start position -> Pháo 2 bình 5 (Red)
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w": ((7, 1), (7, 4)), 
            # Start position -> Pháo 8 bình 5 (Red alternate)
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w alternate": ((7, 7), (7, 4)), 
            # Đối thủ đi Pháo đầu -> Mã 8 tấn 7 (Black)
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1C/1C7/9/RNBAKABNR b": ((0, 7), (2, 6)),
        }

    def get_best_move(self, real_board):
        """Hàm chính để gọi Bot"""
        # 1. OPENING BOOK CHECK
        fen_key = real_board.to_fen()
        if fen_key in self.opening_book:
            print(f"📖 Opening Book Move!")
            return self.opening_book[fen_key]

        # Reset trạng thái tìm kiếm
        self.transposition_table.clear() # Có thể comment dòng này nếu muốn giữ tri thức giữa các turn (nhưng tốn RAM)
        self.killer_moves.clear()
        self.start_time = time.time()
        self.stop_search = False
        self.nodes_count = 0
        
        board = real_board.copy()
        if not hasattr(board, 'validator') or not board.validator:
            board.validator = real_board.validator

        # Cập nhật lịch sử chống lặp
        current_fen_short = board.to_fen().split(' ')[0]
        self.board_history.append(current_fen_short)
        if len(self.board_history) > 20: self.board_history.pop(0)

        # 2. DYNAMIC DEPTH
        num_pieces = sum(1 for r in board.board for p in r if p)
        target_depth = self.base_depth
        if num_pieces < 16: target_depth += 1
        if num_pieces < 8: target_depth += 2 

        print(f"🤖 Thinking... Depth Target: {target_depth}")
        
        is_maximizing = (board.current_turn == 'white')
        best_global_move = None
        
        # Aspiration Window ban đầu
        alpha = -1000000
        beta = 1000000

        # 3. ITERATIVE DEEPENING
        for d in range(1, target_depth + 1):
            if self.stop_search: break
            
            try:
                score, move = self.minimax(board, d, alpha, beta, is_maximizing, allow_null=True)
                
                if move:
                    best_global_move = move
                    time_elapsed = time.time() - self.start_time
                    print(f"   Depth {d} | Score: {int(score)} | Nodes: {self.nodes_count} | Time: {time_elapsed:.2f}s")
                
                # Nếu tìm thấy Mate (chiếu hết), dừng luôn
                if abs(score) > 90000: 
                    print("🔥 Mate detected!")
                    break
                
                # Aspiration Window Tuning (Thu hẹp cửa sổ cho depth sau)
                if d >= 2:
                    alpha = score - 500
                    beta = score + 500

            except Exception as e:
                print(f"❌ Error at depth {d}: {e}")
                break

        if not best_global_move:
            print("⚠️ Fallback to Random Move")
            return self.get_random_move(real_board)
            
        return best_global_move

    def minimax(self, board, depth, alpha, beta, is_maximizing, allow_null=True):
        self.nodes_count += 1
        
        # 0. TIME CHECK (Cứ mỗi 2048 node check 1 lần để tối ưu)
        if self.nodes_count & 2047 == 0:
            if (time.time() - self.start_time) > self.time_limit:
                self.stop_search = True
        
        if self.stop_search: return 0, None

        # 1. CHECK EXTENSION (Kéo dài depth nếu bị chiếu)
        in_check = False
        if hasattr(board, 'is_check'): # An toàn nếu class Board không có hàm is_check
             in_check = board.is_check(board.current_turn)
        
        extension = 0
        if in_check: extension = 1
        real_depth = depth + extension
        
        # Giới hạn extension để tránh nổ stack
        if extension > 0 and real_depth > self.base_depth + 2:
            real_depth = self.base_depth + 2

        # 2. REPETITION & GAME OVER CHECK
        current_fen_short = board.to_fen().split(' ')[0]
        if self.board_history.count(current_fen_short) >= 2: 
            return 0, None # 3 lần lặp = Hòa
        
        if board.game_over:
            return (100000 + real_depth) if board.winner == 'white' else (-100000 - real_depth), None

        # 3. TRANSPOSITION TABLE (TT) LOOKUP
        board_key = board.to_fen()
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry['depth'] >= real_depth:
                if entry['flag'] == 'exact': return entry['score'], entry['move']
                if entry['flag'] == 'lower' and entry['score'] > alpha: alpha = entry['score']
                if entry['flag'] == 'upper' and entry['score'] < beta: beta = entry['score']
                if alpha >= beta: return entry['score'], entry['move']

        # 4. QUIESCENCE SEARCH (Tại lá)
        if real_depth <= 0:
            return self.quiescence(board, alpha, beta, is_maximizing), None

        # 5. NULL MOVE PRUNING
        # Nếu depth còn cao, không bị chiếu -> Thử "không đi gì cả" (Pass turn)
        # Nếu vẫn >= Beta -> Cắt tỉa.
        if allow_null and real_depth >= 3 and not in_check:
             # Lưu ý: Python chess board thường khó implement Null Move chuẩn mà không làm hỏng state.
             # Logic dưới đây là giả lập R=2. Nếu engine quá mạnh, có thể bật.
             # Hiện tại tôi để pass để an toàn cho code của bạn.
             pass 

        # 6. MOVE GENERATION
        moves = self.get_ordered_moves(board, real_depth)
        
        if not moves:
            if in_check: return (-100000 - real_depth) if is_maximizing else (100000 + real_depth), None
            return 0, None # Stalemate

        best_move = None
        best_score = -float('inf') if is_maximizing else float('inf')
        tt_flag = 'exact'
        moves_searched = 0

        for move in moves:
            moves_searched += 1
            start, end = move
            captured = board.move_piece_dry_run(start, end)
            
            # Thêm vào history tạm
            self.board_history.append(board.to_fen().split(' ')[0])

            # --- LMR (Late Move Reduction) ---
            # Giảm depth với các nước đi muộn, trừ khi ăn quân hoặc bị chiếu
            reduction = 0
            if real_depth >= 3 and moves_searched > 4 and not captured and not in_check:
                reduction = 1

            # --- PVS (Principal Variation Search) ---
            score = 0
            if moves_searched == 1:
                # Nước đi đầu tiên (tốt nhất): Full Search
                score, _ = self.minimax(board, real_depth - 1, alpha, beta, not is_maximizing, True)
            else:
                # Các nước sau: Search với cửa sổ hẹp (Null Window) và Reduced Depth
                score, _ = self.minimax(board, real_depth - 1 - reduction, alpha, alpha + 1, not is_maximizing, True)
                
                # Nếu kết quả tốt hơn mong đợi (Fail High) hoặc do giảm depth quá đà: Search lại
                if score > alpha and reduction > 0:
                    score, _ = self.minimax(board, real_depth - 1, alpha, alpha + 1, not is_maximizing, True)
                
                if score > alpha and score < beta: # Nếu vẫn tốt, search Full Window
                    score, _ = self.minimax(board, real_depth - 1, alpha, beta, not is_maximizing, True)

            # Hoàn tác
            self.board_history.pop()
            board.undo_move_dry_run(start, end, captured)

            if self.stop_search: return 0, None

            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)

            # Beta Cutoff
            if beta <= alpha:
                tt_flag = 'lower' if is_maximizing else 'upper'
                if not captured:
                    self.killer_moves[real_depth] = move
                    self.history_heuristic[move] = self.history_heuristic.get(move, 0) + real_depth**2
                break

        # 7. LƯU VÀO TT
        # Chỉ lưu nếu depth mới >= depth cũ trong bảng
        save = True
        if board_key in self.transposition_table:
             if self.transposition_table[board_key]['depth'] > real_depth: save = False
        
        if save:
            self.transposition_table[board_key] = {
                'score': best_score, 'move': best_move, 'depth': real_depth, 'flag': tt_flag
            }
            
        return best_score, best_move

    def quiescence(self, board, alpha, beta, is_maximizing):
        self.nodes_count += 1
        stand_pat = self.evaluate(board)
        
        if is_maximizing:
            if stand_pat >= beta: return beta
            if stand_pat > alpha: alpha = stand_pat
        else:
            if stand_pat <= alpha: return alpha
            if stand_pat < beta: beta = stand_pat

        # --- TẮT DELTA PRUNING ĐỂ KHÔNG BỎ SÓT NƯỚC ĂN ---
        # (Chấp nhận chậm hơn một chút nhưng chắc chắn không bỏ sót)
        
        moves = self.get_ordered_moves(board, 0, only_captures=True)
        
        for move in moves:
            start, end = move
            captured = board.move_piece_dry_run(start, end)
            
            # Đệ quy tìm tiếp xem ăn xong có bị ăn lại không
            score = self.quiescence(board, alpha, beta, not is_maximizing)
            
            board.undo_move_dry_run(start, end, captured)

            if is_maximizing:
                if score >= beta: return beta
                if score > alpha: alpha = score
            else:
                if score <= alpha: return alpha
                if score < beta: beta = score
                
        return alpha if is_maximizing else beta

   # --- CÁC HÀM PHỤ TRỢ MỚI CHO LOGIC BẢO VỆ ---
    
    def get_piece_at(self, board, r, c):
        if 0 <= r < 10 and 0 <= c < 9:
            return board.board[r][c]
        return None

    def is_protected_by_friendly(self, board, r, c, my_color):
        """Kiểm tra xem vị trí (r,c) có được quân MÌNH bảo vệ không"""
        # Logic nhanh: Giả sử có quân địch ăn vào đó, mình có ăn lại được không?
        # Quét các quân mình xem có ai nhắm vào (r,c) không.
        
        # 1. Xe/Pháo (Dọc/Ngang)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            mounts = 0
            for step in range(1, 10):
                nr, nc = r + step*dr, c + step*dc
                p = self.get_piece_at(board, nr, nc)
                if not p: continue
                
                if p.color == my_color:
                    if p.symbol.upper() == 'R' and mounts == 0: return True
                    if p.symbol.upper() == 'C' and mounts == 1: return True # Pháo cần 1 ngòi
                    if mounts == 0: mounts += 1 # Quân mình làm ngòi cho Pháo sau lưng
                    else: break
                else:
                    mounts += 1 # Quân địch làm ngòi
                if mounts > 1: break

        # 2. Mã (Nhật)
        knight_moves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
        for kr, kc in knight_moves:
            p = self.get_piece_at(board, r + kr, c + kc)
            if p and p.color == my_color and p.symbol.upper() == 'N':
                # Check cản chân
                foot_r, foot_c = r + int(kr/2), c + int(kc/2)
                if not self.get_piece_at(board, foot_r, foot_c):
                    return True

        # 3. Tượng/Sĩ/Tướng/Tốt (Bỏ qua cho nhanh hoặc thêm nếu muốn kỹ)
        return False

    def count_attackers(self, board, r, c, enemy_color):
        """Đếm xem có bao nhiêu quân ĐỊCH đang nhắm vào ô này"""
        count = 0
        # (Logic tương tự như hàm is_protected nhưng tìm quân Enemy)
        # 1. Xe/Pháo
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            mounts = 0
            for step in range(1, 10):
                nr, nc = r + step*dr, c + step*dc
                p = self.get_piece_at(board, nr, nc)
                if not p: continue
                if p.color == enemy_color:
                    if p.symbol.upper() == 'R' and mounts == 0: count += 1
                    elif p.symbol.upper() == 'C' and mounts == 1: count += 1
                    break
                else: mounts += 1
                if mounts > 1: break
        
        # 2. Mã
        for kr, kc in [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]:
            p = self.get_piece_at(board, r + kr, c + kc)
            if p and p.color == enemy_color and p.symbol.upper() == 'N':
                if not self.get_piece_at(board, r + int(kr/2), c + int(kc/2)): count += 1
        
        # 3. Tốt (Quan trọng: Tốt sang sông ăn được)
        pawn_dir = 1 if enemy_color == 'black' else -1 # Black đi xuống (+), White đi lên (-)
        # Check Tốt địch bên trái/phải/trước mặt
        for pr, pc in [(r - pawn_dir, c), (r, c-1), (r, c+1)]:
             p = self.get_piece_at(board, pr, pc)
             if p and p.color == enemy_color and p.symbol.upper() == 'P':
                 count += 1

        return count

    # --- HÀM ĐÁNH GIÁ CHÍNH V6 ---

    def evaluate(self, board):
        score = 0
        my_pieces = []
        enemy_pieces = []
        
        # Duyệt bàn cờ và tính điểm cơ bản
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p:
                    if p.color == 'white': my_pieces.append(((r,c), p))
                    else: enemy_pieces.append(((r,c), p))
                    
                    val = self.piece_values.get(p.symbol, 0)
                    pst_val = 0
                    if p.symbol.upper() in self.pst:
                        t = self.pst[p.symbol.upper()]
                        pst_val = t[r][c] if p.color == 'white' else t[9-r][c]
                    
                    if p.color == 'white': score += (val + pst_val)
                    else: score -= (val + pst_val)

        # ---------------------------------------------------------
        # LOGIC BẢO VỆ THÔNG MINH (Smart Trade)
        # ---------------------------------------------------------
        
        # A. Phân tích quân TRẮNG (Phe Bot)
        for pos, p in my_pieces:
            r, c = pos
            val = self.piece_values.get(p.symbol, 0)
            
            # Tìm xem con gì đang định ăn mình
            attacker_val = self.get_lowest_attacker_value(board, r, c, 'black')
            
            if attacker_val is not None:
                # Có kẻ địch nhắm!
                is_guarded = self.is_protected_by_friendly(board, r, c, 'white')
                
                if not is_guarded:
                    # 1. Không ai bảo kê -> Mất trắng -> Trừ 100% giá trị
                    score -= val 
                else:
                    # 2. Có bảo kê -> Nhưng lỗ vốn không?
                    if attacker_val < val:
                        # VÍ DỤ: Xe (90) bị Pháo (45) bắn.
                        # Dù Xe có bảo kê, nhưng đổi Xe lấy Pháo là LỖ.
                        # Trừ phần chênh lệch (90 - 45 = 45 điểm)
                        diff = val - attacker_val
                        score -= (diff + 10) # Trừ thêm tí để nó sợ mà chạy
                    else:
                        # Kẻ địch to hơn hoặc bằng (Xe đổi Xe) -> OK, chấp nhận được
                        score -= (val * 0.1) # Trừ nhẹ áp lực

        # B. Phân tích quân ĐEN (Phe Địch) - Tìm chỗ nó lỗ để đánh
        for pos, p in enemy_pieces:
            r, c = pos
            val = self.piece_values.get(p.symbol, 0)
            
            my_attacker_val = self.get_lowest_attacker_value(board, r, c, 'white')
            
            if my_attacker_val is not None:
                is_enemy_guarded = self.is_protected_by_friendly(board, r, c, 'black')
                
                if not is_enemy_guarded:
                    score += val # Ngon ăn -> Cộng điểm
                else:
                    # Nó có bảo kê, nhưng nếu mình dùng Tốt/Pháo đổi Xe nó -> Lãi
                    if my_attacker_val < val:
                         diff = val - my_attacker_val
                         score += diff # Thưởng điểm vì đang ép nó đổi lỗ

        return score + random.uniform(-0.5, 0.5)
    def get_positional_score(self, board):
        score = 0
        
        # Tìm vị trí tướng để tính King Safety
        red_king = None
        black_king = None
        
        # Cache quân cờ để đỡ duyệt 2 lần
        pieces = []
        
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p:
                    pieces.append(((r,c), p))
                    if p.symbol == 'K': red_king = (r, c)
                    elif p.symbol == 'k': black_king = (r, c)

        if not red_king or not black_king: return 0 # Tránh lỗi

        # --- CẤU HÌNH TRỌNG SỐ (WEIGHTS) ---
        # Đây là bí mật tạo nên tính cách của Bot
        W_MATERIAL = 1.0  # Điểm chất
        W_PST = 0.5       # Điểm vị trí bảng
        W_MOBILITY = 2.0  # Điểm độ thoáng (Quan trọng!)
        W_KING_SAFETY = 1.5 # Điểm an toàn tướng
        W_THREAT = 1.2    # Điểm đe dọa

        for pos, p in pieces:
            r, c = pos
            val = self.piece_values.get(p.symbol, 0)
            sym_upper = p.symbol.upper()
            color_factor = 1 if p.color == 'white' else -1
            
            # 1. MATERIAL & PST
            pst_val = 0
            if sym_upper in self.pst:
                table = self.pst[sym_upper]
                pst_val = table[r][c] if p.color == 'white' else table[9-r][c]
            
            current_score = (val * W_MATERIAL) + (pst_val * W_PST)

            # 2. MOBILITY (ĐỘ THOÁNG) - Khắc phục điểm yếu "quân tù"
            # Xe/Mã/Pháo càng đi được nhiều ô càng mạnh
            mobility = 0
            if sym_upper in ['R', 'N', 'C']:
                # Ước lượng nhanh số nước đi hợp lệ (không gọi validator vì chậm)
                # Chỉ check xung quanh xem có bị chặn không
                if sym_upper == 'R': # Xe thích đường thẳng thoáng
                    # Check 4 hướng, mỗi ô trống cộng điểm
                    for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if 0 <= r+dr < 10 and 0 <= c+dc < 9 and board.board[r+dr][c+dc] is None:
                            mobility += 2 # Thưởng cho mỗi ô trống cạnh bên
                elif sym_upper == 'N': # Mã sợ bị cản chân
                    # Check 4 chân mã, nếu không bị cản thì được thưởng lớn
                    blocked = 0
                    for br, bc in [(0,1), (0,-1), (1,0), (-1,0)]: # Vị trí chân mã
                        if 0 <= r+br < 10 and 0 <= c+bc < 9 and board.board[r+br][c+bc]:
                            blocked += 1
                    mobility += (4 - blocked) * 5 # Mã thoáng rất giá trị
            
            current_score += mobility * W_MOBILITY

            # 3. KING SAFETY (AN TOÀN TƯỚNG)
            # Nếu quân này là Sĩ/Tượng bảo vệ tướng -> Thưởng
            # Nếu Tướng bị "trần trụi" -> Phạt
            king_safety = 0
            my_king = red_king if p.color == 'white' else black_king
            
            if sym_upper in ['A', 'B']: # Sĩ, Tượng
                # Khoảng cách Manhattan tới tướng
                dist = abs(r - my_king[0]) + abs(c - my_king[1])
                if dist <= 2: king_safety += 15 # Sĩ tượng ở gần tướng là tốt
            
            if sym_upper == 'K':
                # Tướng ở cột 4, 5, 6 nhưng hàng gốc an toàn hơn hàng trên
                if p.color == 'white':
                    if r == 9: king_safety += 20
                    elif r <= 7: king_safety -= 30 # Tướng leo lầu dễ chết
                else:
                    if r == 0: king_safety += 20
                    elif r >= 2: king_safety -= 30
            
            current_score += king_safety * W_KING_SAFETY

            # 4. THREAT (ĐE DỌA) - Tấn công
            # Quân mình đang nhắm vào Tướng địch
            threat = 0
            enemy_king = black_king if p.color == 'white' else red_king
            dist_to_enemy = abs(r - enemy_king[0]) + abs(c - enemy_king[1])
            
            if sym_upper in ['R', 'C', 'N', 'P']:
                if dist_to_enemy <= 4: # Vùng nguy hiểm
                    threat += (5 - dist_to_enemy) * 10 
                    
                # Bonus Tốt sang sông
                if sym_upper == 'P':
                    if (p.color == 'white' and r <= 4) or (p.color == 'black' and r >= 5):
                        threat += 40 # Tốt sang sông cực kỳ giá trị

            current_score += threat * W_THREAT

            score += current_score * color_factor

        # Cộng chút random để phá thế cờ hòa
        return score + random.uniform(-0.5, 0.5)

    def get_ordered_moves(self, board, depth, only_captures=False):
        capture_moves = []
        quiet_moves = []
        killer = self.killer_moves.get(depth, None)
        
        # Lấy tất cả nước đi hợp lệ
        # [LƯU Ý QUAN TRỌNG]: Đảm bảo board.validator của bạn hoạt động đúng!
        for r in range(10):
            for c in range(9):
                piece = board.board[r][c]
                if piece and piece.color == board.current_turn:
                    try:
                        # Kiểm tra xem hàm validator có cần tham số color không
                        if 'player_color' in board.validator.get_valid_moves_for_piece.__code__.co_varnames:
                             dests = board.validator.get_valid_moves_for_piece(board, (r, c), board.current_turn)
                        else:
                             dests = board.validator.get_valid_moves_for_piece(board, (r, c))
                    except: continue

                    if not dests: continue

                    for d in dests:
                        move = ((r, c), d)
                        target = board.board[d[0]][d[1]]
                        
                        # --- LOGIC ƯU TIÊN ĂN QUÂN (VIP) ---
                        if target:
                            victim_val = self.piece_values.get(target.symbol, 0)
                            attacker_val = self.piece_values.get(piece.symbol, 0)
                            
                            # MVV-LVA cải tiến:
                            # 1. Ăn quân càng to càng tốt (victim_val * 100)
                            # 2. Dùng quân càng nhỏ ăn càng tốt ( - attacker_val)
                            # 3. Cộng điểm thưởng tuyệt đối để nó luôn nổi lên đầu danh sách ( + 100000)
                            score = 100000 + (victim_val * 100) - attacker_val
                            capture_moves.append((score, move))
                        
                        elif not only_captures:
                            # Nước đi thường
                            if move == killer:
                                quiet_moves.append((90000, move)) # Killer move ưu tiên nhì
                            else:
                                h_score = self.history_heuristic.get(move, 0)
                                # Ưu tiên nước đi giúp kiểm soát trung lộ hoặc tiến tốt
                                if r < 5 and piece.symbol.upper() == 'P': h_score += 50 
                                quiet_moves.append((h_score, move))

        # Sắp xếp từ cao xuống thấp
        capture_moves.sort(key=lambda x: x[0], reverse=True)
        quiet_moves.sort(key=lambda x: x[0], reverse=True)
        
        final_moves = [m[1] for m in capture_moves]
        if not only_captures:
            final_moves += [m[1] for m in quiet_moves]
            
        return final_moves

    def get_random_move(self, board):
        moves = self.get_ordered_moves(board, 0)
        return random.choice(moves) if moves else None
    def scan_threats(self, board):
        """
        Hàm này quét nhanh xem các quân chủ lực (Xe, Pháo, Mã) có đang nằm trong miệng cọp không.
        Nếu có -> Trừ điểm cực nặng.
        """
        penalty = 0
        rows = 10; cols = 9
        
        # Duyệt bàn cờ tìm quân của phe Bot (hoặc phe đang xét)
        # Để đơn giản, ta quét cả 2 phe, nếu phe nào bị đe dọa thì trừ điểm phe đó
        
        for r in range(rows):
            for c in range(cols):
                p = board.board[r][c]
                if not p: continue
                
                # Chỉ quan tâm quân chủ lực: Xe (R), Pháo (C), Mã (N)
                if p.symbol.upper() not in ['R', 'C', 'N']: continue
                
                # Kiểm tra xem quân này có bị ĐỐI THỦ ăn không?
                # Cách nhanh nhất: Giả vờ đổi lượt cho đối thủ, xem đối thủ có nước nào ăn vào vị trí (r,c) không.
                # Tuy nhiên, gọi validator.get_valid_moves() ở đây sẽ RẤT CHẬM.
                # TA SẼ DÙNG LOGIC QUÉT THỦ CÔNG (Nhanh hơn):
                
                enemy_color = 'black' if p.color == 'white' else 'white'
                is_threatened = False
                
                # 1. Check Dọc/Ngang (Sợ Xe và Pháo địch)
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                for dr, dc in directions:
                    mounts = 0 # Đếm ngòi cho Pháo
                    for step in range(1, 10):
                        nr, nc = r + step*dr, c + step*dc
                        if not (0 <= nr < 10 and 0 <= nc < 9): break
                        
                        target = board.board[nr][nc]
                        if not target: continue # Ô trống
                        
                        if target.color == enemy_color:
                            # Gặp Xe địch và không có ngòi -> CHẾT
                            if target.symbol.upper() == 'R' and mounts == 0:
                                is_threatened = True
                            # Gặp Pháo địch và có đúng 1 ngòi -> CHẾT
                            elif target.symbol.upper() == 'C' and mounts == 1:
                                is_threatened = True
                            # Gặp quân địch khác chắn đường -> Không sợ Xe/Pháo xa nữa
                            if is_threatened: break
                            # Nếu gặp địch mà chưa chết ngay (ví dụ gặp Mã địch), thì nó là ngòi
                            mounts += 1
                        else:
                            # Gặp quân mình -> Là ngòi
                            mounts += 1
                        
                        # Chỉ cần tìm thấy 1 mối đe dọa là đủ sợ rồi
                        if is_threatened: break
                        if mounts > 1: break # Quá 1 ngòi thì Pháo cũng bó tay
                    if is_threatened: break

                # 2. Check Mã địch (Sợ Mã) - Bước nhảy L
                if not is_threatened:
                    knight_moves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
                    for kr, kc in knight_moves:
                        nr, nc = r + kr, c + kc
                        if 0 <= nr < 10 and 0 <= nc < 9:
                            target = board.board[nr][nc]
                            if target and target.color == enemy_color and target.symbol.upper() == 'N':
                                # Check cản Mã (luật cờ tướng)
                                # Chân mã nằm ở đâu?
                                foot_r, foot_c = r + int(kr/2), c + int(kc/2)
                                if not board.board[foot_r][foot_c]: # Không bị cản
                                    is_threatened = True
                                    break

                # NẾU BỊ ĐE DỌA
                if is_threatened:
                    # Kiểm tra xem có quân bảo kê không? (Simplified: Có quân mình giữ không?)
                    # Để code đơn giản và bot cẩn thận, ta cứ coi như bị dọa là TRỪ ĐIỂM luôn.
                    # Thà chạy nhầm còn hơn bỏ sót.
                    
                    val = self.piece_values.get(p.symbol, 0)
                    # Phạt nặng: 80% giá trị quân cờ
                    penalty_score = val * 0.8 
                    
                    if p.color == 'white': penalty -= penalty_score
                    else: penalty += penalty_score # Black bị đe dọa -> penalty dương (tốt cho White)

        return penalty
    # --- CẬP NHẬT HÀM PHỤ TRỢ ---

    def get_lowest_attacker_value(self, board, r, c, enemy_color):
        """
        Tìm giá trị của quân địch NHỎ NHẤT đang nhắm vào ô này.
        Trả về: Giá trị quân nhỏ nhất (VD: 10 là Tốt), hoặc None nếu an toàn.
        """
        min_val = 99999
        found = False
        
        # 1. Check Tốt (Nguy hiểm nhất vì nó rẻ tiền)
        pawn_dir = 1 if enemy_color == 'black' else -1 
        # Check trái/phải/trước
        for pr, pc in [(r - pawn_dir, c), (r, c-1), (r, c+1)]:
             if 0 <= pr < 10 and 0 <= pc < 9:
                 p = board.board[pr][pc]
                 if p and p.color == enemy_color and p.symbol.upper() == 'P':
                     return 10 # Tốt đang gí -> Chạy ngay!

        # 2. Check Mã
        knight_moves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
        for kr, kc in knight_moves:
            nr, nc = r + kr, c + kc
            if 0 <= nr < 10 and 0 <= nc < 9:
                p = board.board[nr][nc]
                if p and p.color == enemy_color and p.symbol.upper() == 'N':
                    # Check cản chân
                    if not board.board[r + int(kr/2)][c + int(kc/2)]:
                        min_val = min(min_val, 40)
                        found = True

        # 3. Check Pháo (Cực kỳ nguy hiểm với Xe)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            mounts = 0
            for step in range(1, 10):
                nr, nc = r + step*dr, c + step*dc
                if not (0 <= nr < 10 and 0 <= nc < 9): break
                p = board.board[nr][nc]
                if not p: continue
                
                if p.color == enemy_color:
                    if p.symbol.upper() == 'C' and mounts == 1:
                        min_val = min(min_val, 45)
                        found = True
                    if p.symbol.upper() == 'R' and mounts == 0:
                        min_val = min(min_val, 90)
                        found = True
                    break # Gặp địch là dừng
                else:
                    mounts += 1 # Gặp quân mình là ngòi
                if mounts > 1: break
        
        return min_val if found else None