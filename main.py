# main.py (Full Code)
import sys
import pygame

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

SERVER_IP = "board-game-app-sv.onrender.com" 
SERVER_PORT = 80

def main():
    # Khởi tạo Network Manager
    print("Đang khởi động Network Manager...")
    network_manager = NetworkManager()

    # Khởi tạo App Giao diện
    print("Đang khởi động Giao diện...")

    app = App(network_manager, SERVER_IP, SERVER_PORT)

    # Chạy vòng lặp game
    app.run()

if __name__ == "__main__":
    main()