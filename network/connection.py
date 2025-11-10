# network/connection.py
import socket
import threading
import queue

class Connection:
    def __init__(self, sock: socket.socket, peer_name=""):
        self.sock = sock
        self.peer_name = peer_name
        self.incoming = queue.Queue()
        self.running = True

        threading.Thread(target=self._receive_loop, daemon=True).start()

    def _receive_loop(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                msg = data.decode('utf-8')
                self.incoming.put(msg)
            except Exception:
                break
        self.running = False

    def send(self, message: str):
        try:
            self.sock.sendall(message.encode('utf-8'))
        except Exception:
            self.running = False

    def get_message(self):
        """Lấy tin nhắn nếu có, không chặn luồng"""
        try:
            return self.incoming.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass
