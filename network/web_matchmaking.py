
import requests
import subprocess
import re
from typing import Optional, Dict
WEB_SERVER = "https://board-game-app-sv.onrender.com"

# ==========================
# LẤY IP RADMIN VPN (PowerShell)
# ==========================
def get_radmin_ip() -> Optional[str]:
    """Tìm IP Radmin bằng PowerShell (Cách mạnh nhất)."""
    try:
        # Dùng PowerShell để lọc IP bắt đầu bằng 26.
        cmd = 'powershell -command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like \'26.*\'} | Select-Object -ExpandProperty IPAddress"'
        output = subprocess.check_output(cmd, shell=True, encoding="utf8", timeout=3).strip()
        
        if output:
            return output.splitlines()[0].strip()
    except:
        try:
            output = subprocess.check_output("ipconfig", shell=True, encoding="utf8")
            match = re.search(r"IPv4 Address[^\:]*: (26\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", output)
            if match:
                return match.group(1).strip()
        except:
            pass
    return None

# ==========================
# HEARTBEAT (Cập nhật: Thêm lobby_state)
# ==========================
def send_heartbeat(username: str, p2p_port: int, lobby_state: str = "menu"):
    radmin_ip = get_radmin_ip()

    url = f"{WEB_SERVER}/heartbeat"
    try:
        requests.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip,       # Gửi IP Radmin
            "lobby_state": lobby_state # Gửi trạng thái (chess/xiangqi/menu)
        }, timeout=5)
    except:
        pass

# ==========================
# LẤY DANH SÁCH USER
# ==========================
def get_online_users() -> list:
    url = f"{WEB_SERVER}/users"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

# ==========================
# TẠO PHÒNG
# ==========================
def create_room_online(username: str, p2p_port: int, game_type: str) -> Optional[str]:
    radmin_ip = get_radmin_ip()

    url = f"{WEB_SERVER}/create-room"
    try:
        r = requests.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip,
            "game_type": game_type
        }, timeout=90)
        if r.status_code == 200:
            return r.json().get("room_id")
    except:
        pass
    return None

# ==========================
# VÀO PHÒNG
# ==========================
def join_room_online(username: str, room_id: str) -> Optional[Dict]:
    url = f"{WEB_SERVER}/join-room"
    try:
        r = requests.post(url, json={
            "username": username,
            "room_id": room_id
        }, timeout=90)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# ==========================
# GỬI MỜI
# ==========================
def send_invite_online(challenger: str, target: str, room_id: str, game_type: str):
    url = f"{WEB_SERVER}/send-invite"
    try:
        requests.post(url, json={
            "challenger": challenger,
            "target": target,
            "room_id": room_id,
            "game_type": game_type,
        }, timeout=2)
    except:
        pass

# ==========================
# KIỂM TRA MỜI
# ==========================
def check_invite_online(username: str):
    url = f"{WEB_SERVER}/check-invite/{username}"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "from" in data: return data
    except:
        pass
    return None

# ==========================
# CHẤP NHẬN MỜI (Optional)
# ==========================
def accept_invite_online(username: str, room_id: str):
    url = f"{WEB_SERVER}/accept-invite/{username}/{room_id}"
    try: requests.post(url, timeout=2)
    except: pass