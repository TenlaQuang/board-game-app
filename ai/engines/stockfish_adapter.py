from stockfish import Stockfish
import os

class StockfishAdapter:
    def __init__(self, difficulty="MEDIUM"):
        # --- [SỬA LẠI ĐƯỜNG DẪN] ---
        # Lấy thư mục chứa file script này (tức là thư mục ai/engines/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Vì file exe nằm cùng thư mục với file .py này
        exe_path = os.path.join(current_dir, "stockfish.exe")
        
        print(f"--> [DEBUG] Đang tìm Stockfish tại: {exe_path}")

        if not os.path.exists(exe_path):
            print(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file stockfish.exe!")
            print(f"   (Bạn hãy chắc chắn file tên là 'stockfish.exe' chứ không phải tên dài ngoằng)")
            self.engine = None
            return
        
        try:
            self.engine = Stockfish(path=exe_path)
            self.set_difficulty(difficulty)
            print("✅ Kết nối Stockfish thành công!")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Stockfish: {e}")
            self.engine = None

    def set_difficulty(self, level):
        """Cấu hình độ thông minh của AI"""
        if not self.engine: return
        
        # Cấu hình: (Skill Level 0-20, Depth, Time)
        settings = {
            "EASY":   {"skill": 1,  "depth": 5,  "time": 500},
            "MEDIUM": {"skill": 10, "depth": 12, "time": 1000},
            "HARD":   {"skill": 20, "depth": 18, "time": 2000}
        }
        
        config = settings.get(level, settings["MEDIUM"])
        
        # Cập nhật params
        self.engine.set_skill_level(config["skill"])
        self.engine.set_depth(config["depth"])
        self.engine.update_engine_parameters({"Minimum Thinking Time": config["time"]})

    def get_best_move(self, fen_string):
        """Nhận chuỗi FEN bàn cờ, trả về nước đi (ví dụ: 'e2e4')"""
        if not self.engine: 
            print("⚠️ Engine chưa được khởi tạo!")
            return None
        
        try:
            if self.engine.is_fen_valid(fen_string):
                self.engine.set_fen_position(fen_string)
                return self.engine.get_best_move()
            else:
                print(f"⚠️ FEN không hợp lệ: {fen_string}")
                return None
        except Exception as e:
            print(f"Lỗi khi tính nước đi: {e}")
            return None