import torch
import random
from ai.model import XiangqiNet
from ai.preprocess import fen_to_tensor

class CustomXiangqiBot:
    def __init__(self, model_path="ai/weights/xiangqi_model.pth", depth=3):
        self.device = torch.device("cpu")
        self.model = XiangqiNet().to(self.device)
        self.base_depth = depth
        
        # --- TỐI ƯU 1: BỘ NHỚ ĐỆM (Transposition Table) ---
        self.transposition_table = {} 
        
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ Bot Ultimate: Cache + Beam + Quiescence (Depth {self.base_depth})")
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
        self.transposition_table.clear()
        
        board = real_board.copy()
        if not hasattr(board, 'validator') or not board.validator:
            board.validator = real_board.validator
        if not board.validator: return None

        # Tự động tăng độ sâu khi ít quân
        num_pieces = self.count_pieces(board)
        current_depth = self.base_depth
        if num_pieces < 16: current_depth += 1 # Ít quân thì nghĩ sâu thêm 1 nước
        if num_pieces < 6: current_depth += 3  # Sát cục thì nghĩ sâu thêm 3 nước
        
        print(f"🤖 Bot tính Depth {current_depth} ({num_pieces} quân)...")

        is_maximizing = (board.current_turn == 'white')
        best_val, best_move = self.minimax(board, current_depth, -1000000, 1000000, is_maximizing)
        
        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        # 1. CHECK GAME OVER (Ưu tiên thắng sớm)
        if board.game_over:
            if board.winner == 'white': return 100000 + depth, None
            elif board.winner == 'black': return -100000 - depth, None
            else: return 0, None

        # 2. ĐIỂM DỪNG: GỌI QUIESCENCE SEARCH
        if depth == 0:
            # Thay vì trả về điểm ngay, ta gọi tìm kiếm tĩnh để tránh bị hớ
            return self.quiescence(board, alpha, beta, is_maximizing), None

        # Tra cứu Cache
        board_key = board.to_fen()
        if board_key in self.transposition_table:
            return self.transposition_table[board_key], None

        # 3. LẤY NƯỚC ĐI
        moves = self.get_ordered_moves(board)
        if not moves: return (0, None)

        # Beam Search (Cắt tỉa)
        if depth > 2: moves = moves[:20] 
        else: moves = moves[:10]

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
            
            # Lưu vào Cache
            self.transposition_table[board_key] = max_eval
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
            
            self.transposition_table[board_key] = min_eval
            return min_eval, best_move

    def quiescence(self, board, alpha, beta, is_maximizing):
        """
        Tìm kiếm tĩnh: Đi tiếp các nước ĂN QUÂN cho đến khi yên tĩnh.
        """
        # 1. Chấm điểm hiện tại (Stand-pat)
        stand_pat = self.evaluate(board)

        # 2. Cắt tỉa sớm (Nếu đứng yên đã quá tốt/quá xấu thì không cần xét ăn quân dở)
        if is_maximizing:
            if stand_pat >= beta: return beta
            if stand_pat > alpha: alpha = stand_pat
        else:
            if stand_pat <= alpha: return alpha
            if stand_pat < beta: beta = stand_pat

        # 3. Lấy các nước ĂN QUÂN (Capture moves only)
        all_moves = self.get_ordered_moves(board)
        capture_moves = []
        
        for move in all_moves:
            start, end = move
            if board.board[end[0]][end[1]]: # Đích đến có quân -> Là nước ăn quân
                capture_moves.append(move)
        
        if not capture_moves: return stand_pat

        # 4. Duyệt các nước ăn quân (Không giới hạn độ sâu, dừng khi hết nước ăn)
        if is_maximizing:
            for move in capture_moves:
                start, end = move
                captured = board.move_piece_dry_run(start, end)
                
                score = self.quiescence(board, alpha, beta, False)
                
                board.undo_move_dry_run(start, end, captured)

                if score >= beta: return beta
                if score > alpha: alpha = score
            return alpha
        else:
            for move in capture_moves:
                start, end = move
                captured = board.move_piece_dry_run(start, end)
                
                score = self.quiescence(board, alpha, beta, True)
                
                board.undo_move_dry_run(start, end, captured)

                if score <= alpha: return alpha
                if score < beta: beta = score
            return beta

    def evaluate(self, board):
        fen = board.to_fen()
        with torch.no_grad():
            t = fen_to_tensor(fen).unsqueeze(0).to(self.device)
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
                            if target:
                                val = self.piece_values.get(target.symbol, 0)
                                capture_moves.append((val, move))
                            else:
                                quiet_moves.append(move)
        
        capture_moves.sort(key=lambda x: x[0], reverse=True)
        sorted_captures = [m[1] for m in capture_moves]
        random.shuffle(quiet_moves)
        return sorted_captures + quiet_moves