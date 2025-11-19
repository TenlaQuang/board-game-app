# network/web_matchmaking.py (Bản cuối cùng - Hỗ trợ Radmin & Game Type)
import requests
import subprocess
import re
from typing import Optional, Dict

# !!! LƯU Ý: Đảm bảo link này là link Render của bạn !!!
WEB_SERVER = "https://board-game-app-sv.onrender.com"

# ==========================
# LẤY IP RADMIN VPN (Windows)
# ==========================
# Trong network/web_matchmaking.py

def get_radmin_ip() -> Optional[str]:
    """Tìm IP Radmin bằng cách quét dải IP 26.x.x.x trong output ipconfig."""
    try:
        # Chạy lệnh ipconfig
        output = subprocess.check_output("ipconfig", shell=True, encoding="utf8")

        # FIX: Trực tiếp tìm kiếm IP dạng 26.x.x.x trong toàn bộ output
        # Regex tìm: "IPv4 Address" + [khoảng trắng/ký tự] + IP bắt đầu bằng 26.
        match = re.search(
            r"IPv4 Address[^\:]*: (26\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", 
            output
        )
        if match:
            # Trả về IP (ví dụ: 26.24.235.145)
            return match.group(1).strip()

    except Exception as e:
        # Lỗi nếu ipconfig không chạy được
        pass

    return None # Trả về None nếu không tìm thấy IP Radmin


# ==========================
# HEARTBEAT
# ==========================
def send_heartbeat(username: str, p2p_port: int):
    radmin_ip = get_radmin_ip()

    url = f"{WEB_SERVER}/heartbeat"
    try:
        requests.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip # Gửi IP Radmin (ưu tiên kết nối)
        }, timeout=5)
    except:
        pass


# ==========================
# LẤY DANH SÁCH USER ONLINE (HÀM BỊ LỖI Ở LẦN TRƯỚC)
# ==========================
def get_online_users() -> list:
    """Hàm này phải tồn tại để network_manager gọi."""
    url = f"{WEB_SERVER}/users"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []


# ==========================
# TẠO PHÒNG ONLINE
# ==========================
def create_room_online(username: str, p2p_port: int, game_type: str) -> Optional[str]:
    radmin_ip = get_radmin_ip() # Lấy IP Radmin

    url = f"{WEB_SERVER}/create-room"
    try:
        r = requests.post(url, json={
            "username": username,
            "p2p_port": p2p_port,
            "ip": radmin_ip, # Gửi IP Radmin/LAN
            "game_type": game_type
        }, timeout=90)
        if r.status_code == 200:
            return r.json().get("room_id")
    except Exception as e:
        # print(f"Err create: {e}")
        pass
    return None


# ==========================
# JOIN PHÒNG ONLINE
# ==========================
def join_room_online(username: str, room_id: str) -> Optional[Dict]:
    url = f"{WEB_SERVER}/join-room"
    try:
        r = requests.post(url, json={
            "username": username,
            "room_id": room_id
        }, timeout=90)
        if r.status_code == 200:
            return r.json() # Trả về game_type và host_ip (là IP Radmin)
    except Exception as e:
        # print(f"Err join: {e}")
        pass

    return None


# ==========================
# SEND INVITE
# ==========================
def send_invite_online(challenger: str, target: str, room_id: str, game_type: str):
    radmin_ip = get_radmin_ip() # Lấy IP Radmin

    url = f"{WEB_SERVER}/send-invite"
    try:
        requests.post(url, json={
            "challenger": challenger,
            "target": target,
            "room_id": room_id,
            "game_type": game_type,
            "ip": radmin_ip # Gửi IP Radmin/LAN
        }, timeout=2)
    except:
        pass


# ==========================
# CHECK INVITE
# ==========================
def check_invite_online(username: str):
    url = f"{WEB_SERVER}/check-invite/{username}"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "from" in data:
                return data
    except:
        pass
    return None