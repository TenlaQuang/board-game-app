# network/server.py
import socket
from network.connection import Connection

PORT = 5050

def start_server(player_name):
    """Tạo server, chờ client kết nối"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(1)
    print(f"[Server] {player_name} đang chờ kết nối...")

    conn, addr = s.accept()
    print(f"[Server] Kết nối từ {addr}")

    # Gửi tên của server cho client
    conn.sendall(player_name.encode('utf-8'))
    peer_name = conn.recv(1024).decode('utf-8')

    s.close()
    return Connection(conn, peer_name)
