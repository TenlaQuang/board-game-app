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
        self.current_lobby_state = "menu"
        
        # Lấy IP Radmin
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
            return self._listening_port
        except Exception as e:
            print(f"[NET] Lỗi host: {e}")
            return 0

    def _accept_incoming(self):
        if not self._listen_socket: return
        try:
            while self._listen_socket: # [FIX] Vòng lặp để chấp nhận kết nối lại sau khi ngắt
                conn, addr = self._listen_socket.accept()
                conn.settimeout(None) 
                if self.p2p_socket is None:
                    print(f"[NET] Chấp nhận kết nối từ {addr}")
                    self.p2p_socket = conn
                    self.is_host = True
                    self._start_p2p_listener()
                else:
                    conn.close()
        except: pass

    # --- 2. WEB SERVER ---
    def create_room_on_server(self):
        if not self._listening_port: return None
        # Chỉ tạo nếu chưa có socket P2P
        return web_matchmaking.create_room_online(self.username, self._listening_port, self.current_lobby_state)

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
            try:
                if self._listening_port:
                    web_matchmaking.send_heartbeat(
                        self.username, 
                        self._listening_port, 
                        self.current_lobby_state
                    )
                
                users = web_matchmaking.get_online_users()
                invite = web_matchmaking.check_invite_online(self.username)
                
                if self._poll_callback:
                    self._poll_callback(users, invite)
            except Exception as e:
                time.sleep(3) 
            time.sleep(1.5)

    # --- 4. CLIENT CONNECT ---
    def connect_to_peer(self, ip, port):
        # [FIX] Nếu đang có kết nối cũ thì đóng trước
        if self.p2p_socket: 
            self.reset_connection()
        
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
            except: return False

        if self.local_radmin_ip and try_connect(ip, port, "RADMIN/LAN"): return True
        if not self.local_radmin_ip and try_connect(ip, port, "PUBLIC IP"): return True
        if try_connect('127.0.0.1', port, "LOCALHOST"): return True

        print(f"[NET] Kết nối thất bại hoàn toàn.")
        return False

    # --- 5. LISTENER ---
    def _start_p2p_listener(self):
        if self.p2p_listener_thread and self.p2p_listener_thread.is_alive():
            return # Đã có thread chạy thì thôi
            
        self.p2p_listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.p2p_listener_thread.start()

    def _listen_loop(self):
        try:
            while self.p2p_socket:
                try:
                    data = self.p2p_socket.recv(1024).decode('utf-8')
                    if not data: 
                        print("[NET] Đối thủ đã ngắt kết nối.")
                        break
                    
                    buffer = data
                    # Xử lý dính gói tin (TCP stream)
                    for line in buffer.split("\n"):
                        if line.strip():
                            try: self.p2p_queue.put(json.loads(line))
                            except: pass
                except OSError:
                    break # Socket bị đóng thủ công
        except Exception as e:
            print(f"[NET] Lỗi listener: {e}")
        finally: 
            self.reset_connection() # Đảm bảo dọn dẹp khi vòng lặp dừng

    def send_to_p2p(self, data):
        if self.p2p_socket:
            try: self.p2p_socket.sendall((json.dumps(data)+"\n").encode('utf-8'))
            except: pass

    def send_chat(self, message):
        self.send_to_p2p({"type": "chat", "content": message})

    def send_command(self, command):
        self.send_to_p2p({"type": "command", "content": command})

    # --- [MỚI] HÀM QUAN TRỌNG ĐỂ SỬA LỖI ---
    def reset_connection(self):
        """Ngắt toàn bộ kết nối: P2P và cả Cổng Lắng Nghe (Host)"""
        print("[NET] Đang dọn dẹp kết nối mạng...")
        
        # 1. Ngắt kết nối với đối thủ (P2P)
        if self.p2p_socket:
            try:
                self.p2p_socket.shutdown(socket.SHUT_RDWR)
                self.p2p_socket.close()
            except: pass
        self.p2p_socket = None
        
        # 2. [QUAN TRỌNG] Đóng cổng lắng nghe (Host) để không ai vào được nữa
        if self._listen_socket:
            try:
                self._listen_socket.close()
            except: pass
            self._listen_socket = None
            self._listening_port = None # Xóa port để lần sau tạo mới
            
        self.is_host = False
        
        # 3. Xóa tin nhắn tồn đọng
        with self.p2p_queue.mutex:
            self.p2p_queue.queue.clear()
            
        print("[NET] Đã đóng hoàn toàn kết nối & cổng Host.")

    def shutdown(self):
        self._polling = False
        self.reset_connection()
        try: 
            if self._listen_socket: self._listen_socket.close()
        except: pass
        # [THÊM VÀO CUỐI CLASS NetworkManager]
    def force_update(self):
        """Gửi heartbeat và lấy danh sách user NGAY LẬP TỨC (không đợi 3s)"""
        def _task():
            # 1. Báo cáo ngay vị trí hiện tại lên Server
            if self._listening_port:
                web_matchmaking.send_heartbeat(
                    self.username, 
                    self._listening_port, 
                    self.current_lobby_state
                )
            
            # 2. Lấy danh sách user mới nhất về ngay
            users = web_matchmaking.get_online_users()
            invite = web_matchmaking.check_invite_online(self.username)
            
            # 3. Cập nhật UI ngay lập tức
            if self._poll_callback:
                self._poll_callback(users, invite)
                
        threading.Thread(target=_task, daemon=True).start()