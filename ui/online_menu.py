import pygame
import pygame_gui
import threading
from pygame_gui.elements import UIWindow, UIButton, UITextEntryLine, UILabel, UISelectionList
from pygame_gui.windows import UIConfirmationDialog 
from utils.constants import WIDTH, HEIGHT
from network import web_matchmaking 

class OnlineMenu:
    def __init__(self, screen, ui_manager, network_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.network_manager = network_manager
        
        self.current_game_type = 'chess' 
        self.pending_room_id = None
        self.invite_dialog = None
        
        # Biến lưu trữ
        self.target_player = None 
        self.last_user_set = set()
        self.users_data = {} # Lưu trữ data người chơi

        # 1. Khung cửa sổ chính
        self.rect = pygame.Rect(0, 0, 700, 560)
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        
        self.window = UIWindow(
            rect=self.rect,
            manager=ui_manager,
            window_display_title="Sảnh Online (P2P)",
            object_id="#online_window"
        )
        
        # 2. NHẬP TÊN
        self.lbl_name = UILabel(pygame.Rect((20, 20), (300, 30)), "Nhập tên của bạn:", ui_manager, container=self.window)
        self.entry_name = UITextEntryLine(pygame.Rect((20, 50), (200, 40)), ui_manager, container=self.window)
        self.entry_name.set_text(self.network_manager.username)

        # 3. CỘT TRÁI (Tạo/Vào)
        y = 110 
        self.btn_create = UIButton(pygame.Rect((20, y), (150, 50)), "Tạo Phòng", ui_manager, container=self.window)
        self.lbl_room_id = UILabel(pygame.Rect((20, y+60), (300, 40)), "", ui_manager, container=self.window)
        self.lbl_or = UILabel(pygame.Rect((20, y+110), (300, 30)), "--- HOẶC NHẬP ID ---", ui_manager, container=self.window)
        self.entry_id = UITextEntryLine(pygame.Rect((20, y+150), (180, 40)), ui_manager, container=self.window)
        self.entry_id.set_allowed_characters('numbers')
        self.btn_join = UIButton(pygame.Rect((210, y+150), (80, 40)), "Vào", ui_manager, container=self.window)
        self.lbl_status = UILabel(pygame.Rect((20, y+210), (300, 30)), "Trạng thái: Sẵn sàng", ui_manager, container=self.window)
        self.btn_back = UIButton(pygame.Rect((20, 460), (100, 40)), "Quay lại", ui_manager, container=self.window)
        
        # 4. CỘT PHẢI (List User)
        self.lbl_list = UILabel(pygame.Rect((350, 20), (300, 30)), "Người chơi đang Online:", ui_manager, container=self.window)
        self.user_list = UISelectionList(pygame.Rect((350, 60), (300, 380)), item_list=[], manager=ui_manager, container=self.window)
        self.btn_challenge = UIButton(pygame.Rect((350, 450), (300, 50)), "Thách Đấu Người Chọn", ui_manager, container=self.window)
        
        self.window.hide()

    def show(self):
        self.window.show()
        game_name = "Cờ Vua" if self.current_game_type == 'chess' else "Cờ Tướng"
        self.window.set_display_title(f"Sảnh Online - {game_name}")
        
        # [QUAN TRỌNG] Cập nhật trạng thái mạng ngay khi hiện menu
        self.network_manager.current_lobby_state = self.current_game_type 
        
        self.network_manager.start_hosting_phase()
        self.network_manager.start_polling_users(self.update_user_list_ui)

    def hide(self):
        self.window.hide()
        self.network_manager.stop_polling_users()
        self.target_player = None 
        if self.invite_dialog:
            self.invite_dialog.kill()
            self.invite_dialog = None

    def update_user_list_ui(self, users, invite=None):
        # 1. Cập nhật dữ liệu người dùng
        self.users_data = {u['username']: u for u in users}

        current_selection = self.user_list.get_single_selection() 
        new_names = [f"{u['username']}" for u in users]
        new_user_set = set(new_names)
        
        if new_user_set != self.last_user_set: 
            self.user_list.set_item_list(new_names)
            self.last_user_set = new_user_set
            if current_selection and current_selection in new_names:
                self.user_list.set_selection_list([current_selection]) 

        # 2. Xử lý lời mời (Popup)
        if invite:
            challenger = invite.get("from")
            room_id = invite.get("room_id")
            g_type = invite.get("game_type", "chess") 
            
            # --- KIỂM TRA LOẠI GAME ---
            if g_type != self.current_game_type:
                # Nếu khác loại game, bỏ qua không hiện popup
                return 
            # --------------------------

            if self.invite_dialog is None:
                self.current_game_type = g_type 
                self.pending_room_id = room_id 
                game_name = "Cờ Vua" if g_type == "chess" else "Cờ Tướng"
                
                dialog_rect = pygame.Rect((0, 0), (400, 200))
                dialog_rect.center = (WIDTH // 2, HEIGHT // 2)
                
                self.invite_dialog = UIConfirmationDialog(
                    rect=dialog_rect, manager=self.ui_manager, window_title="Thách đấu",
                    action_long_desc=f"<b>{challenger}</b> mời bạn chơi <b>{game_name}</b>.<br>Đồng ý không?",
                    action_short_name="Đồng ý", blocking=True 
                )
                self.invite_dialog.rebuild() 

    def handle_events(self, event):
        # --- XỬ LÝ CLICK VÀO LIST ---
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.user_list:
                self.target_player = event.text
                # Lấy info để hiển thị thêm (tùy chọn)
                user_info = self.users_data.get(self.target_player)
                if user_info:
                    state = user_info.get('lobby_state', 'menu')
                    game_map = {'chess': 'Cờ Vua', 'chinese_chess': 'Cờ Tướng', 'menu': 'Menu'}
                    state_vn = game_map.get(state, state)
                    self.lbl_status.set_text(f"Đã chọn: {self.target_player} ({state_vn})")
                else:
                    self.lbl_status.set_text(f"Đã chọn: {self.target_player}")

        # --- XỬ LÝ POPUP ---
        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.invite_dialog:
                self.lbl_status.set_text("Đã chấp nhận! Đang vào phòng...")
                self.invite_dialog = None
                if self.pending_room_id:
                    self.entry_id.set_text(self.pending_room_id)
                    threading.Thread(target=self._thread_join, args=(self.pending_room_id,), daemon=True).start()
        
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.invite_dialog:
                self.lbl_status.set_text("Đã từ chối lời mời.")
                self.invite_dialog = None
                self.pending_room_id = None

        # --- XỬ LÝ NÚT BẤM ---
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_back:
                return "BACK"
            
            current_name = self.entry_name.get_text()
            if current_name: self.network_manager.username = current_name

            if event.ui_element == self.btn_create:
                self.lbl_status.set_text(f"Đang tạo phòng ({self.current_game_type})...")
                threading.Thread(target=self._thread_create, daemon=True).start()
                
            if event.ui_element == self.btn_join:
                rid = self.entry_id.get_text()
                if rid:
                    self.lbl_status.set_text(f"Đang tìm phòng {rid}...")
                    threading.Thread(target=self._thread_join, args=(rid,), daemon=True).start()
                else:
                    self.lbl_status.set_text("Vui lòng nhập ID!")

            if event.ui_element == self.btn_challenge:
                if self.target_player:
                    target_name = self.target_player
                    
                    # Lấy thông tin đối thủ
                    opponent_data = self.users_data.get(target_name)
                    
                    if target_name == self.network_manager.username:
                         self.lbl_status.set_text("Không thể tự thách đấu mình!")
                         
                    elif opponent_data:
                        opp_state = opponent_data.get('lobby_state', 'menu')
                        
                        # CHECK LOBBY STATE: Chặn nếu khác game
                        if opp_state != self.current_game_type:
                            game_names = {'chess': 'Cờ Vua', 'chinese_chess': 'Cờ Tướng', 'menu': 'Menu'}
                            opp_game_name = game_names.get(opp_state, "Không xác định")
                            self.lbl_status.set_text(f"Lỗi: {target_name} đang ở {opp_game_name}!")
                        else:
                            self.lbl_status.set_text(f"Đang mời {target_name} ({self.current_game_type})...")
                            threading.Thread(target=self._thread_challenge, args=(target_name,), daemon=True).start()
                    else:
                         self.lbl_status.set_text("Đang tải thông tin người chơi...")

                else:
                    self.lbl_status.set_text("Chưa chọn người chơi!") 
        return None

    def _thread_create(self):
        rid = web_matchmaking.create_room_online(
            self.network_manager.username, self.network_manager._listening_port, self.current_game_type
        )
        if rid: self.lbl_room_id.set_text(f"ROOM ID: {rid}"); self.lbl_status.set_text("Đang chờ...")
        else: self.lbl_status.set_text("Lỗi kết nối Server!")

    def _thread_join(self, rid):
        host_info = web_matchmaking.join_room_online(self.network_manager.username, rid)
        if host_info:
            ip, port = host_info.get('host_ip'), host_info.get('host_port')
            room_game_type = host_info.get('game_type', 'chess')
            self.current_game_type = room_game_type 
            self.lbl_status.set_text(f"Thấy Host! Kết nối {ip}...")
            if not self.network_manager.connect_to_peer(ip, port):
                self.lbl_status.set_text("Lỗi kết nối P2P.")
        else: self.lbl_status.set_text("Phòng không tồn tại!")

    def _thread_challenge(self, target_name):
        rid = web_matchmaking.create_room_online(
            self.network_manager.username, self.network_manager._listening_port, self.current_game_type
        )
        if rid:
            self.lbl_room_id.set_text(f"ROOM ID: {rid}")
            web_matchmaking.send_invite_online(
                self.network_manager.username, target_name, rid, self.current_game_type 
            )
            self.lbl_status.set_text(f"Đã mời {target_name}. Chờ phản hồi...")
        else: self.lbl_status.set_text("Lỗi tạo phòng.")