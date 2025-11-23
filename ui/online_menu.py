import pygame
import pygame.scrap # <--- Import module này để dùng copy/paste
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
        
        # [SỬA LỖI 1] Khởi động hệ thống clipboard
        try:
            pygame.scrap.init()
        except pygame.error:
            print("Cảnh báo: Không thể khởi tạo clipboard (scrap). Tính năng Copy có thể không hoạt động.")

        self.current_game_type = 'chess' 
        self.users_data = {} 
        self.pending_room_id = None
        self.host_room_id = None 
        self.invite_dialog = None
        self.invite_list_window = None 

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
        self.current_view = "MAIN" 
        self.setup_main_view()
        self.window.hide()

    def show(self):
        self.window.show()
        self.network_manager.start_polling_users(self.update_user_list_ui)

    def hide(self):
        self.window.hide()
        self.network_manager.stop_polling_users()
        if self.invite_dialog:
            self.invite_dialog.kill()
        if self.invite_list_window:
            self.invite_list_window.kill()

    def clear_ui(self):
        """Xóa sạch giao diện cũ"""
        for element in self.ui_elements:
            element.kill()
        self.ui_elements = []
        if self.invite_list_window:
            self.invite_list_window.kill()
            self.invite_list_window = None

    # ==========================================
    # 1. MENU CHÍNH
    # ==========================================
    def setup_main_view(self):
        self.clear_ui()
        self.current_view = "MAIN"
        self.window.set_display_title("Chọn Chế Độ Chơi")

        btn_create = UIButton(pygame.Rect((100, 150), (250, 200)), "TẠO PHÒNG", self.ui_manager, container=self.window)
        btn_join = UIButton(pygame.Rect((450, 150), (250, 200)), "NHẬP ID PHÒNG", self.ui_manager, container=self.window)
        
        lbl_name = UILabel(pygame.Rect((250, 400), (300, 30)), "Tên hiển thị:", self.ui_manager, container=self.window)
        self.entry_name = UITextEntryLine(pygame.Rect((250, 430), (300, 40)), self.ui_manager, container=self.window)
        self.entry_name.set_text(self.network_manager.username)
        
        btn_back = UIButton(pygame.Rect((20, 500), (100, 40)), "Quay lại", self.ui_manager, container=self.window)

        self.ui_elements.extend([btn_create, btn_join, lbl_name, self.entry_name, btn_back])
        self.btn_create_main = btn_create
        self.btn_join_main = btn_join
        self.btn_back_main = btn_back

    # ==========================================
    # 2. NHẬP ID (SIZE NÚT 125x76 - FIX BỐ CỤC)
    # ==========================================
    def setup_join_view(self):
        self.clear_ui()
        self.current_view = "JOIN"
        self.window.set_display_title("Nhập Mã Phòng")
        
        self.join_input_text = ""

        # --- 1. HÌNH NỀN KHUNG ĐEN ---
        input_rect = pygame.Rect((229, 17), (350, 90)) # Đẩy ô nhập lên cao chút (y=30) cho thoáng
        try:
            bg_surf = pygame.image.load('ui/assets/images/id_input_bg.png').convert_alpha()
            bg_surf = pygame.transform.scale(bg_surf, (input_rect.width, input_rect.height))
        except FileNotFoundError:
            bg_surf = pygame.Surface((input_rect.width, input_rect.height))
            bg_surf.fill((30, 30, 30))

        self.input_bg = UIImage(
            relative_rect=input_rect,
            image_surface=bg_surf,
            manager=self.ui_manager,
            container=self.window
        )
        self.ui_elements.append(self.input_bg)

        # --- 2. HIỂN THỊ SỐ ---
        self.entry_join_id = UILabel(
            relative_rect=input_rect, 
            text="",
            manager=self.ui_manager, 
            container=self.window,
            object_id="#room_id_label" 
        )
        self.ui_elements.append(self.entry_join_id)
        
        # --- 3. BÀN PHÍM SỐ (SIZE 125x76) ---
        btn_w, btn_h = 125, 76
        gap = 10  # Khoảng cách nhỏ lại để tiết kiệm chỗ
        
        # Tính toán vị trí giữa màn hình 800px
        # Tổng rộng = (3 * 125) + (2 * 10) = 395px
        # Start X = (800 - 395) / 2 = 202
        start_x = 202
        start_y = 110 # Bắt đầu ngay dưới ô nhập liệu
        
        # Vòng lặp tạo nút 1-9
        for i in range(1, 10):
            r = (i - 1) // 3
            c = (i - 1) % 3
            btn = UIButton(
                relative_rect=pygame.Rect((start_x + c*(btn_w+gap), start_y + r*(btn_h+gap)), (btn_w, btn_h)), 
                text=str(i), 
                manager=self.ui_manager, 
                container=self.window,
                object_id="#keypad_btn" 
            )
            self.ui_elements.append(btn)
        
        # Hàng cuối: X, 0, <
        last_row_y = start_y + 3*(btn_h+gap)
        
        # Nút 0
        btn_0 = UIButton(
            relative_rect=pygame.Rect((start_x + 1*(btn_w+gap), last_row_y), (btn_w, btn_h)), 
            text="0", 
            manager=self.ui_manager, 
            container=self.window,
            object_id="#keypad_btn" 
        )
        
        # Nút Xóa (X)
        btn_clear = UIButton(
            relative_rect=pygame.Rect((start_x, last_row_y), (btn_w, btn_h)), 
            text="X", 
            manager=self.ui_manager, 
            container=self.window,
            object_id="#keypad_btn" 
        )
        
        # Nút Backspace (<)
        btn_back_join = UIButton(
            relative_rect=pygame.Rect((start_x + 2*(btn_w+gap), last_row_y), (btn_w, btn_h)), 
            text="<", 
            manager=self.ui_manager, 
            container=self.window,
            object_id="#keypad_btn" 
        )

        # --- 4. NÚT VÀO BÀN & BACK ---
        # Tính toán vị trí y kết thúc bàn phím: 110 + (4 * 86) = 454
        # Đặt nút Vào Bàn ở y = 470 là vừa đẹp, không bị tụt
        self.btn_confirm_join = UIButton(
            relative_rect=pygame.Rect((250, 460), (300, 70)), 
            text="VÀO BÀN", 
            manager=self.ui_manager, 
            container=self.window,
            object_id="#enter_table_btn"
        )
        
        self.btn_back_to_main = UIButton(pygame.Rect((20, 20), (80, 40)), "Back", self.ui_manager, container=self.window)

        self.ui_elements.extend([btn_0, btn_clear, btn_back_join, self.btn_confirm_join, self.btn_back_to_main])
        
        # Dòng trạng thái (đẩy xuống dưới cùng)
        self.lbl_status = UILabel(pygame.Rect((200, 550), (400, 30)), "Nhập ID để vào...", self.ui_manager, container=self.window)
        self.ui_elements.append(self.lbl_status)
    # ==========================================
    # 3. SẢNH CHỜ (LOBBY) 
    # ==========================================
    def setup_lobby_view(self, room_id):
        self.clear_ui()
        self.current_view = "LOBBY"
        self.host_room_id = room_id
        self.window.set_display_title("Phòng chờ")

        # 1. Kích thước ảnh
        board_w, board_h = 534, 427
        
        try:
            board_surf = pygame.image.load('ui/assets/images/lobby_board.png').convert_alpha()
            board_surf = pygame.transform.scale(board_surf, (board_w, board_h))
        except FileNotFoundError:
            board_surf = pygame.Surface((board_w, board_h))
            board_surf.fill((100, 70, 40))

        # 2. Tạo hình nền - CĂN GIỮA (CÓ TRỪ HAO TITLE BAR)
        win_w, win_h = self.rect.width, self.rect.height
        
        img_rect = pygame.Rect(0, 0, board_w, board_h)
        
        # [FIX QUAN TRỌNG] Trừ đi 40px ở trục Y để bảng nhích lên trên, bù lại cho thanh tiêu đề
        img_rect.center = ((win_w // 2) - 42, (win_h // 2) - 50) 
        
        self.lobby_bg = UIImage(
            relative_rect=img_rect,
            image_surface=board_surf,
            manager=self.ui_manager,
            container=self.window
        )
        self.ui_elements.append(self.lobby_bg)

        # Lấy mốc tọa độ mới của bảng
        bx, by = img_rect.x, img_rect.y

        # --- CĂN CHỈNH NÚT (DỊCH SANG PHẢI CHO KHỚP) ---

        # 1. Ô NHẬP ID
        # [FIX] Tăng bx từ 60 -> 75 để dịch sang phải lọt vào khung đen
        # width giảm còn 245 để không bị dài quá
        self.entry_room_display = UILabel(
            pygame.Rect((bx + 115, by + 170), (220, 50)), 
            text=str(room_id),
            manager=self.ui_manager,
            container=self.window,
            object_id="#room_id_label"
        )
        self.entry_room_display.set_text(str(room_id))
        self.entry_room_display.disable()
        
        # 2. NÚT COPY
        # [FIX] Tăng bx từ 340 -> 355 để dịch sang phải cho cân với ô ID
        self.btn_copy = UIButton(
            pygame.Rect((bx + 358, by + 170), (110, 50)), 
            "Copy", 
            self.ui_manager, 
            container=self.window,
            object_id="#transparent_btn" 
        )

        # 3. NÚT INVITE
        # Giữ nguyên độ cao by + 310, chỉnh nhẹ bx cho cân
        self.btn_open_invite_list = UIButton(
            pygame.Rect((bx + 162, by + 255), (150, 60)), 
            "Invite", 
            self.ui_manager, 
            container=self.window,
            object_id="#transparent_btn" 
        )
        
        # 4. NÚT EXIT
        self.btn_cancel_host = UIButton(
            pygame.Rect((bx + 269, by + 255), (150, 60)), 
            "Exit", 
            self.ui_manager, 
            container=self.window,
            object_id="#transparent_btn" 
        )

        # 5. Dòng trạng thái
        self.lbl_lobby_status = UILabel(
            pygame.Rect((bx + 40, by + 385), (454, 30)), 
            "", 
            self.ui_manager, 
            container=self.window
        )
        
        self.ui_elements.extend([self.entry_room_display, self.btn_copy, self.btn_open_invite_list, self.btn_cancel_host, self.lbl_lobby_status])
    # ==========================================
    # 4. POPUP DANH SÁCH MỜI
    # ==========================================
    def open_invite_popup(self):
        if self.invite_list_window is not None:
            self.invite_list_window.kill()

        w, h = 300, 400
        center_x = (WIDTH - w) // 2
        center_y = (HEIGHT - h) // 2
        
        self.invite_list_window = UIWindow(
            rect=pygame.Rect(center_x, center_y, w, h),
            manager=self.ui_manager,
            window_display_title="Mời bạn bè",
            resizable=False
        )
        
        self.user_list = UISelectionList(
            relative_rect=pygame.Rect((10, 10), (280, 280)),
            item_list=[], 
            manager=self.ui_manager,
            container=self.invite_list_window
        )

        self.btn_send_invite_action = UIButton(
            relative_rect=pygame.Rect((10, 300), (280, 50)),
            text="Gửi Lời Mời",
            manager=self.ui_manager,
            container=self.invite_list_window
        )
        
        self.update_user_list_ui(self.users_data.values(), None)

    # ==========================================
    # XỬ LÝ SỰ KIỆN (ĐÃ FIX LỖI get_text)
    # ==========================================
    def handle_events(self, event):
        if self.current_view == "SWITCH_TO_LOBBY" and self.host_room_id:
            self.setup_lobby_view(self.host_room_id)
            self.current_view = "LOBBY"

        if self.current_view == "MAIN" and hasattr(self, 'entry_name'):
             self.network_manager.username = self.entry_name.get_text()

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if hasattr(self, 'user_list') and event.ui_element == self.user_list:
                self.target_player = event.text

        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.invite_list_window:
                self.invite_list_window = None

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.invite_dialog:
                self.invite_dialog = None
                if self.pending_room_id:
                    threading.Thread(target=self._thread_join, args=(self.pending_room_id,), daemon=True).start()

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            
            # --- MAIN ---
            if self.current_view == "MAIN":
                if event.ui_element == self.btn_create_main:
                    threading.Thread(target=self._thread_create, daemon=True).start()
                elif event.ui_element == self.btn_join_main:
                    self.setup_join_view()
                elif event.ui_element == self.btn_back_main:
                    return "BACK"

            # --- JOIN (LOGIC MỚI: DÙNG BIẾN join_input_text) ---
            elif self.current_view == "JOIN":
                text = event.ui_element.text
                
                # Đảm bảo biến lưu trữ tồn tại (an toàn)
                if not hasattr(self, 'join_input_text'):
                    self.join_input_text = ""

                # 1. Bấm số
                if text.isdigit():
                    if len(self.join_input_text) < 6: 
                        self.join_input_text += text
                        self.entry_join_id.set_text(self.join_input_text) # Cập nhật Label
                
                # 2. Bấm Xóa (X)
                elif text == "X":
                    self.join_input_text = ""
                    self.entry_join_id.set_text("") 
                
                # 3. Bấm Backspace (<)
                elif text == "<":
                    self.join_input_text = self.join_input_text[:-1] 
                    self.entry_join_id.set_text(self.join_input_text)
                
                elif event.ui_element == self.btn_back_to_main:
                    self.setup_main_view()
                
                # 4. Bấm Vào Bàn (SỬA LỖI Ở ĐÂY)
                elif event.ui_element == self.btn_confirm_join:
                    # Lấy ID từ biến self.join_input_text thay vì get_text()
                    rid = self.join_input_text 
                    if rid:
                        self.lbl_status.set_text(f"Đang tìm phòng {rid}...")
                        threading.Thread(target=self._thread_join, args=(rid,), daemon=True).start()

            # --- LOBBY ---
            elif self.current_view == "LOBBY":
                if event.ui_element == self.btn_cancel_host:
                    self.setup_main_view()
                elif event.ui_element == self.btn_copy:
                    try:
                        pygame.scrap.put(pygame.SCRAP_TEXT, str(self.host_room_id).encode())
                        self.lbl_lobby_status.set_text("")
                    except pygame.error:
                        self.lbl_lobby_status.set_text("Lỗi copy clipboard!")
                
                elif event.ui_element == self.btn_open_invite_list:
                    self.open_invite_popup()

            # --- POPUP ---
            if hasattr(self, 'btn_send_invite_action') and event.ui_element == self.btn_send_invite_action:
                if hasattr(self, 'target_player') and self.target_player:
                    self.lbl_lobby_status.set_text(f"Đã gửi mời tới {self.target_player}")
                    threading.Thread(target=self._thread_send_invite, args=(self.target_player,), daemon=True).start()
                    if self.invite_list_window:
                        self.invite_list_window.kill()
                        self.invite_list_window = None
                else:
                    print("Chưa chọn người chơi!")

        return None
    # ==========================================
    # LOGIC MẠNG
    # ==========================================
    def update_user_list_ui(self, users, invite=None):
        if isinstance(users, list):
             self.users_data = {u['username']: u for u in users}
        else:
             self.users_data = {}

        if self.invite_list_window is not None and hasattr(self, 'user_list'):
            new_names = [u['username'] for u in users if u['username'] != self.network_manager.username]
            self.user_list.set_item_list(new_names)

        if invite:
            self._handle_incoming_invite(invite)

    def _handle_incoming_invite(self, invite):
        if self.invite_dialog is None:
            challenger = invite.get("from")
            room_id = invite.get("room_id")
            g_type = invite.get("game_type", "chess")
            
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

    def _thread_create(self):
        print("Đang mở port để Host...")
        self.network_manager.start_hosting_phase() 
        print(f"Đang tạo phòng trên Server...")
        rid = web_matchmaking.create_room_online(
            self.network_manager.username, 
            self.network_manager._listening_port, 
            self.current_game_type
        )
        if rid:
            self.host_room_id = rid
            self.current_view = "SWITCH_TO_LOBBY"
        else:
            print("Lỗi tạo phòng")

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
        web_matchmaking.send_invite_online(
            self.network_manager.username, target_name, self.host_room_id, self.current_game_type 
        )