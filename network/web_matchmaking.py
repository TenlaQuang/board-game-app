# network/web_matchmaking.py (Cập nhật)
import requests

WEB_SERVER = "https://board-game-app-sv.onrender.com" # Kiểm tra lại link của bạn

# ... (send_heartbeat, get_online_users giữ nguyên) ...

def send_heartbeat(username: str, p2p_port: int):
    url = f"{WEB_SERVER}/heartbeat"
    try: requests.post(url, json={"username": username, "p2p_port": p2p_port}, timeout=5)
    except: pass

def get_online_users():
    url = f"{WEB_SERVER}/users"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200: return r.json()
    except: pass
    return []

# --- SỬA HÀM NÀY: THÊM game_type ---
def create_room_online(username: str, p2p_port: int, game_type: str):
    url = f"{WEB_SERVER}/create-room"
    try:
        r = requests.post(url, json={
            "username": username, 
            "p2p_port": p2p_port,
            "game_type": game_type # Gửi loại game lên
        }, timeout=90)
        if r.status_code == 200: return r.json().get("room_id")
    except Exception as e: print(f"Err create: {e}")
    return None

def join_room_online(username: str, room_id: str):
    url = f"{WEB_SERVER}/join-room"
    try:
        r = requests.post(url, json={"username": username, "room_id": room_id}, timeout=90)
        if r.status_code == 200: return r.json() # Server giờ sẽ trả về cả game_type
    except Exception as e: print(f"Err join: {e}")
    return None

# --- SỬA HÀM NÀY: THÊM game_type ---
def send_invite_online(challenger: str, target: str, room_id: str, game_type: str):
    url = f"{WEB_SERVER}/send-invite"
    try:
        requests.post(url, json={
            "challenger": challenger, 
            "target": target, 
            "room_id": room_id,
            "game_type": game_type # Báo cho đối thủ biết chơi game gì
        }, timeout=2)
    except: pass

def check_invite_online(username: str):
    url = f"{WEB_SERVER}/check-invite/{username}"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "from" in data: return data
    except: pass
    return None