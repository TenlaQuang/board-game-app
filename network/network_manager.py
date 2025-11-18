# network/network_manager.py
import socket
import threading
import queue
import json
import time
from typing import Optional, Tuple

# Import helper from package network (network/__init__.py)
# network.__init__ provides find_opponent(...) và start_responder_for_localhost(...)
try:
    from . import find_opponent as package_find_opponent
    from . import start_responder_for_localhost
except Exception:
    # Nếu không ở trong package (chạy trực tiếp), fallback: no-op
    package_find_opponent = None
    start_responder_for_localhost = None


class NetworkManager:
    def __init__(self):
        # queues để UI/logic đọc event từ server/p2p
        self.server_queue = queue.Queue()
        self.p2p_queue = queue.Queue()

        # sockets
        self.matchmaker_socket = None
        self.p2p_socket = None

        # listener threads
        self.matchmaker_listener_thread = None
        self.p2p_listener_thread = None

        # thông tin user / role
        self.username = None
        self.role = None

        # thread điều khiển connect_to_peer (để poll/tracking)
        self._connect_thread = None
        self._connect_thread_lock = threading.Lock()
        self._connect_result = None  # (True/False, message)

    # --- HÀM GỬI AN TOÀN (Thêm \n) ---
    def send_to_matchmaker(self, command_dict):
        if not self.matchmaker_socket:
            return
        try:
            data = json.dumps(command_dict) + "\n"
            self.matchmaker_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            print(f"[NetworkManager] Lỗi gửi lệnh server: {e}")

    def send_to_p2p(self, command_dict):
        if not self.p2p_socket:
            return
        try:
            data = json.dumps(command_dict) + "\n"
            self.p2p_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            print(f"[NetworkManager] Lỗi gửi lệnh P2P: {e}")

    # --- HÀM NHẬN AN TOÀN (Xử lý Buffer) ---
    def _receive_loop(self, sock: socket.socket, target_queue: queue.Queue, source_name: str):
        """Hàm dùng chung để lắng nghe socket với buffer."""
        buffer = ""
        try:
            while True:
                data = sock.recv(1024).decode('utf-8')
                if not data:
                    break

                buffer += data

                # Xử lý từng dòng lệnh trong buffer
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message.strip():  # Bỏ qua dòng trống
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
            # báo cho consumer biết socket đóng
            try:
                target_queue.put({"type": "disconnect"})
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass

    def _listen_to_matchmaker(self):
        if not self.matchmaker_socket:
            return
        self._receive_loop(self.matchmaker_socket, self.server_queue, "SERVER")

    def _listen_to_p2p(self):
        if not self.p2p_socket:
            return
        self._receive_loop(self.p2p_socket, self.p2p_queue, "P2P")

    # --- Logic Start Game tách ra cho gọn ---
    def _handle_start_game(self, command):
        """
        Server có thể push lệnh start_game:
        { "type":"start_game", "role":"host"/"client", "port":12345, "opponent_ip":"1.2.3.4", "opponent_username":"X" }
        """
        self.role = command.get('role')
        port = command.get('port')
        ip = command.get('opponent_ip')
        opponent_username = command.get('opponent_username', 'Opponent')

        threading.Thread(
            target=self._initiate_p2p_connection,
            args=(self.role, ip, port, opponent_username),
            daemon=True
        ).start()

    # --- P2P connection (host/client) ---
    def _initiate_p2p_connection(self, role: str, opponent_ip: Optional[str], port: int, opponent_username: str):
        """
        Internal: tạo socket host hoặc client tùy role.
        Khi thành công sẽ:
         - đặt self.p2p_socket
         - start listener thread self._listen_to_p2p
         - gửi handshake {"type":"handshake","from": username}
         - push {"type":"p2p_connected", "opponent_username": ...} vào server_queue
        """
        if role == 'host':
            try:
                host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                host_socket.bind(('0.0.0.0', port))
                host_socket.listen(1)
                # thông báo UI/logic rằng đang chờ kết nối
                self.server_queue.put({"type": "p2p_waiting"})
                conn, addr = host_socket.accept()
                self.p2p_socket = conn
                try:
                    host_socket.close()
                except Exception:
                    pass
            except Exception as e:
                self.server_queue.put({"type": "p2p_error", "message": str(e)})
                return
        else:  # client
            # thử nhiều lần - giữ logic cũ
            for _ in range(5):
                try:
                    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_sock.connect((opponent_ip, port))
                    self.p2p_socket = client_sock
                    break
                except Exception:
                    time.sleep(1)

            if not self.p2p_socket:
                self.server_queue.put({"type": "p2p_error", "message": "Không thể kết nối"})
                return

        # P2P OK -> Start listening
        try:
            self.p2p_listener_thread = threading.Thread(target=self._listen_to_p2p, daemon=True)
            self.p2p_listener_thread.start()
        except Exception as e:
            print("[NetworkManager] Không thể start p2p listener:", e)

        # Handshake (gửi tên)
        try:
            self.send_to_p2p({"type": "handshake", "from": self.username})
        except Exception:
            pass

        # Báo event cho UI/logic
        self.server_queue.put({"type": "p2p_connected", "opponent_username": opponent_username})

    # --- Giữ nguyên logic connect matchmaker ban đầu (server TCP của bạn) ---
    def connect_to_matchmaker(self, host_ip: str, port: int, username: str) -> bool:
        """
        Kết nối TCP tới server matchmaking (your old server).
        Sau khi đăng ký thành công (register_ok) sẽ start listener đọc lệnh server.
        """
        try:
            self.matchmaker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.matchmaker_socket.connect((host_ip, port))
            self.username = username

            register_cmd = json.dumps({"type": "register", "username": self.username}) + "\n"
            self.matchmaker_socket.sendall(register_cmd.encode('utf-8'))

            # nhận phản hồi ban đầu (blocking, 1 lần)
            raw = self.matchmaker_socket.recv(4096).decode('utf-8')
            # server có thể gửi nhiều JSON kèm \n, lấy phần đầu
            if "\n" in raw:
                raw = raw.split("\n", 1)[0]
            response = json.loads(raw)

            if response.get('type') == 'register_ok':
                self.matchmaker_listener_thread = threading.Thread(target=self._listen_to_matchmaker, daemon=True)
                self.matchmaker_listener_thread.start()
                return True
            else:
                return False
        except Exception as e:
            print(f"[NetworkManager] Connect Error: {e}")
            return False

    # -----------------------
    # NEW API - functions that UI (window.py) expects
    # -----------------------
    def find_opponent(self, username: str,
                      lan_timeout: float = 2.0,
                      web_timeout: float = 60.0,
                      web_poll_interval: float = 1.0) -> Optional[Tuple[str, Optional[int]]]:
        """
        Wrapper: cố gắng tìm opponent bằng LAN trước, nếu không -> gọi web matchmaking (package_find_opponent).
        Trả về (ip, port) hoặc None.
        """
        # Lưu username
        self.username = username

        # 1) Thử package find_opponent (đã implement trong network/__init__.py)
        try:
            if package_find_opponent:
                res = package_find_opponent(username=username, p2p_port=None,
                                            lan_timeout=lan_timeout,
                                            web_timeout=web_timeout,
                                            web_poll_interval=web_poll_interval)
                if res:
                    return res
        except Exception as e:
            print("[NetworkManager] package_find_opponent error:", e)

        # 2) Nếu không có package finder, fallback simple: return None
        return None

    def connect_to_peer(self, ip: str, port: int, timeout: float = 10.0) -> bool:
        """
        API được UI gọi để kết nối tới opponent (client side).
        - Tạo 1 thread chạy _initiate_p2p_connection(role='client', ...)
        - Poll tới timeout để kiểm tra kết quả.
        Trả về True nếu kết nối thành công, False nếu timeout hoặc lỗi.
        """
        with self._connect_thread_lock:
            # reset result
            self._connect_result = None

            # start background connect (so UI thread not blocked)
            t = threading.Thread(target=self._initiate_p2p_connection,
                                 args=('client', ip, port, 'Opponent'),
                                 daemon=True)
            t.start()
            self._connect_thread = t

        # Poll for result: check p2p_socket or server_queue error events
        start = time.time()
        while time.time() - start < timeout:
            # nếu socket đã set -> success
            if self.p2p_socket:
                self._connect_result = (True, "connected")
                return True

            # kiểm tra server_queue có p2p_error
            try:
                while not self.server_queue.empty():
                    ev = self.server_queue.get_nowait()
                    # nếu có event p2p_error -> lỗi
                    if ev.get('type') == 'p2p_error':
                        self._connect_result = (False, ev.get('message'))
                        return False
                    # if p2p_connected event -> success
                    if ev.get('type') == 'p2p_connected':
                        self._connect_result = (True, "connected")
                        return True
                    # else: bỏ qua
            except queue.Empty:
                pass

            time.sleep(0.1)

        # timeout
        self._connect_result = (False, "timeout")
        return False

    # Cho phép start responder trong LAN (nếu muốn bị tìm thấy)
    def start_responder(self, username: str, p2p_port: int):
        if start_responder_for_localhost:
            try:
                start_responder_for_localhost(username, p2p_port)
            except Exception as e:
                print("[NetworkManager] start_responder failed:", e)
        else:
            print("[NetworkManager] start_responder not available (package function missing)")

    # -----------------------
    # Cleanup
    # -----------------------
    def shutdown(self):
        try:
            if self.matchmaker_socket:
                try:
                    self.matchmaker_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.matchmaker_socket.close()
        except Exception:
            pass
        try:
            if self.p2p_socket:
                try:
                    self.p2p_socket.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.p2p_socket.close()
        except Exception:
            pass

        # join threads gracefully (non-blocking)
        try:
            if self.matchmaker_listener_thread and self.matchmaker_listener_thread.is_alive():
                # socket closed -> listener should exit
                pass
        except Exception:
            pass

        try:
            if self.p2p_listener_thread and self.p2p_listener_thread.is_alive():
                pass
        except Exception:
            pass
