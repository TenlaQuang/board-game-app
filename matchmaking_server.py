import socket
import threading
import json

# Cấu hình
HOST = '0.0.0.0'
PORT = 9999
P2P_PORT = 12345

clients = {} # { "username": (conn, addr) }
lobby = {}   # { "username": "idle" | "in_game" }
lobby_lock = threading.Lock() # NEW: Dùng Lock để tránh tranh chấp dữ liệu giữa các luồng

def send_json(conn, data_dict):
    """Hàm tiện ích để gửi JSON kèm ký tự xuống dòng \n"""
    try:
        message = json.dumps(data_dict) + "\n" # QUAN TRỌNG: Thêm \n
        conn.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Lỗi gửi tin: {e}")

def handle_client(conn, addr):
    """Xử lý client với bộ đệm (Buffer) để chống phân mảnh TCP."""
    print(f"[NEW] {addr} đã kết nối.")
    current_username = None
    buffer = "" # Bộ đệm chứa dữ liệu chưa xử lý

    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            buffer += data
            
            # Xử lý cắt dòng \n (Line Delimiter Protocol)
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                message = message.strip()
                if not message: continue # Bỏ qua dòng trống

                try:
                    command = json.loads(message)
                    # print(f"[RECV] {addr}: {command}") # Bật lên nếu muốn debug kỹ

                    # --- XỬ LÝ LOGIC ---

                    # 1. Đăng ký
                    if command.get('type') == 'register':
                        username = command['username']
                        with lobby_lock: # Dùng lock khi sửa biến toàn cục
                            if username not in clients:
                                current_username = username
                                clients[username] = (conn, addr)
                                lobby[username] = "idle"
                                print(f"[REGISTER] {addr} -> {username}")
                                send_json(conn, {"type": "register_ok"})
                            else:
                                send_json(conn, {"type": "error", "message": "Tên đã tồn tại"})

                    # 2. Lấy danh sách Lobby
                    elif command.get('type') == 'get_lobby':
                        with lobby_lock:
                            idle_players = [u for u, s in lobby.items() if s == 'idle' and u != current_username]
                        send_json(conn, {"type": "lobby_list", "players": idle_players})

                    # 3. Mời chơi
                    elif command.get('type') == 'invite':
                        target = command['target']
                        target_conn = None
                        with lobby_lock:
                            if target in clients and lobby.get(target) == 'idle':
                                target_conn = clients[target][0]
                        
                        if target_conn:
                            send_json(target_conn, {"type": "invited", "from": current_username})
                            print(f"[INVITE] {current_username} -> {target}")
                        else:
                            send_json(conn, {"type": "error", "message": "Người chơi bận hoặc offline"})

                    # 4. Chấp nhận lời mời
                    elif command.get('type') == 'accept':
                        target_username = command['target'] # Người đã mời (sẽ thành Host)
                        
                        host_conn = None
                        client_conn = conn # Mình là người chấp nhận (sẽ thành Client)
                        
                        host_ip = None

                        with lobby_lock:
                            if target_username in clients:
                                host_conn, host_addr = clients[target_username]
                                host_ip = host_addr[0] # IP của Host
                                
                                # Cập nhật trạng thái
                                lobby[target_username] = "in_game"
                                lobby[current_username] = "in_game"
                        
                        if host_conn:
                            print(f"[MATCH] Host({target_username}) vs Client({current_username})")
                            
                            # Gửi lệnh cho Host
                            send_json(host_conn, {
                                "type": "start_game",
                                "role": "host",
                                "port": P2P_PORT,
                                "opponent_username": current_username
                            })
                            
                            # Gửi lệnh cho Client (Mình)
                            send_json(client_conn, {
                                "type": "start_game",
                                "role": "client",
                                "opponent_ip": host_ip,
                                "port": P2P_PORT,
                                "opponent_username": target_username
                            })
                        else:
                            send_json(conn, {"type": "error", "message": "Đối thủ đã thoát"})

                except json.JSONDecodeError:
                    print(f"[ERROR] JSON lỗi từ {addr}: {message}")
                except Exception as e:
                    print(f"[ERROR] Logic lỗi: {e}")

    except Exception as e:
        print(f"[DISCONNECT] Lỗi kết nối {addr}: {e}")
    finally:
        # Dọn dẹp khi ngắt kết nối
        with lobby_lock:
            if current_username:
                if current_username in clients: del clients[current_username]
                if current_username in lobby: del lobby[current_username]
                print(f"[EXIT] {current_username} đã thoát.")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((HOST, PORT))
    except OSError:
        print(f"Lỗi: Cổng {PORT} đang bận. Hãy tắt server cũ hoặc đổi cổng.")
        return

    server.listen(5)
    print(f"[*] Server Mai Mối chạy tại {HOST}:{PORT}")
    print("-------------------------------------------------")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_server()