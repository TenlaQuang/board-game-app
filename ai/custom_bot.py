import torch
import random
from ai.model import XiangqiNet
from ai.preprocess import fen_to_tensor

class CustomXiangqiBot:
    def __init__(self, model_path="ai/weights/xiangqi_model.pth", depth=4):
        self.device = torch.device("cpu")
        self.model = XiangqiNet().to(self.device)
        self.base_depth = depth
        
        # --- TỐI ƯU 1: BỘ NHỚ ĐỆM (Transposition Table) ---
        # Lưu kết quả chấm điểm để không phải tính lại những thế cờ trùng lặp
        self.transposition_table = {} 
        
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ Bot Speed: Cache + Beam Search (Depth {self.base_depth})")
        except:
            print("⚠️ Lỗi nạp model")

        self.piece_values = {
            'r': 90, 'n': 40, 'b': 20, 'a': 20, 'k': 1000, 'c': 45, 'p': 10,
            'R': 90, 'N': 40, 'B': 20, 'A': 20, 'K': 1000, 'C': 45, 'P': 10
        }

    def count_pieces(self, board):
        count = 0
        for r in range(10):
            for c in range(9):
                if board.board[r][c]: count += 1
        return count

    def get_best_move(self, real_board):
        # Xóa bộ nhớ đệm cũ mỗi lần đi mới (để tiết kiệm RAM)
        self.transposition_table.clear()
        
        board = real_board.copy()
        if not hasattr(board, 'validator') or not board.validator:
            board.validator = real_board.validator
        if not board.validator: return None

        # Tự động tăng độ sâu khi ít quân
        num_pieces = self.count_pieces(board)
        current_depth = self.base_depth
        
        # Chỉ tăng depth khi còn rất ít quân để tránh lag
        if num_pieces < 10: current_depth += 1 
        
        print(f"🤖 Bot tính Depth {current_depth} ({num_pieces} quân)...")

        is_maximizing = (board.current_turn == 'white')
        best_val, best_move = self.minimax(board, current_depth, -1000000, 1000000, is_maximizing)
        
        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        # 1. CHECK GAME OVER
        if board.game_over:
            if board.winner == 'white': return 100000 + depth, None
            elif board.winner == 'black': return -100000 - depth, None
            else: return 0, None

        # 2. ĐIỂM DỪNG & TRA CỨU CACHE
        # Tạo khóa (Key) đại diện cho bàn cờ hiện tại
        board_key = board.to_fen() # FEN là duy nhất cho mỗi thế cờ
        
        # Nếu thế cờ này đã từng tính rồi -> Lấy ra dùng luôn (Siêu nhanh)
        if depth == 0:
            if board_key in self.transposition_table:
                return self.transposition_table[board_key], None
            
            score = self.evaluate(board)
            self.transposition_table[board_key] = score # Lưu lại
            return score, None

        # 3. LẤY NƯỚC ĐI
        moves = self.get_ordered_moves(board)
        if not moves: return (0, None)

        # --- TỐI ƯU 2: BEAM SEARCH (CẮT TỈA) ---
        # Thay vì tính hết 40 nước đi, chỉ tính Top 10-15 nước ngon nhất
        # (Vì moves đã được sắp xếp ưu tiên ăn quân rồi)
        BEAM_WIDTH = 12 
        # Nếu đang ở độ sâu lớn (gần gốc), tính kỹ hơn. Sâu quá thì cắt bớt.
        if depth > 2: 
            moves = moves[:15] # Giữ 15 nước
        else:
            moves = moves[:10]  # Chỉ giữ 8 nước ngon nhất

        best_move = None

        if is_maximizing: # ĐỎ (Max)
            max_eval = -float('inf')
            for move in moves:
                start, end = move
                captured = board.move_piece_dry_run(start, end)
                
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                
                board.undo_move_dry_run(start, end, captured)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval, best_move

        else: # ĐEN (Min)
            min_eval = float('inf')
            for move in moves:
                start, end = move
                captured = board.move_piece_dry_run(start, end)
                
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                
                board.undo_move_dry_run(start, end, captured)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval, best_move

    def evaluate(self, board):
        # Kết hợp AI + Vật chất
        fen = board.to_fen()
        with torch.no_grad():
            t = fen_to_tensor(fen).unsqueeze(0).to(self.device)
            # Nhân 5.0 để AI quyết định chiến thuật chính
            ai_score = self.model(t).item() * 5.0 

        mat_score = self.get_material_score(board)
        return ai_score + mat_score

    def get_material_score(self, board):
        score = 0
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p:
                    val = self.piece_values.get(p.symbol, 0)
                    if p.color == 'white': score += val
                    else: score -= val
        return score / 100.0

    def get_ordered_moves(self, board):
        all_moves = []
        capture_moves = []
        quiet_moves = []
        rows = 10; cols = 9
        for r in range(rows):
            for c in range(cols):
                piece = board.board[r][c]
                if piece and piece.color == board.current_turn:
                    try:
                        dests = board.validator.get_valid_moves_for_piece(board, (r, c), board.current_turn)
                    except:
                        dests = board.validator.get_valid_moves_for_piece(board, (r, c))
                    
                    if dests:
                        for d in dests:
                            move = ((r, c), d)
                            target = board.board[d[0]][d[1]]
                            if target: # Nước ăn quân
                                val = self.piece_values.get(target.symbol, 0)
                                capture_moves.append((val, move))
                            else:
                                quiet_moves.append(move)
        
        # Sắp xếp nước ăn quân: Ăn quân to nhất lên đầu
        capture_moves.sort(key=lambda x: x[0], reverse=True)
        sorted_captures = [m[1] for m in capture_moves]
        random.shuffle(quiet_moves)
        
        return sorted_captures + quiet_moves