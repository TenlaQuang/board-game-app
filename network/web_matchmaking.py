# network/web_matchmaking.py
# Giao tiếp với Matchmaking FastAPI (deploy trên Render hoặc VPS)
# - register_online(username, p2p_port) -> session_id / ok
# - find_peer_online(username, p2p_port, poll_interval, timeout) -> (peer_ip, peer_port) or None

import requests
import time
from typing import Optional, Tuple

# Thay đổi URL theo server bạn deploy (Render, Heroku, VPS...)
WEB_SERVER = "https://board-game-app-sv.onrender.com" 

# Endpoints giả định (same as mình đã cung cấp FastAPI trước đó)
# POST /register  { "username": "...", "p2p_port": 12345 } -> { "session_id": "..." }
# GET  /match/{session_id} -> { "status": "waiting" } hoặc { "status": "matched", "peer_ip": "...", "peer_p2p_port": 12345 }
# POST /unregister

def register_online(username: str, p2p_port: Optional[int] = None, timeout: float = 5.0) -> Optional[str]:
    """
    Đăng ký lên web matchmaking. Trả về session_id nếu OK.
    """
    url = WEB_SERVER.rstrip("/") + "/register"
    payload = {"username": username}
    if p2p_port is not None:
        payload["p2p_port"] = p2p_port
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            # nếu server trả về session_id hoặc ok
            return data.get("session_id") or data.get("session") or "ok"
    except Exception as e:
        # lỗi kết nối
        # print("[WEB] register error:", e)
        return None
    return None

def unregister_online(username: str, p2p_port: Optional[int] = None, timeout: float = 3.0):
    url = WEB_SERVER.rstrip("/") + "/unregister"
    payload = {"username": username}
    if p2p_port is not None:
        payload["p2p_port"] = p2p_port
    try:
        requests.post(url, json=payload, timeout=timeout)
    except Exception:
        pass

def find_peer_online(username: str, p2p_port: Optional[int] = None, poll_interval: float = 1.0, timeout: float = 60.0) -> Optional[Tuple[str, Optional[int]]]:
    """
    Đăng ký và poll server để chờ ghép cặp.
    - Trả về (peer_ip, peer_p2p_port) nếu matched.
    - Nếu timeout -> trả None.
    """
    session_id = register_online(username, p2p_port)
    if not session_id:
        return None

    # Nhiều server có API khác nhau; ở đây ta giả định có endpoint /match/{session_id}
    match_url = WEB_SERVER.rstrip("/") + f"/match/{session_id}"
    start = time.time()

    while True:
        if time.time() - start > timeout:
            # timeout -> try unregister
            try:
                unregister_online(username, p2p_port)
            except Exception:
                pass
            return None
        try:
            r = requests.get(match_url, timeout=5.0)
        except Exception:
            time.sleep(poll_interval)
            continue

        if r.status_code != 200:
            time.sleep(poll_interval)
            continue
        try:
            data = r.json()
        except Exception:
            time.sleep(poll_interval)
            continue

        status = data.get("status")
        if status == "matched":
            # server trả về peer info
            peer_ip = data.get("peer_ip") or data.get("opponent_public_ip")
            peer_port = data.get("peer_p2p_port") or data.get("p2p_port")
            # có thể server trả host/client info -> xử lý linh hoạt
            if isinstance(peer_ip, str):
                return (peer_ip, peer_port)
            else:
                time.sleep(poll_interval)
                continue

        # status waiting
        time.sleep(poll_interval)
