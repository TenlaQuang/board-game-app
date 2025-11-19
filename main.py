# main.py (Full Code)
import sys
import pygame

# 1. Thêm đường dẫn để Python tìm thấy các module
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Import các thành phần
try:
    from network.network_manager import NetworkManager
except ImportError as e:
    print("LỖI IMPORT NETWORK:", e)
    print("Hãy kiểm tra xem file network/network_manager.py có tồn tại và đúng cú pháp không.")
    sys.exit(1)

try:
    from ui.window import App
except ImportError as e:
    print("LỖI IMPORT UI:", e)
    sys.exit(1)

# Cấu hình Server Render (bạn có thể sửa IP/Port này nếu cần, 
# nhưng logic mới dùng web_matchmaking nên cái này chủ yếu để giữ format cũ)
SERVER_IP = "board-game-app-sv.onrender.com" 
SERVER_PORT = 80

def main():
    # Khởi tạo Network Manager
    print("Đang khởi động Network Manager...")
    network_manager = NetworkManager()

    # Khởi tạo App Giao diện
    print("Đang khởi động Giao diện...")
    # Truyền network_manager vào App để UI có thể gọi lệnh mạng
    app = App(network_manager, SERVER_IP, SERVER_PORT)

    # Chạy vòng lặp game
    app.run()

if __name__ == "__main__":
    main()