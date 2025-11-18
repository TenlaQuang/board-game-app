# network/network_manager.py (FIX LỖI TIMEOUT)
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
            
            # --- FIX 1: Đảm bảo socket Host không bị timeout ---
            conn.settimeout(None) 
            # ---------------------------------------------------

            if self.p2p_socket is None:
                self.p2p_socket = conn
                self.is_host = True
                self._start_p2p_listener()
            else:
                conn.close()
        except: pass

    # --- 2. WEB SERVER ---
    def create_room_on_server(self):
        if not self._listening_port: return None
        return web_matchmaking.create_room_online(self.username, self._listening_port)

    def join_room_on_server(self, rid):
        return web_matchmaking.join_room_online(self.username, rid)

    # --- 3. POLLING ---
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

    # --- 4. CLIENT CONNECT ---
    def connect_to_peer(self, ip, port):
        if self.p2p_socket: return True
        print(f"[NET] Đang kết nối tới {ip}:{port}...")

        def try_connect(target_ip, target_port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0) # Chỉ timeout lúc đang tìm
                sock.connect((target_ip, target_port))
                
                # --- FIX 2: KẾT NỐI XONG LÀ BỎ TIMEOUT NGAY ---
                sock.settimeout(None) 
                # ----------------------------------------------

                self.p2p_socket = sock
                self.is_host = False
                self._start_p2p_listener()
                return True
            except Exception as e:
                print(f"[NET] Kết nối {target_ip} thất bại: {e}")
                return False

        # 1. Thử IP Public
        if try_connect(ip, port):
            print("[NET] Kết nối Public IP thành công!")
            return True
        
        # 2. Thử Localhost (nếu cùng máy)
        print("[NET] Đang thử Localhost...")
        if try_connect('127.0.0.1', port):
            print("[NET] Kết nối Localhost thành công!")
            return True
            
        return False

    # --- 5. LISTENER ---
    def _start_p2p_listener(self):
        if not self.p2p_listener_thread or not self.p2p_listener_thread.is_alive():
            self.p2p_listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.p2p_listener_thread.start()

    def _listen_loop(self):
        try:
            while self.p2p_socket:
                # Bây giờ recv sẽ đợi mãi mãi cho đến khi có data, không bị ngắt sau 3s nữa
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

        # Trong network/network_manager.py

    def _poll_loop(self):
        while self._polling:
            if self._listening_port:
                web_matchmaking.send_heartbeat(self.username, self._listening_port)
            
            # 1. Lấy danh sách user
            users = web_matchmaking.get_online_users()
            
            # 2. (MỚI) Kiểm tra lời mời
            invite = web_matchmaking.check_invite_online(self.username)
            
            if self._poll_callback:
                try: 
                    # Truyền cả users và invite về cho UI
                    self._poll_callback(users, invite)
                except: pass
            time.sleep(3)