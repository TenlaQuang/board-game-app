# Tên file: matchmaking_server.py (Chạy riêng biệt)
import socket
import threading
import json

# Dùng 0.0.0.0 để chấp nhận kết nối từ mọi IP
HOST = '0.0.0.0' 
PORT = 9999      # Cổng cho server mai mối
P2P_PORT = 12345 # Cổng cố định cho P2P (cần mở cổng này)

clients = {} # Lưu trữ: { "username": (socket_conn, address) }
lobby = {}   # Lưu trữ: { "username": "idle" | "in_game" }

def handle_client(conn, addr):
    """Xử lý từng client kết nối đến server mai mối."""
    print(f"[NEW] {addr} đã kết nối.")
    current_username = None
    
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            try:
                command = json.loads(data)
                
                # 1. Đăng ký tên
                if command.get('type') == 'register':
                    username = command['username']
                    if username not in clients:
                        current_username = username
                        clients[username] = (conn, addr)
                        lobby[username] = "idle"
                        print(f"[REGISTER] {addr} là {username}")
                        conn.sendall(json.dumps({"type": "register_ok"}).encode('utf-8'))
                    else:
                        conn.sendall(json.dumps({"type": "error", "message": "Tên đã tồn tại"}).encode('utf-8'))

                # 2. Lấy danh sách người chơi rảnh
                elif command.get('type') == 'get_lobby':
                    idle_players = [user for user, status in lobby.items() if status == 'idle' and user != current_username]
                    conn.sendall(json.dumps({"type": "lobby_list", "players": idle_players}).encode('utf-8'))

                # 3. Mời chơi
                elif command.get('type') == 'invite':
                    target_username = command['target']
                    if target_username in clients:
                        target_conn = clients[target_username][0]
                        # Chuyển tiếp lời mời
                        target_conn.sendall(json.dumps({"type": "invited", "from": current_username}).encode('utf-8'))
                        print(f"[INVITE] {current_username} mời {target_username}")
                    else:
                        conn.sendall(json.dumps({"type": "error", "message": "Người chơi không online"}).encode('utf-8'))

                # 4. Chấp nhận (Phần "Dắt Tay" quan trọng)
                elif command.get('type') == 'accept':
                    target_username = command['target'] # Người đã mời mình
                    
                    if target_username in clients:
                        # Chỉ định vai trò: Người mời (target) làm Host, Người chấp nhận (current) làm Client
                        host_username = target_username
                        client_username = current_username
                        
                        host_conn, host_addr = clients[host_username]
                        client_conn, client_addr = clients[client_username]
                        
                        # host_addr[0] là IP mà server THẤY (Public IP hoặc LAN IP)
                        host_ip = host_addr[0]
                        
                        print(f"[MATCH] {host_username} (Host) vs {client_username} (Client) tại IP: {host_ip}")
                        
                        # Lệnh cho Host: "Bạn làm Host, mở cổng P2P_PORT"
                        host_conn.sendall(json.dumps({
                            "type": "start_game",
                            "role": "host",
                            "port": P2P_PORT,
                            "opponent_username": client_username # Báo host biết client là ai
                        }).encode('utf-8'))
                        
                        # Lệnh cho Client: "Bạn làm Client, kết nối đến IP của Host"
                        client_conn.sendall(json.dumps({
                            "type": "start_game",
                            "role": "client",
                            "opponent_ip": host_ip,
                            "port": P2P_PORT,
                            "opponent_username": host_username # Báo client biết host là ai
                        }).encode('utf-8'))
                        
                        lobby[host_username] = "in_game"
                        lobby[client_username] = "in_game"
            
            except json.JSONDecodeError:
                print(f"[ERROR] Dữ liệu JSON lỗi từ {addr}")
            except Exception as e:
                print(f"[ERROR] Lỗi xử lý client: {e}")

    except Exception:
        print(f"[DISCONNECT] {addr} ngắt kết nối.")
    finally:
        if current_username:
            if current_username in clients:
                del clients[current_username]
            if current_username in lobby:
                del lobby[current_username]
            print(f"[DISCONNECT] {current_username} đã thoát.")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Server 'Mai Mối' đang lắng nghe trên {HOST}:{PORT}")
    
    while True:
        conn, addr = server.accept()
        # Tạo luồng mới cho mỗi client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_server()