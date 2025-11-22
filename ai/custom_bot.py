import torch
from ai.model import XiangqiNet
from ai.preprocess import fen_to_tensor

class CustomXiangqiBot:
    def __init__(self, model_path="ai/weights/xiangqi_model.pth"):
        self.device = torch.device("cpu")
        self.model = XiangqiNet().to(self.device)
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ Đã nạp Model: {model_path}")
        except:
            print("⚠️ Lỗi nạp model (Bot sẽ đánh random)")

    def get_best_move(self, real_board):
        # 1. TẠO BẢN SAO (QUAN TRỌNG NHẤT)
        # AI sẽ tính trên 'board' (bản sao), không đụng vào 'real_board'
        board = real_board.copy()
        
        # --- Từ đoạn này trở đi code giữ nguyên, nhưng nó sẽ thao tác trên 'board' ảo ---
        
        # Kiểm tra validator trên bản sao
        if not hasattr(board, 'validator') or not board.validator:
            # Fallback: Gán validator từ bàn thật sang nếu bản sao bị thiếu
            board.validator = real_board.validator
        
        if not board.validator: return None

        # Thay đổi các biến gọi hàm bên dưới dùng 'board' (là bản sao)
        # Không dùng real_board nữa
        
        # Logic cũ của bạn...
        all_moves = []
        rows = getattr(board, 'rows', 10)
        cols = getattr(board, 'cols', 9)
        
        # ... (Giữ nguyên vòng lặp for tìm nước đi) ...
        for r in range(rows):
            for c in range(cols):
                piece = board.board[r][c] # Dùng board bản sao
                if piece and piece.color == board.current_turn:
                    destinations = board.validator.get_valid_moves_for_piece(board, (r, c), board.current_turn)
                    if destinations:
                        for dest in destinations:
                            all_moves.append(((r, c), dest))
        
        if not all_moves: return None

        print(f"🤖 Bot đang tính toán trên {len(all_moves)} nước đi (Bản sao)...")
        
        best_score = -9999
        best_move = None
        
        for move in all_moves:
            start, end = move
            
            # --- ĐI THỬ TRÊN BẢN SAO (Không ảnh hưởng màn hình) ---
            captured = board.move_piece_dry_run(start, end)
            
            # --- CHẤM ĐIỂM ---
            fen = board.to_fen()
            score = self.predict(fen)
            
            # --- HOÀN TÁC TRÊN BẢN SAO ---
            board.undo_move_dry_run(start, end, captured)

            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    def predict(self, fen):
        with torch.no_grad():
            t = fen_to_tensor(fen).unsqueeze(0).to(self.device)
            return self.model(t).item()