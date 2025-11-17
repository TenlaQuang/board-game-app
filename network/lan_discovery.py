# network/lan_discovery.py
# Hàm dò LAN và responder cho broadcast discovery.
# - start_lan_responder(p2p_port): chạy 1 thread lắng nghe broadcast và trả lời
# - find_peer_lan(timeout=2): gửi broadcast, chờ reply, trả về (ip, p2p_port) hoặc None

import socket
import threading
import json
import time
from typing import Optional, Tuple

BROADCAST_PORT = 50000
BROADCAST_ADDR = '<broadcast>'
DISCOVER_MSG = "FIND_PEER_V1"   # identifier để tránh nhầm với ứng dụng khác
REPLY_MSG = "PEER_HERE_V1"
BUFFER_SIZE = 1024

def _make_payload(username: str, p2p_port: int):
    return json.dumps({"type": "peer_announce", "username": username, "p2p_port": p2p_port})

def _parse_payload(data: bytes):
    try:
        return json.loads(data.decode('utf-8'))
    except Exception:
        return None

def start_lan_responder(username: str, p2p_port: int):
    """
    Chạy background thread để lắng nghe broadcast FIND_PEER_V1 và trả lời.
    Gọi 1 lần khi app khởi động (nếu muốn hỗ trợ bị tìm trong LAN).
    """
    def responder():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Cho phép bind vào tất cả địa chỉ
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('', BROADCAST_PORT))
        except Exception as e:
            print("[LAN_RESPONDER] bind error:", e)
            s.close()
            return

        while True:
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                # data có thể là FIND_PEER_V1 hoặc JSON
                text = data.decode('utf-8', errors='ignore')
                # Nếu là tìm kiếm (chỉ 1 token) — hỗ trợ cả 2 dạng
                if DISCOVER_MSG in text:
                    # trả lời bằng JSON để gửi p2p_port
                    payload = _make_payload(username, p2p_port)
                    s.sendto(payload.encode('utf-8'), addr)
                else:
                    # nếu là JSON kiểm tra type
                    parsed = _parse_payload(data)
                    if parsed and parsed.get("type") == "peer_discover":
                        # trả lời lại với announce
                        payload = _make_payload(username, p2p_port)
                        s.sendto(payload.encode('utf-8'), addr)
            except Exception:
                # tránh crash thread
                continue

    t = threading.Thread(target=responder, daemon=True)
    t.start()
    return t  # trả về thread nếu caller muốn dùng

def find_peer_lan(timeout: float = 2.0, username: str = None, p2p_port: int = None) -> Optional[Tuple[str, Optional[int]]]:
    """
    Gửi broadcast để tìm peer. Trả về (ip, p2p_port) nếu có, hoặc None.
    - timeout: tổng thời gian chờ (giây)
    - username, p2p_port: nếu được truyền, gửi như JSON; không bắt buộc
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(timeout)
    start = time.time()
    try:
        # Gửi dạng đơn giản để tương thích: "FIND_PEER_V1"
        try:
            s.sendto(DISCOVER_MSG.encode('utf-8'), (BROADCAST_ADDR, BROADCAST_PORT))
        except Exception:
            # thử broadcast theo cách khác
            s.sendto(DISCOVER_MSG.encode('utf-8'), ('255.255.255.255', BROADCAST_PORT))

        # nếu caller cung cấp username/p2p_port, cũng gửi JSON discovery
        if username is not None and p2p_port is not None:
            disc_payload = json.dumps({"type": "peer_discover", "username": username, "p2p_port": p2p_port})
            try:
                s.sendto(disc_payload.encode('utf-8'), (BROADCAST_ADDR, BROADCAST_PORT))
            except Exception:
                s.sendto(disc_payload.encode('utf-8'), ('255.255.255.255', BROADCAST_PORT))

        # chờ đáp trả (có thể nhiều responses) -> trả về response đầu tiên hợp lệ
        while True:
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                break
            s.settimeout(remaining)
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                break
            try:
                parsed = json.loads(data.decode('utf-8'))
                if parsed.get("type") in ("peer_announce",):
                    peer_ip = addr[0]
                    peer_port = parsed.get("p2p_port")
                    return (peer_ip, peer_port)
            except Exception:
                # nếu data là chuỗi đơn giản "PEER_HERE_V1" thì trả ip
                text = data.decode('utf-8', errors='ignore')
                if REPLY_MSG in text or "PEER_HERE" in text:
                    return (addr[0], None)
                # ngược lại bỏ qua
                continue
    finally:
        s.close()
    return None
