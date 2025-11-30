import requests
import subprocess
import re
import socket
import threading
from urllib.parse import quote # <--- [QUAN TRỌNG] Thêm thư viện này
from typing import Optional, Dict

WEB_SERVER = "https://board-game-app-sv.onrender.com"

# Session giúp kết nối nhanh hơn
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
session.mount('https://', adapter)

_CACHED_RADMIN_IP = None

def get_radmin_ip() -> Optional[str]:
    global _CACHED_RADMIN_IP
    if _CACHED_RADMIN_IP: return _CACHED_RADMIN_IP

    print("[NET] Đang quét IP Radmin lần đầu...")
    # 1. Socket
    try:
        hostname = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        for ip in ip_list:
            if ip.startswith("26."):
                _CACHED_RADMIN_IP = ip
                return ip
    except: pass
    
    # 2. PowerShell
    try:
        cmd = 'powershell -command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like \'26.*\'} | Select-Object -ExpandProperty IPAddress"'
        output = subprocess.check_output(cmd, shell=True, encoding="utf8", timeout=2, creationflags=0x08000000).strip()
        if output:
            ip = output.splitlines()[0].strip()
            _CACHED_RADMIN_IP = ip
            return ip
    except: pass

    # 3. Ipconfig
    try:
        output = subprocess.check_output("ipconfig", shell=True, encoding="utf8", creationflags=0x08000000)
        match = re.search(r":\s*(26\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
        if match:
            ip = match.group(1).strip()
            _CACHED_RADMIN_IP = ip
            return ip
    except: pass

    return None

# --- CÁC API SERVER ---

def send_heartbeat(username: str, p2p_port: int, lobby_state: str = "menu"):
    radmin_ip = get_radmin_ip()
    url = f"{WEB_SERVER}/heartbeat"
    try:
        session.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip,       
            "lobby_state": lobby_state 
        }, timeout=3)
    except: pass

def get_online_users() -> list:
    url = f"{WEB_SERVER}/users"
    try:
        r = session.get(url, timeout=4)
        if r.status_code == 200: return r.json()
    except: pass
    return []

def create_room_online(username: str, p2p_port: int, game_type: str) -> Optional[str]:
    radmin_ip = get_radmin_ip()
    url = f"{WEB_SERVER}/create-room"
    try:
        r = session.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip,
            "game_type": game_type
        }, timeout=10)
        if r.status_code == 200: return r.json().get("room_id")
    except: pass
    return None

def join_room_online(username: str, room_id: str) -> Optional[Dict]:
    url = f"{WEB_SERVER}/join-room"
    try:
        r = session.post(url, json={"username": username, "room_id": room_id}, timeout=10)
        if r.status_code == 200: return r.json()
    except: pass
    return None

# def send_invite_online(challenger: str, target: str, room_id: str, game_type: str):
#     url = f"{WEB_SERVER}/send-invite"
#     try:
#         session.post(url, json={
#             "challenger": challenger,
#             "target": target,
#             "room_id": room_id,
#             "game_type": game_type,
#         }, timeout=2)
#     except: pass
def send_invite_online(challenger: str, target: str, room_id: str, game_type: str):
    url = f"{WEB_SERVER}/send-invite"
    try:
        # [SỬA LẠI ĐÚNG NHƯ SERVER YÊU CẦU]
        payload = {
            "challenger": challenger,  # <--- Server bắt buộc dùng từ này
            "target": target,          # <--- Server bắt buộc dùng từ này
            "room_id": room_id,
            "game_type": game_type,
        }
        
        # Gửi đi
        r = session.post(url, json=payload, timeout=2)
        
        if r.status_code == 200:
            return True
        else:
            # In lỗi ra để debug nếu có
            print(f"❌ Server báo lỗi: {r.text}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi gửi mời: {e}")
        return False

def check_invite_online(username: str):
    # [FIX LỖI QUAN TRỌNG] Mã hóa tên username (VD: "Player 1" -> "Player%201")
    # Nếu không mã hóa, server sẽ không hiểu đường dẫn và trả về lỗi 404
    safe_username = quote(username) 
    
    url = f"{WEB_SERVER}/check-invite/{safe_username}"
    try:
        r = session.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "from" in data: return data
    except: pass
    return None

def accept_invite_online(username: str, room_id: str):
    # Cũng cần mã hóa ở đây cho chắc chắn
    safe_username = quote(username)
    url = f"{WEB_SERVER}/accept-invite/{safe_username}/{room_id}"
    try: session.post(url, timeout=2)
    except: pass

def wake_up_server():
    def _wake():
        try: requests.get(WEB_SERVER, timeout=3)
        except: pass
    threading.Thread(target=_wake, daemon=True).start()