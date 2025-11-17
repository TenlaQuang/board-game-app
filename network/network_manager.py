import socket
import threading
import queue
import json
import time

class NetworkManager:
    def __init__(self):
        self.server_queue = queue.Queue()
        self.p2p_queue = queue.Queue()
        
        self.matchmaker_socket = None
        self.p2p_socket = None
        
        self.matchmaker_listener_thread = None
        self.p2p_listener_thread = None
        
        self.username = None
        self.role = None 

    # --- HÀM GỬI AN TOÀN (Thêm \n) ---
    def send_to_matchmaker(self, command_dict):
        if not self.matchmaker_socket: return
        try:
            # QUAN TRỌNG: Thêm \n vào cuối để đánh dấu hết tin nhắn
            data = json.dumps(command_dict) + "\n"
            self.matchmaker_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            print(f"Lỗi gửi lệnh server: {e}")

    def send_to_p2p(self, command_dict):
        if not self.p2p_socket: return
        try:
            data = json.dumps(command_dict) + "\n"
            self.p2p_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            print(f"Lỗi gửi lệnh P2P: {e}")

    # --- HÀM NHẬN AN TOÀN (Xử lý Buffer) ---
    def _receive_loop(self, sock, target_queue, source_name):
        """Hàm dùng chung để lắng nghe socket với buffer."""
        buffer = ""
        try:
            while True:
                data = sock.recv(1024).decode('utf-8')
                if not data: break
                
                buffer += data
                
                # Xử lý từng dòng lệnh trong buffer
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message.strip(): # Bỏ qua dòng trống
                        try:
                            command = json.loads(message)
                            print(f"[{source_name}] Nhận: {command}")
                            
                            # Logic đặc biệt cho Server (Start Game)
                            if source_name == "SERVER" and command.get('type') == 'start_game':
                                self._handle_start_game(command)
                            
                            target_queue.put(command)
                            
                        except json.JSONDecodeError:
                            print(f"[{source_name}] Lỗi JSON: {message}")
        except Exception as e:
            print(f"[{source_name}] Mất kết nối: {e}")
        finally:
            target_queue.put({"type": "disconnect"})
            if sock: sock.close()

    def _listen_to_matchmaker(self):
        self._receive_loop(self.matchmaker_socket, self.server_queue, "SERVER")

    def _listen_to_p2p(self):
        self._receive_loop(self.p2p_socket, self.p2p_queue, "P2P")

    # --- Logic Start Game tách ra cho gọn ---
    def _handle_start_game(self, command):
        self.role = command.get('role')
        port = command.get('port')
        ip = command.get('opponent_ip')
        opponent_username = command.get('opponent_username', 'Opponent')
        
        threading.Thread(
            target=self._initiate_p2p_connection, 
            args=(self.role, ip, port, opponent_username), 
            daemon=True
        ).start()

    # --- Giữ nguyên logic P2P connection cũ của bạn, nó đã ổn ---
    def _initiate_p2p_connection(self, role, opponent_ip, port, opponent_username):
        # (Giữ nguyên code cũ của bạn ở đoạn này, chỉ lưu ý logic handshake)
        if role == 'host':
            try:
                host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host_socket.bind(('0.0.0.0', port))
                host_socket.listen(1)
                self.server_queue.put({"type": "p2p_waiting"})
                conn, addr = host_socket.accept()
                self.p2p_socket = conn
                host_socket.close()
            except Exception as e:
                self.server_queue.put({"type": "p2p_error", "message": str(e)})
                return
        else: # Client
            for _ in range(5):
                try:
                    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_sock.connect((opponent_ip, port))
                    self.p2p_socket = client_sock
                    break
                except:
                    time.sleep(1)
            
            if not self.p2p_socket:
                self.server_queue.put({"type": "p2p_error", "message": "Không thể kết nối"})
                return

        # P2P OK -> Start listening
        self.p2p_listener_thread = threading.Thread(target=self._listen_to_p2p, daemon=True)
        self.p2p_listener_thread.start()
        
        # Handshake
        self.send_to_p2p({"type": "handshake", "from": self.username})
        self.server_queue.put({"type": "p2p_connected", "opponent_username": opponent_username})

    # --- Giữ nguyên logic connect server ban đầu ---
    def connect_to_matchmaker(self, host_ip, port, username):
        try:
            self.matchmaker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.matchmaker_socket.connect((host_ip, port))
            self.username = username
            
            # Gửi đăng ký (nhớ thêm \n nếu server hỗ trợ, hoặc giữ nguyên nếu server cũ chưa sửa)
            # Tốt nhất là sửa cả Server để dùng \n
            register_cmd = json.dumps({"type": "register", "username": self.username}) + "\n" 
            self.matchmaker_socket.sendall(register_cmd.encode('utf-8'))
            
            # Đoạn nhận phản hồi ban đầu này cũng nên cẩn thận, 
            # nhưng vì nó ngắn và chạy 1 lần nên tạm thời recv(1024) cũng được
            response = json.loads(self.matchmaker_socket.recv(1024).decode('utf-8'))
            
            if response.get('type') == 'register_ok':
                self.matchmaker_listener_thread = threading.Thread(target=self._listen_to_matchmaker, daemon=True)
                self.matchmaker_listener_thread.start()
                return True
            else:
                return False
        except Exception as e:
            print(f"Connect Error: {e}")
            return False

    def shutdown(self):
        if self.matchmaker_socket: self.matchmaker_socket.close()
        if self.p2p_socket: self.p2p_socket.close()