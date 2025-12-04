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
        
        # Socket kết nối với đối thủ (P2P)
        self.p2p_socket = None
        self.p2p_listener_thread = None
        
        # Socket để lắng nghe (Khi làm Host)
        self._listen_socket = None
        self._listening_port = None
        
        self.username = "Player_" + str(int(time.time()) % 1000)
        
        # [SỬA LẠI] Quản lý Polling bằng Event thay vì biến bool đơn thuần
        self._poll_stop_event = threading.Event()
        self._poll_thread = None
        self._poll_callback = None
        
        self.is_host = False 
        self.current_lobby_state = "menu"
        self.local_radmin_ip = web_matchmaking.get_radmin_ip() 

    # =====================================================
    # 1. HOSTING (TẠO PHÒNG)
    # =====================================================
    def start_hosting_phase(self) -> int:
        """Mở cổng để chờ người khác kết nối vào"""
        self.reset_connection() 

        try:
            self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind vào cổng ngẫu nhiên (Port 0)
            self._listen_socket.bind(('0.0.0.0', 0)) 
            self._listening_port = self._listen_socket.getsockname()[1]
            self._listen_socket.listen(1)
            
            print(f"[NET] Đang Host tại Port: {self._listening_port}")
            threading.Thread(target=self._accept_incoming, daemon=True).start()
            
            return self._listening_port
        except Exception as e:
            print(f"[NET] Lỗi host: {e}")
            self.reset_connection()
            return 0

    def _accept_incoming(self):
        """Luồng chờ kết nối"""
        print("[NET] Host đang chờ người chơi...")
        while self._listen_socket:
            try:
                conn, addr = self._listen_socket.accept()
                print(f"[NET] Có kết nối từ {addr}")
                
                if self.p2p_socket is not None:
                    conn.close(); continue
                
                conn.settimeout(None) 
                self.p2p_socket = conn
                self.is_host = True # Xác nhận mình là chủ
                self._start_p2p_listener()
            except OSError:
                break
            except Exception as e:
                print(f"[NET] Lỗi accept: {e}")
                break

    # =====================================================
    # 2. CLIENT CONNECT
    # =====================================================
    def connect_to_peer(self, ip, port):
        """Kết nối tới Host"""
        self.reset_connection() # Reset sạch trước khi connect
        
        def try_connect(target_ip, target_port):
            if not target_ip: return False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.connect((target_ip, target_port))
                sock.settimeout(None)
                
                self.p2p_socket = sock
                self.is_host = False # Xác nhận mình là khách
                self._start_p2p_listener()
                return True
            except: return False

        # Thử các loại IP
        if self.local_radmin_ip and try_connect(ip, port): return True
        if try_connect(ip, port): return True
        if try_connect('127.0.0.1', port): return True

        return False

    # =====================================================
    # 3. COMMUNICATION
    # =====================================================
    def _start_p2p_listener(self):
        if self.p2p_listener_thread and self.p2p_listener_thread.is_alive(): return
        self.p2p_listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.p2p_listener_thread.start()

    def _listen_loop(self):
        # Bộ đệm phải nằm ngoài vòng lặp while để tích trữ dữ liệu
        buffer = ""
        
        print("[NET] Đang lắng nghe dữ liệu P2P...")
        
        try:
            while self.p2p_socket:
                try:
                    # 1. Tăng lên 1MB (1024 * 1024) để nuốt trọn gói tin Voice
                    chunk = self.p2p_socket.recv(1048576).decode('utf-8')
                    
                    if not chunk: 
                        print("[NET] Đối thủ đã ngắt kết nối.")
                        break
                    
                    # 2. [QUAN TRỌNG] Cộng dồn dữ liệu mới vào dữ liệu cũ
                    buffer += chunk
                    
                    # 3. Xử lý tách tin nhắn (Dựa vào ký tự xuống dòng \n)
                    # Chỉ xử lý khi tìm thấy dấu xuống dòng (tức là đã trọn vẹn 1 tin nhắn)
                    while "\n" in buffer:
                        # Tách: [Tin nhắn hoàn chỉnh] \n [Phần thừa còn lại...]
                        message, buffer = buffer.split("\n", 1)
                        
                        if message.strip():
                            try:
                                data_json = json.loads(message)
                                
                                # Debug chơi cho vui để biết voice đã tới
                                if data_json.get("type") == "chat" and "[VOICE" in data_json.get("content", ""):
                                    print(f"[NET] >>> ĐÃ NHẬN VOICE! Kích thước: {len(message)} bytes")
                                    
                                self.p2p_queue.put(data_json)
                            except json.JSONDecodeError:
                                # Nếu JSON lỗi, có thể do chưa nhận đủ, kệ nó chờ vòng lặp sau
                                print(f"[NET] Đang chờ gom đủ gói tin... (Buffer: {len(buffer)})")
                                pass
                                
                except OSError:
                    break 
                except Exception as e:
                    print(f"[NET] Lỗi nhận dữ liệu: {e}")
                    break
                    
        except Exception as e:
            print(f"[NET] Lỗi listener: {e}")
        finally: 
            self.reset_connection()

    def send_to_p2p(self, data):
        if self.p2p_socket:
            try: 
                msg = json.dumps(data) + "\n"
                self.p2p_socket.sendall(msg.encode('utf-8'))
            except: self.reset_connection()

    def send_chat(self, message): self.send_to_p2p({"type": "chat", "content": message})
    def send_command(self, command): self.send_to_p2p({"type": "command", "content": command})

    # =====================================================
    # 4. RESET (SỬA LỖI KẸT PORT)
    # =====================================================
    # [TRONG CLASS NETWORKMANAGER]

    def reset_connection(self):
        """Ngắt TOÀN BỘ kết nối (Dành cho cả Host và Guest)"""
        print("[NET] --- RESET CONNECTION ---")
        
        # 1. Reset trạng thái Web Server về menu (QUAN TRỌNG)
        self.current_lobby_state = "menu"  # <--- THÊM DÒNG NÀY
        
        # 2. Gán cờ Host = False
        self.is_host = False
        
        # 3. Ngắt kết nối P2P
        self._close_socket_only()
        # 3. Ngắt cổng Host (Server Socket)
        sock = self._listen_socket
        self._listen_socket = None 
        self._listening_port = None
        
        if sock:
            try:
                # Host cũng cần shutdown để ngắt accept()
                sock.shutdown(socket.SHUT_RDWR) 
            except: pass
            try:
                sock.close()
            except: pass
            
        # 4. Xóa hàng đợi tin nhắn
        with self.p2p_queue.mutex:
            self.p2p_queue.queue.clear()
            
        print("[NET] Đã dọn dẹp sạch sẽ.")

    def _close_socket_only(self):
        """Hàm phụ: Chỉ đóng socket P2P (Socket giao tiếp)"""
        if self.p2p_socket:
            print("[NET] Đang cưỡng chế đóng Socket P2P...")
            try:
                # [CỰC KỲ QUAN TRỌNG]
                # Guest đang bị kẹt ở recv(). Shutdown sẽ bắn lỗi vào recv() để nó thoát ra.
                self.p2p_socket.shutdown(socket.SHUT_RDWR)
            except Exception as e: 
                # Thường sẽ lỗi nếu socket đã chết từ trước, cứ kệ nó
                pass
            
            try:
                self.p2p_socket.close()
            except: pass
            
        self.p2p_socket = None

    # =====================================================
    # 5. POLLING SERVER (SỬA LỖI ZOMBIE THREAD)
    # =====================================================
    def start_polling_users(self, callback):
        # Nếu đang chạy rồi thì thôi, chỉ cập nhật callback
        if self._poll_thread and self._poll_thread.is_alive() and not self._poll_stop_event.is_set():
            self._poll_callback = callback
            return

        # Dừng thread cũ cho chắc ăn
        self.stop_polling_users()
        
        # Khởi tạo thread mới
        self._poll_stop_event.clear() # Xóa cờ dừng
        self._poll_callback = callback
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_polling_users(self):
        """Dừng polling và CHỜ cho đến khi nó dừng hẳn"""
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_stop_event.set() # Dựng cờ báo dừng
            # Chờ tối đa 0.2s cho thread cũ chết, không chờ lâu tránh đơ UI
            self._poll_thread.join(timeout=0.2) 

    def _poll_loop(self):
        print("[NET] Polling loop START.")
        while not self._poll_stop_event.is_set(): # Kiểm tra cờ liên tục
            try:
                if self._listening_port:
                    web_matchmaking.send_heartbeat(self.username, self._listening_port, self.current_lobby_state)
                
                users = web_matchmaking.get_online_users()
                invite = web_matchmaking.check_invite_online(self.username)
                
                if self._poll_callback:
                    self._poll_callback(users, invite)
            except: pass
            
            # Ngủ thông minh: Ngủ 1.5s nhưng nếu có lệnh dừng thì dậy ngay
            # wait(1.5) trả về True nếu cờ được dựng, False nếu hết giờ
            if self._poll_stop_event.wait(1.5):
                break # Nếu cờ dựng lên thì thoát vòng lặp ngay

        print("[NET] Polling loop END.")

    def force_update(self):
        threading.Thread(target=self._run_force_update, daemon=True).start()

    def _run_force_update(self):
        try:
            users = web_matchmaking.get_online_users()
            invite = web_matchmaking.check_invite_online(self.username)
            if self._poll_callback: self._poll_callback(users, invite)
        except: pass

    def shutdown(self):
        self._polling = False
        self.reset_connection()
        try: 
            if self._listen_socket: self._listen_socket.close()
        except: pass