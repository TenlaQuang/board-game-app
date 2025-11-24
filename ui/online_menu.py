import pygame
import pygame.scrap 
import pygame_gui
import threading
from pygame_gui.elements import UIWindow, UIButton, UITextEntryLine, UILabel, UISelectionList, UIImage
from pygame_gui.windows import UIConfirmationDialog 
from utils.constants import WIDTH, HEIGHT
from network import web_matchmaking 

class OnlineMenu:
    def __init__(self, screen, ui_manager, network_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.network_manager = network_manager
        
        try:
            pygame.scrap.init()
        except pygame.error:
            print("Cảnh báo: Không thể khởi tạo clipboard (scrap).")

        self.current_game_type = 'chess' 
        self.users_data = {} 
        self.pending_room_id = None
        self.host_room_id = None 
        self.invite_dialog = None
        self.invite_list_window = None 
        self.is_logged_in = False # Cờ kiểm tra đăng nhập

        # Container chính
        self.rect = pygame.Rect(0, 0, 800, 600)
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        
        self.window = UIWindow(
            rect=self.rect,
            manager=ui_manager,
            window_display_title="Sảnh Online (P2P)",
            object_id="#online_window"
        )
        
        self.ui_elements = []
        
        # [THAY ĐỔI] Khởi động vào màn hình Login trước
        self.current_view = "LOGIN" 
        self.setup_login_view()
        
        self.window.hide()

    def show(self):
        self.window.show()
        # Chỉ poll nếu đã đăng nhập
        if self.is_logged_in:
            self.network_manager.start_polling_users(self.update_user_list_ui)

    def hide(self):
        self.window.hide()
        self.network_manager.stop_polling_users()
        if self.invite_dialog: self.invite_dialog.kill()
        if self.invite_list_window: self.invite_list_window.kill()

    def clear_ui(self):
        """Xóa sạch giao diện cũ"""
        for element in self.ui_elements:
            element.kill()
        self.ui_elements = []
        if self.invite_list_window:
            self.invite_list_window.kill()
            self.invite_list_window = None

    # ==========================================
    # [MỚI] 0. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    def setup_login_view(self):
        self.clear_ui()
        self.current_view = "LOGIN"
        self.window.set_display_title("Đăng Nhập")

        lbl_title = UILabel(pygame.Rect((200, 150), (400, 50)), "Nhập tên hiển thị của bạn:", self.ui_manager, container=self.window)
        
        self.entry_login_name = UITextEntryLine(pygame.Rect((250, 210), (300, 50)), self.ui_manager, container=self.window)
        self.entry_login_name.set_text(self.network_manager.username)
        
        self.btn_login_connect = UIButton(pygame.Rect((250, 280), (300, 60)), "KẾT NỐI SERVER", self.ui_manager, container=self.window)
        
        self.btn_back_login = UIButton(pygame.Rect((20, 500), (100, 40)), "Quay lại", self.ui_manager, container=self.window)

        self.lbl_login_status = UILabel(pygame.Rect((200, 360), (400, 30)), "", self.ui_manager, container=self.window)

        self.ui_elements.extend([lbl_title, self.entry_login_name, self.btn_login_connect, self.btn_back_login, self.lbl_login_status])

    # ==========================================
    # 1. MENU CHÍNH (DASHBOARD) - ĐÃ SỬA NHẸ
    # ==========================================
    def setup_main_view(self):
        self.clear_ui()
        self.current_view = "MAIN"
        self.window.set_display_title(f"Sảnh Chính - {self.network_manager.username}")

        # Giữ nguyên vị trí nút Tạo/Nhập phòng của bạn
        btn_create = UIButton(pygame.Rect((100, 150), (250, 200)), "TẠO PHÒNG", self.ui_manager, container=self.window)
        btn_join = UIButton(pygame.Rect((450, 150), (250, 200)), "NHẬP ID PHÒNG", self.ui_manager, container=self.window)
        
        # [SỬA] Thay ô nhập tên thành Label chào mừng (vì đã nhập ở Login rồi)
        lbl_welcome = UILabel(pygame.Rect((200, 430), (400, 40)), f"Xin chào, {self.network_manager.username}!", self.ui_manager, container=self.window)
        
        # Thêm nút Đăng xuất (Logout)
        self.btn_logout = UIButton(pygame.Rect((20, 500), (100, 40)), "Đăng xuất", self.ui_manager, container=self.window)

        self.ui_elements.extend([btn_create, btn_join, lbl_welcome, self.btn_logout])
        self.btn_create_main = btn_create
        self.btn_join_main = btn_join

    # ==========================================
    # 2. NHẬP ID (GIỮ NGUYÊN 100% CỦA BẠN)
    # ==========================================
    def setup_join_view(self):
        self.clear_ui()
        self.current_view = "JOIN"
        self.window.set_display_title("Nhập Mã Phòng")
        
        # Đảm bảo biến text tồn tại
        if not hasattr(self, 'join_input_text'): self.join_input_text = ""

        # --- 1. HÌNH NỀN KHUNG ĐEN ---
        input_rect = pygame.Rect((229, 17), (350, 90)) 
        try:
            bg_surf = pygame.image.load('ui/assets/images/id_input_bg.png').convert_alpha()
            bg_surf = pygame.transform.scale(bg_surf, (input_rect.width, input_rect.height))
        except FileNotFoundError:
            bg_surf = pygame.Surface((input_rect.width, input_rect.height))
            bg_surf.fill((30, 30, 30))

        self.input_bg = UIImage(relative_rect=input_rect, image_surface=bg_surf, manager=self.ui_manager, container=self.window)
        self.ui_elements.append(self.input_bg)

        # --- 2. HIỂN THỊ SỐ ---
        self.entry_join_id = UILabel(relative_rect=input_rect, text=self.join_input_text, manager=self.ui_manager, container=self.window, object_id="#room_id_label")
        self.ui_elements.append(self.entry_join_id)
        
        # --- 3. BÀN PHÍM SỐ (GIỮ NGUYÊN) ---
        btn_w, btn_h = 125, 76
        gap = 10  
        start_x = 202
        start_y = 110 
        
        for i in range(1, 10):
            r = (i - 1) // 3
            c = (i - 1) % 3
            btn = UIButton(relative_rect=pygame.Rect((start_x + c*(btn_w+gap), start_y + r*(btn_h+gap)), (btn_w, btn_h)), text=str(i), manager=self.ui_manager, container=self.window, object_id="#keypad_btn")
            self.ui_elements.append(btn)
        
        last_row_y = start_y + 3*(btn_h+gap)
        btn_0 = UIButton(relative_rect=pygame.Rect((start_x + 1*(btn_w+gap), last_row_y), (btn_w, btn_h)), text="0", manager=self.ui_manager, container=self.window, object_id="#keypad_btn")
        btn_clear = UIButton(relative_rect=pygame.Rect((start_x, last_row_y), (btn_w, btn_h)), text="X", manager=self.ui_manager, container=self.window, object_id="#keypad_btn")
        btn_back_join = UIButton(relative_rect=pygame.Rect((start_x + 2*(btn_w+gap), last_row_y), (btn_w, btn_h)), text="<", manager=self.ui_manager, container=self.window, object_id="#keypad_btn")

        # --- 4. NÚT VÀO BÀN & BACK ---
        self.btn_confirm_join = UIButton(relative_rect=pygame.Rect((250, 460), (300, 70)), text="VÀO BÀN", manager=self.ui_manager, container=self.window, object_id="#enter_table_btn")
        self.btn_back_to_main = UIButton(pygame.Rect((20, 20), (80, 40)), "Back", self.ui_manager, container=self.window)

        self.ui_elements.extend([btn_0, btn_clear, btn_back_join, self.btn_confirm_join, self.btn_back_to_main])
        self.lbl_status = UILabel(pygame.Rect((200, 550), (400, 30)), "Nhập ID để vào...", self.ui_manager, container=self.window)
        self.ui_elements.append(self.lbl_status)

    # ==========================================
    # 3. SẢNH CHỜ (GIỮ NGUYÊN 100% CỦA BẠN)
    # ==========================================
    def setup_lobby_view(self, room_id):
        self.clear_ui()
        self.current_view = "LOBBY"
        self.host_room_id = room_id
        self.window.set_display_title("Phòng chờ")

        board_w, board_h = 534, 427
        try:
            board_surf = pygame.image.load('ui/assets/images/lobby_board.png').convert_alpha()
            board_surf = pygame.transform.scale(board_surf, (board_w, board_h))
        except FileNotFoundError:
            board_surf = pygame.Surface((board_w, board_h)); board_surf.fill((100, 70, 40))

        win_w, win_h = self.rect.width, self.rect.height
        img_rect = pygame.Rect(0, 0, board_w, board_h)
        img_rect.center = ((win_w // 2) - 42, (win_h // 2) - 50) 
        
        self.lobby_bg = UIImage(relative_rect=img_rect, image_surface=board_surf, manager=self.ui_manager, container=self.window)
        self.ui_elements.append(self.lobby_bg)

        bx, by = img_rect.x, img_rect.y
        self.entry_room_display = UILabel(pygame.Rect((bx + 115, by + 170), (220, 50)), text=str(room_id), manager=self.ui_manager, container=self.window, object_id="#room_id_label")
        self.btn_copy = UIButton(pygame.Rect((bx + 358, by + 170), (110, 50)), "Copy", self.ui_manager, container=self.window, object_id="#transparent_btn")
        self.btn_open_invite_list = UIButton(pygame.Rect((bx + 162, by + 255), (150, 60)), "Invite", self.ui_manager, container=self.window, object_id="#transparent_btn")
        self.btn_cancel_host = UIButton(pygame.Rect((bx + 269, by + 255), (150, 60)), "Exit", self.ui_manager, container=self.window, object_id="#transparent_btn")
        self.lbl_lobby_status = UILabel(pygame.Rect((bx + 40, by + 385), (454, 30)), "", self.ui_manager, container=self.window)
        self.ui_elements.extend([self.entry_room_display, self.btn_copy, self.btn_open_invite_list, self.btn_cancel_host, self.lbl_lobby_status])

    # ==========================================
    # 4. POPUP DANH SÁCH MỜI
    # ==========================================
    def open_invite_popup(self):
        if self.invite_list_window is not None: self.invite_list_window.kill()
        w, h = 300, 400
        self.invite_list_window = UIWindow(rect=pygame.Rect((WIDTH - w) // 2, (HEIGHT - h) // 2, w, h), manager=self.ui_manager, window_display_title="Mời bạn bè", resizable=False)
        self.user_list = UISelectionList(relative_rect=pygame.Rect((10, 10), (280, 280)), item_list=[], manager=self.ui_manager, container=self.invite_list_window)
        self.btn_send_invite_action = UIButton(relative_rect=pygame.Rect((10, 300), (280, 50)), text="Gửi Lời Mời", manager=self.ui_manager, container=self.invite_list_window)
        self.update_user_list_ui(self.users_data.values(), None)

    # ==========================================
    # XỬ LÝ SỰ KIỆN
    # ==========================================
    def handle_events(self, event):
        # Logic chuyển view từ Thread
        if self.current_view == "SWITCH_TO_MAIN":
             self.setup_main_view()
        elif self.current_view == "SWITCH_TO_LOBBY" and self.host_room_id:
            self.setup_lobby_view(self.host_room_id)
            self.current_view = "LOBBY"

        # Logic sự kiện UI
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if hasattr(self, 'user_list') and event.ui_element == self.user_list:
                self.target_player = event.text

        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.invite_list_window:
                self.invite_list_window = None

            elif event.ui_element == self.invite_dialog:
                self.invite_dialog = None

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.invite_dialog:
                self.invite_dialog = None
                if self.pending_room_id:
                    threading.Thread(target=self._thread_join, args=(self.pending_room_id,), daemon=True).start()

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            
            # --- [MỚI] LOGIN VIEW ---
            if self.current_view == "LOGIN":
                if event.ui_element == self.btn_login_connect:
                    username = self.entry_login_name.get_text().strip()
                    if username:
                        self.lbl_login_status.set_text("Đang kết nối server...")
                        threading.Thread(target=self._thread_login, args=(username,), daemon=True).start()
                    else:
                        self.lbl_login_status.set_text("Vui lòng nhập tên!")
                elif event.ui_element == self.btn_back_login:
                    return "BACK"

            # --- MAIN VIEW ---
            elif self.current_view == "MAIN":
                if event.ui_element == self.btn_create_main:
                    threading.Thread(target=self._thread_create, daemon=True).start()
                elif event.ui_element == self.btn_join_main:
                    self.setup_join_view()
                elif event.ui_element == self.btn_logout: # Nút logout quay về Login
                    self.is_logged_in = False
                    self.network_manager.stop_polling_users()
                    self.setup_login_view()

            # --- JOIN VIEW ---
            elif self.current_view == "JOIN":
                text = event.ui_element.text
                if not hasattr(self, 'join_input_text'): self.join_input_text = ""
                if text.isdigit():
                    if len(self.join_input_text) < 6: 
                        self.join_input_text += text
                        self.entry_join_id.set_text(self.join_input_text)
                elif text == "X":
                    self.join_input_text = ""; self.entry_join_id.set_text("") 
                elif text == "<":
                    self.join_input_text = self.join_input_text[:-1]; self.entry_join_id.set_text(self.join_input_text)
                
                elif event.ui_element == self.btn_back_to_main:
                    self.setup_main_view()
                
                elif event.ui_element == self.btn_confirm_join:
                    rid = self.join_input_text 
                    if rid:
                        self.lbl_status.set_text(f"Đang tìm phòng {rid}...")
                        threading.Thread(target=self._thread_join, args=(rid,), daemon=True).start()

            # --- LOBBY VIEW ---
            elif self.current_view == "LOBBY":
                if event.ui_element == self.btn_cancel_host:
                    self.setup_main_view()
                elif event.ui_element == self.btn_copy:
                    try: pygame.scrap.put(pygame.SCRAP_TEXT, str(self.host_room_id).encode()); self.lbl_lobby_status.set_text("")
                    except: self.lbl_lobby_status.set_text("Lỗi copy clipboard!")
                elif event.ui_element == self.btn_open_invite_list:
                    self.open_invite_popup()

            # --- POPUP ---
            if hasattr(self, 'btn_send_invite_action') and event.ui_element == self.btn_send_invite_action:
                if hasattr(self, 'target_player') and self.target_player:
                    self.lbl_lobby_status.set_text(f"Đã gửi mời tới {self.target_player}")
                    threading.Thread(target=self._thread_send_invite, args=(self.target_player,), daemon=True).start()
                    if self.invite_list_window: self.invite_list_window.kill(); self.invite_list_window = None

        return None

    # ==========================================
    # LOGIC MẠNG
    # ==========================================

    def update_user_list_ui(self, users, invite=None):
        if isinstance(users, list):
            # [FIX QUAN TRỌNG] Chỉ lấy những người đang chơi CÙNG LOẠI GAME với mình
            # Nếu mình đang ở 'chess' -> chỉ thấy người 'chess'
            # Nếu mình đang ở 'chinese_chess' -> chỉ thấy người 'chinese_chess'
            filtered_users = [
                u for u in users 
                if u.get('lobby_state') == self.current_game_type 
            ]
            self.users_data = {u['username']: u for u in filtered_users}
        else:
             self.users_data = {}

        # Cập nhật danh sách lên giao diện Popup (nếu đang mở)
        if self.invite_list_window is not None and hasattr(self, 'user_list'):
            # Lọc bỏ tên chính mình ra
            new_names = [u['username'] for u in self.users_data.values() if u['username'] != self.network_manager.username]
            self.user_list.set_item_list(new_names)

        # Xử lý lời mời đến (Giữ nguyên)
        if invite:
            self._handle_incoming_invite(invite)

    def _handle_incoming_invite(self, invite):
        # Chỉ hiện nếu chưa có hộp thoại nào
        if self.invite_dialog is None:
            challenger = invite.get("from")
            room_id = invite.get("room_id")
            g_type = invite.get("game_type", "chess")
            
            # Kiểm tra xem lời mời có đúng loại game mình đang chơi không
            if g_type != self.current_game_type:
                return # Bỏ qua nếu khác loại cờ

            self.pending_room_id = room_id
            self.invite_dialog = UIConfirmationDialog(
                rect=pygame.Rect((0, 0), (400, 200)),
                manager=self.ui_manager,
                window_title="Thách Đấu!",
                action_long_desc=f"<b>{challenger}</b> mời bạn chơi {g_type}.<br>ID: {room_id}",
                action_short_name="Vào Ngay",
                blocking=True
            )
            self.invite_dialog.rect.center = (WIDTH // 2, HEIGHT // 2)
            self.invite_dialog.rebuild()

    # [MỚI] THREAD LOGIN
    def _thread_login(self, username):
        self.network_manager.username = username
        # Mở port trước để sẵn sàng nhận kết nối
        self.network_manager.start_hosting_phase() 
        # Bắt đầu gửi tên lên Server (hiện tên ngay lập tức)
        self.is_logged_in = True
        self.network_manager.start_polling_users(self.update_user_list_ui)
        # Vào màn hình chính
        self.current_view = "SWITCH_TO_MAIN"

    # [FIX] Cập nhật hàm này trong ui/online_menu.py
    def _thread_create(self):
        # Đảm bảo reset sạch sẽ kết nối cũ trước khi tạo mới
        self.network_manager.reset_connection()
        
        # Bắt đầu mở cổng lắng nghe mới
        port = self.network_manager.start_hosting_phase()
        if port == 0:
            print("Lỗi: Không thể mở port trên máy tính!")
            return

        print(f"[NET] Đang gửi yêu cầu tạo phòng (Port {port})...")
        
        # [MỚI] Cơ chế thử lại 3 lần (Retry Logic)
        rid = None
        for i in range(3):
            rid = web_matchmaking.create_room_online(
                self.network_manager.username, 
                port, 
                self.current_game_type
            )
            if rid:
                print(f"[NET] Tạo phòng thành công: {rid}")
                break
            else:
                print(f"[NET] Tạo phòng thất bại (Lần {i+1}). Đang thử lại...")
                import time
                time.sleep(1) # Nghỉ 1 giây rồi thử lại
        
        if rid:
            self.host_room_id = rid
            self.current_view = "SWITCH_TO_LOBBY"
        else:
            print("[NET] Lỗi: Server không phản hồi sau 3 lần thử.")
            # Có thể thêm thông báo lỗi lên UI nếu muốn

    def _thread_join(self, rid):
        host_info = web_matchmaking.join_room_online(self.network_manager.username, rid)
        if host_info:
            ip, port = host_info.get('host_ip'), host_info.get('host_port')
            if self.network_manager.connect_to_peer(ip, port):
                print("Kết nối P2P thành công!")
            else:
                if hasattr(self, 'lbl_status'): self.lbl_status.set_text("Lỗi kết nối P2P.")
        else:
            if hasattr(self, 'lbl_status'): self.lbl_status.set_text("Không tìm thấy phòng!")

    def _thread_send_invite(self, target_name):
        web_matchmaking.send_invite_online(self.network_manager.username, target_name, self.host_room_id, self.current_game_type)
 
    def reset_ui_state(self):
        """Xóa trạng thái phòng cũ, đưa về màn hình Dashboard"""
        self.host_room_id = None
        self.pending_room_id = None
        if hasattr(self, 'lbl_lobby_status'): 
            self.lbl_lobby_status.set_text("")
        
        # [THÊM DÒNG NÀY] Xóa danh sách người chơi cũ để đợi load mới
        self.users_data = {} 
        if hasattr(self, 'online_list_ui'):
            self.online_list_ui.set_item_list([])

        if self.current_view in ["LOBBY", "JOIN"]:
             self.setup_main_view()