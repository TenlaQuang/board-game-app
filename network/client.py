# network/client.py
import socket
from network.connection import Connection

PORT = 5050

def connect_to_server(player_name):
    """Kết nối tới host"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = input("Nhập IP của người chơi tạo phòng: ").strip() or "127.0.0.1"
    print(f"[Client] Đang kết nối tới {host_ip}:{PORT}...")
    s.connect((host_ip, PORT))

    # Nhận tên của server
    peer_name = s.recv(1024).decode('utf-8')
    # Gửi lại tên của client
    s.sendall(player_name.encode('utf-8'))

    print(f"[Client] Đã kết nối với {peer_name}")
    return Connection(s, peer_name)
