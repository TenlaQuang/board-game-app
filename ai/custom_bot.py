import torch
import random
from ai.model import XiangqiNet
from ai.preprocess import fen_to_tensor

class CustomXiangqiBot:
    def __init__(self, model_path="ai/weights/xiangqi_model.pth", depth=3):
        self.device = torch.device("cpu")
        self.model = XiangqiNet().to(self.device)
        self.depth = depth # Độ sâu suy nghĩ (2 là vừa, 3 hơi chậm)
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            # print(f"Đã nạp Model (Minimax Depth {self.depth})")
        except:
            print("⚠️ Lỗi nạp model")

    def predict(self, fen):
        with torch.no_grad():
            t = fen_to_tensor(fen).unsqueeze(0).to(self.device)
            return self.model(t).item()

    def get_best_move(self, real_board):
        # 1. TẠO BẢN SAO ĐỂ TÍNH TOÁN (Chống lỗi nhấp nháy)
        board = real_board.copy()
        
        # Fix lỗi thiếu validator trên bản sao (nếu có)
        if not hasattr(board, 'validator') or not board.validator:
            board.validator = real_board.validator
        if not board.validator: return None

        print(f"🤖 Bot đang tính Minimax {self.depth} nước...")

        # Xác định Bot là phe nào?
        # Cờ tướng: White (Đỏ) muốn MAX điểm, Black (Đen) muốn MIN điểm
        is_maximizing = (board.current_turn == 'white')
        
        # Gọi thuật toán Minimax
        # alpha = -infinity, beta = +infinity
        best_val, best_move = self.minimax(board, self.depth, -10000, 10000, is_maximizing)
        
        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        # --- ĐIỂM DỪNG ---
        # Nếu hết độ sâu hoặc game kết thúc -> Dùng Model chấm điểm
        if depth == 0 or board.game_over:
            fen = board.to_fen()
            return self.predict(fen), None

        # --- LẤY NƯỚC ĐI ---
        moves = self.get_all_moves(board)
        if not moves:
            return (0, None)

        best_move = None

        if is_maximizing: # Phe ĐỎ (Tìm điểm cao nhất)
            max_eval = -float('inf')
            for move in moves:
                start, end = move
                
                # Đi thử trên bản sao
                captured = board.move_piece_dry_run(start, end)
                
                # Đệ quy xuống tầng dưới (đến lượt phe kia -> False)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                
                # Hoàn tác
                board.undo_move_dry_run(start, end, captured)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                # Cắt tỉa Alpha
                alpha = max(alpha, eval_score)
                if beta <= alpha: break # Beta Cut-off
            
            return max_eval, best_move

        else: # Phe ĐEN (Tìm điểm thấp nhất)
            min_eval = float('inf')
            for move in moves:
                start, end = move
                
                # Đi thử
                captured = board.move_piece_dry_run(start, end)
                
                # Đệ quy (đến lượt phe kia -> True)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                
                # Hoàn tác
                board.undo_move_dry_run(start, end, captured)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                # Cắt tỉa Beta
                beta = min(beta, eval_score)
                if beta <= alpha: break # Alpha Cut-off
            
            return min_eval, best_move

    def get_all_moves(self, board):
        """Hàm tìm nước đi thủ công (Do MoveValidator thiếu hàm get_all)"""
        all_moves = []
        rows = getattr(board, 'rows', 10)
        cols = getattr(board, 'cols', 9)
        
        for r in range(rows):
            for c in range(cols):
                piece = board.board[r][c]
                if piece and piece.color == board.current_turn:
                    try:
                        # Thử gọi hàm có tham số color
                        dests = board.validator.get_valid_moves_for_piece(board, (r, c), board.current_turn)
                    except:
                        # Fallback gọi hàm cũ
                        dests = board.validator.get_valid_moves_for_piece(board, (r, c))
                    
                    if dests:
                        for d in dests: all_moves.append(((r, c), d))
        
        # Trộn ngẫu nhiên để Bot không đánh một màu
        random.shuffle(all_moves)
        return all_moves