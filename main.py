# main.py
# Nhiệm vụ: Khởi tạo NetworkManager và App, sau đó "tiêm" manager vào App.

import sys
import pygame # <-- ĐÃ THÊM: Thêm import này
from ui.window import App # <-- Import class App từ file window.py

# Kiểm tra xem file network_manager.py có tồn tại không
try:
    from network.network_manager import NetworkManager # <-- Import class NetworkManager
except ImportError:
    print("LỖI: Không tìm thấy file 'network/network_manager.py'.")
    print("Vui lòng tạo file này từ code mẫu tôi đã gửi.")
    sys.exit(1)

# Cấu hình (Bạn có thể đưa vào UI sau)
SERVER_IP = "127.0.0.1" # <-- ĐỔI THÀNH IP CỦA SERVER MAI MỐI (127.0.0.1 nếu chạy test ở máy)
SERVER_PORT = 9999
# Lấy username từ UI, tạm thời hardcode
pygame.init() # <-- ĐÃ THÊM: Khởi tạo pygame trước khi dùng time
MY_USERNAME = f"Player{pygame.time.get_ticks() % 1000}" 

if __name__ == "__main__":
    
    # 1. Tạo NetworkManager (bộ não mạng)
    network_manager = NetworkManager()
    
    # 2. Tạo App (Giao diện) và "tiêm" network_manager vào
    app = App(network_manager, SERVER_IP, SERVER_PORT, MY_USERNAME)
    
    # 3. Chạy game
    try:
        app.run()
    except KeyboardInterrupt:
        print("Đã đóng ứng dụng.")
    finally:
        # Đảm bảo dọn dẹp kết nối mạng khi thoát
        network_manager.shutdown()