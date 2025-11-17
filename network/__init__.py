# network/__init__.py
"""
Gói network: xử lý kết nối peer-to-peer (TCP)
- server.py: tạo phòng
- client.py: tham gia phòng
- connection.py: lớp Connection (gửi/nhận dữ liệu)
"""
# network/__init__.py
# Hàm điều phối chính: find_opponent(username, p2p_port)
# - ưu tiên dò LAN
# - nếu LAN không có -> thử Web matchmaking
from .lan_discovery import find_peer_lan, start_lan_responder
from .web_matchmaking import find_peer_online
from typing import Optional, Tuple

def find_opponent(username: str, p2p_port: int = None,
                  lan_timeout: float = 2.0,
                  web_timeout: float = 60.0,
                  web_poll_interval: float = 1.0) -> Optional[Tuple[str, Optional[int]]]:
    """
    Hàm chính gọi khi muốn tìm đối thủ.
    - Thử dò LAN trong lan_timeout giây.
    - Nếu có kết quả -> trả về (ip, port).
    - Nếu không -> thử tìm online qua web_matchmaking (tối đa web_timeout giây).
    """
    # 1) Thử LAN
    try:
        lan_res = find_peer_lan(timeout=lan_timeout, username=username, p2p_port=p2p_port)
        if lan_res:
            # lan_res là tuple (ip, p2p_port) hoặc None
            return lan_res
    except Exception as e:
        # lỗi LAN không quan trọng -> tiếp tục sang web
        print("[network] lan discovery error:", e)

    # 2) Nếu LAN không thấy -> thử Web matchmaking
    try:
        web_res = find_peer_online(username=username, p2p_port=p2p_port, poll_interval=web_poll_interval, timeout=web_timeout)
        if web_res:
            return web_res
    except Exception as e:
        print("[network] web matchmaking error:", e)

    return None

def start_responder_for_localhost(username: str, p2p_port: int):
    """
    Gọi hàm này khi app khởi động nếu bạn muốn máy này có thể
    phản hồi discovery từ người khác trong LAN.
    """
    try:
        start_lan_responder(username, p2p_port)
    except Exception as e:
        print("[network] cannot start LAN responder:", e)
