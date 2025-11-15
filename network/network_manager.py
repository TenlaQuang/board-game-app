# Tên file: network/network_manager.py (Đặt trong dự án của bạn)
import socket
import threading
import queue
import json
import time

class NetworkManager:
    def __init__(self):
        # Queues để giao tiếp với luồng game chính (ui/window.py)
        self.server_queue = queue.Queue() # Lệnh từ server "mai mối" (VD: có người mời)
        self.p2p_queue = queue.Queue()    # Lệnh từ đối thủ (VD: nước đi)
        
        self.matchmaker_socket = None
        self.p2p_socket = None
        
        self.matchmaker_listener_thread = None
        self.p2p_listener_thread = None
        
        self.username = None
        self.role = None # "host" or "client"

    # --- Các hàm xử lý luồng (chạy nền) ---

    def _listen_to_matchmaker(self):
        """Lắng nghe server 'mai mối' trên 1 luồng riêng."""
        try:
            while self.matchmaker_socket:
                data = self.matchmaker_socket.recv(1024).decode('utf-8')
                if not data: break
                try:
                    command = json.loads(data)
                    print(f"[SERVER] Nhận lệnh: {command}")
                    
                    if command.get('type') == 'start_game':
                        # Lệnh đặc biệt: Server bảo bắt đầu P2P
                        # Tự động hóa việc này trong 1 luồng mới để không block
                        self.role = command.get('role')
                        port = command.get('port')
                        ip = command.get('opponent_ip') # Sẽ là None cho Host
                        # Lấy tên đối thủ
                        opponent_username = command.get('opponent_username', 'Opponent')
                        
                        p2p_thread = threading.Thread(
                            target=self._initiate_p2p_connection, 
                            args=(self.role, ip, port, opponent_username), 
                            daemon=True
                        )
                        p2p_thread.start()
                    
                    self.server_queue.put(command) # Đẩy lệnh (VD: 'invited') vào queue
                        
                except json.JSONDecodeError:
                    print(f"[SERVER-ERROR] Dữ liệu JSON lỗi: {data}")
        except Exception:
            print("[SERVER] Mất kết nối server mai mối.")
        finally:
            self.server_queue.put({"type": "disconnect"})
            if self.matchmaker_socket:
                self.matchmaker_socket.close()

    def _listen_to_p2p(self):
        """Lắng nghe đối thủ (P2P) trên 1 luồng riêng."""
        try:
            while self.p2p_socket:
                data = self.p2p_socket.recv(1024).decode('utf-8')
                if not data: break
                try:
                    command = json.loads(data)
                    print(f"[P2P] Nhận lệnh: {command}")
                    self.p2p_queue.put(command) # Đẩy lệnh (VD: 'move') vào queue
                except json.JSONDecodeError:
                    print(f"[P2P-ERROR] Dữ liệu JSON lỗi: {data}")
        except Exception:
            print("[P2P] Đối thủ ngắt kết nối.")
        finally:
            self.p2p_queue.put({"type": "disconnect"})
            if self.p2p_socket:
                self.p2p_socket.close()

    def _initiate_p2p_connection(self, role, opponent_ip, port, opponent_username):
        """(Chạy trên luồng riêng) Thử kết nối P2P."""
        if role == 'host':
            try:
                host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host_socket.bind(('0.0.0.0', port))
                host_socket.listen(1)
                print(f"[P2P-HOST] Đang lắng nghe trên cổng {port}...")
                self.server_queue.put({"type": "p2p_waiting"}) # Báo UI "đang chờ"
                
                conn, addr = host_socket.accept() # Chặn (blocking)
                
                print(f"[P2P-HOST] Đối thủ {addr} đã kết nối!")
                self.p2p_socket = conn
                host_socket.close()
            except Exception as e:
                print(f"Lỗi P2P Host: {e}")
                self.server_queue.put({"type": "p2p_error", "message": str(e)})
                return
        
        else: # role == 'client'
            print(f"[P2P-CLIENT] Đang kết nối đến {opponent_ip}:{port}...")
            # Thử kết nối vài lần, vì Host có thể chưa 'listen' kịp
            for _ in range(5):
                try:
                    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_sock.connect((opponent_ip, port))
                    print("[P2P-CLIENT] Kết nối P2P thành công!")
                    self.p2p_socket = client_sock
                    break
                except Exception:
                    time.sleep(1) # Chờ 1s rồi thử lại
            
            if not self.p2p_socket:
                print("[P2P-CLIENT] Không thể kết nối P2P.")
                self.server_queue.put({"type": "p2p_error", "message": "Không thể kết nối đối thủ"})
                return

        # P2P Thành công!
        print("[P2P] Kết nối thành lập. Bắt đầu luồng nghe P2P.")
        self.p2p_listener_thread = threading.Thread(target=self._listen_to_p2p, daemon=True)
        self.p2p_listener_thread.start()
        
        # Gửi lời chào để xác nhận
        self.send_to_p2p({"type": "handshake", "from": self.username})
        # Báo UI là game sẵn sàng
        self.server_queue.put({"type": "p2p_connected", "opponent_username": opponent_username})

    # --- Các hàm public (gọi từ UI / main.py) ---

    def connect_to_matchmaker(self, host_ip, port, username):
        """Kết nối đến server 'mai mối' (gọi 1 lần)."""
        try:
            self.matchmaker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.matchmaker_socket.connect((host_ip, port))
            
            self.username = username
            # Đăng ký tên
            register_cmd = json.dumps({"type": "register", "username": self.username})
            self.matchmaker_socket.sendall(register_cmd.encode('utf-8'))
            
            response = json.loads(self.matchmaker_socket.recv(1024).decode('utf-8'))
            
            if response.get('type') == 'register_ok':
                # Bắt đầu luồng lắng nghe server
                self.matchmaker_listener_thread = threading.Thread(target=self._listen_to_matchmaker, daemon=True)
                self.matchmaker_listener_thread.start()
                return True
            else:
                print(f"Lỗi đăng ký: {response.get('message')}")
                return False
        except Exception as e:
            print(f"Không thể kết nối server mai mối: {e}")
            return False

    def send_to_matchmaker(self, command_dict):
        """Gửi lệnh cho server 'mai mối' (VD: mời chơi)."""
        if not self.matchmaker_socket: return
        try:
            self.matchmaker_socket.sendall(json.dumps(command_dict).encode('utf-8'))
        except Exception as e:
            print(f"Lỗi gửi lệnh server: {e}")

    def send_to_p2p(self, command_dict):
        """Gửi lệnh P2P cho đối thủ (VD: nước đi)."""
        if not self.p2p_socket: return
        try:
            self.p2p_socket.sendall(json.dumps(command_dict).encode('utf-8'))
        except Exception as e:
            print(f"Lỗi gửi lệnh P2P: {e}")

    def shutdown(self):
        if self.matchmaker_socket: self.matchmaker_socket.close()
        if self.p2p_socket: self.p2p_socket.close() 