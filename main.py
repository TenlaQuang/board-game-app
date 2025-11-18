# main.py
# Nhiệm vụ: Khởi tạo NetworkManager và App, sau đó "tiêm" manager vào App.

import sys
# KHÔNG CẦN pygame ở đây nữa

from ui.window import App # <-- Import class App từ file window.py

# Kiểm tra xem file network_manager.py có tồn tại không
try:
    from network.network_manager import NetworkManager # <-- Import class NetworkManager
except ImportError:
    print("LỖI: Không tìm thấy file 'network/network_manager.py'.")
    sys.exit(1)

# Cấu hình (Bạn có thể đưa vào UI sau)
SERVER_IP = "127.0.0.1" # <-- ĐỔI THÀNH IP CỦA SERVER MAI MỐI (127.0.0.1 nếu chạy test ở máy)
SERVER_PORT = 9999
# KHÔNG CẦN MY_USERNAME ở đây nữa

if __name__ == "__main__":
    
    # 1. Tạo NetworkManager (bộ não mạng)
    network_manager = NetworkManager()
    
    # 2. Tạo App (Giao diện) và "tiêm" network_manager vào
    # MODIFIED: Xóa MY_USERNAME khỏi hàm khởi tạo
    app = App(network_manager, SERVER_IP, SERVER_PORT)
    
    # 3. Chạy game
    try:
        app.run()
    except KeyboardInterrupt:
        print("Đã đóng ứng dụng.")
    finally:
        # Đảm bảo dọn dẹp kết nối mạng khi thoát
        network_manager.shutdown()