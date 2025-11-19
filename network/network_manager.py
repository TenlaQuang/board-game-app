# network/network_manager.py (FIXED P2P LOGIC)
import socket
import threading
import queue
import json
import time

try:
    from . import web_matchmaking
except ImportError:
    import web_matchmaking 

class NetworkManager:
    def __init__(self):
        self.p2p_queue = queue.Queue()
        self.p2p_socket = None
        self.p2p_listener_thread = None
        self._listen_socket = None
        self._listening_port = None
        self.username = "Player_" + str(int(time.time()) % 1000)
        self._polling = False
        self._poll_callback = None
        self.is_host = False 
        
        # Biến mới để lưu trữ IP Radmin/LAN của chính máy này
        self.local_radmin_ip = web_matchmaking.get_radmin_ip() 

    # --- 1. HOSTING ---
    def start_hosting_phase(self) -> int:
        if self._listen_socket: return self._listening_port
        try:
            self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._listen_socket.bind(('0.0.0.0', 0)) 
            self._listening_port = self._listen_socket.getsockname()[1]
            self._listen_socket.listen(1)
            threading.Thread(target=self._accept_incoming, daemon=True).start()
            print(f"[NET] Hosting tại port: {self._listening_port}")
            return self._listening_port
        except Exception as e:
            print(f"[NET] Lỗi host: {e}")
            return 0

    def _accept_incoming(self):
        if not self._listen_socket: return
        try:
            conn, addr = self._listen_socket.accept()
            print(f"[NET] Có kết nối đến từ {addr}")
            
            # Đảm bảo socket Host không bị timeout
            conn.settimeout(None) 

            if self.p2p_socket is None:
                self.p2p_socket = conn
                self.is_host = True
                self._start_p2p_listener()
            else:
                conn.close()
        except: pass

    # --- 2. WEB SERVER ---
    # Cần sửa lại hàm này để gửi IP Radmin lên server (sử dụng logic trong web_matchmaking.py)
    def create_room_on_server(self):
        if not self._listening_port: return None
        # web_matchmaking.create_room_online sẽ tự gọi get_radmin_ip() và gửi lên server.
        return web_matchmaking.create_room_online(self.username, self._listening_port, self.local_radmin_ip)

    def join_room_on_server(self, rid):
        return web_matchmaking.join_room_online(self.username, rid)

    # --- 3. POLLING (GIỮ NGUYÊN) ---
    def start_polling_users(self, callback):
        self._polling = True
        self._poll_callback = callback
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def stop_polling_users(self):
        self._polling = False

    def _poll_loop(self):
        while self._polling:
            if self._listening_port:
                web_matchmaking.send_heartbeat(self.username, self._listening_port)
            users = web_matchmaking.get_online_users()
            if self._poll_callback:
                try: self._poll_callback(users)
                except: pass
            time.sleep(3)

    # --- 4. CLIENT CONNECT (ĐÃ SỬA CHUỖI THỬ NGHIỆM IP) ---
    def connect_to_peer(self, ip, port):
        if self.p2p_socket: return True
        print(f"[NET] Đang kết nối tới {ip}:{port}...")

        # Hàm con để thử kết nối
        def try_connect(target_ip, target_port, label):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0) 
                sock.connect((target_ip, target_port))
                
                sock.settimeout(None) 
                
                self.p2p_socket = sock
                self.is_host = False
                self._start_p2p_listener()
                print(f"[NET] Kết nối {label} thành công!")
                return True
            except Exception as e:
                print(f"[NET] Kết nối {label} thất bại.")
                return False

        # 1. Thử IP Radmin/LAN (IP ưu tiên mà Server trả về)
        if self.local_radmin_ip:
            # Nếu ta có IP Radmin, ta ưu tiên thử kết nối qua nó vì Radmin/LAN luôn là ưu tiên hàng đầu.
            # Ta giả định IP trả về là IP Radmin của đối thủ.
            if try_connect(ip, port, "RADMIN/LAN"):
                return True
        
        # 2. Thử lại với IP công cộng (Nếu không có Radmin, thử Public IP)
        # Nếu IP trả về không phải Radmin (bị None), ta thử lại với IP đó (Public IP).
        if not self.local_radmin_ip:
            if try_connect(ip, port, "PUBLIC IP"):
                return True

        # 3. Thử Localhost (Chỉ dành cho test trên 1 máy, không liên quan đến Radmin)
        # Giữ lại để bạn test local nếu muốn, nhưng không nên là ưu tiên chính.
        if try_connect('127.0.0.1', port, "LOCALHOST"):
            return True

        print(f"[NET] Kết nối thất bại hoàn toàn. (Kiểm tra kết nối Radmin/Firewall)")
        return False

    # --- 5. LISTENER (GIỮ NGUYÊN) ---
    def _start_p2p_listener(self):
        if not self.p2p_listener_thread or not self.p2p_listener_thread.is_alive():
            self.p2p_listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.p2p_listener_thread.start()

    def _listen_loop(self):
        try:
            while self.p2p_socket:
                data = self.p2p_socket.recv(1024).decode('utf-8')
                if not data: break
                buffer = data
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    if msg.strip():
                        try: self.p2p_queue.put(json.loads(msg))
                        except: pass
        except Exception as e: 
            print(f"[NET] Lỗi Listener: {e}")
        finally: 
            print("[NET] Socket đóng.")
            self.p2p_socket = None

    def send_to_p2p(self, data):
        if self.p2p_socket:
            try: self.p2p_socket.sendall((json.dumps(data)+"\n").encode('utf-8'))
            except: pass

    def shutdown(self):
        self._polling = False
        try: 
            if self._listen_socket: self._listen_socket.close()
            if self.p2p_socket: self.p2p_socket.close()
        except: pass