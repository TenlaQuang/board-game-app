import pygame
import pygame.scrap 
import pygame_gui
import threading
from pygame_gui.elements import UIWindow, UIButton, UITextEntryLine, UILabel, UISelectionList, UIImage
from pygame_gui.windows import UIConfirmationDialog 
from utils.constants import WIDTH, HEIGHT
from network import web_matchmaking 
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel
from pygame_gui.elements import UIScrollingContainer
class OnlineMenu:
    def __init__(self, screen, ui_manager, network_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.network_manager = network_manager
        self.invite_panel = None
        self.btn_close_invite = None
        
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
        self.is_logged_in = False 

        # Container chính
        # Kích thước cửa sổ là 800x600
        win_width, win_height = 800, 600
        self.rect = pygame.Rect(0, 0, win_width, win_height)
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        
        self.window = UIWindow(
            rect=self.rect,
            manager=ui_manager,
            window_display_title="Sảnh Online (P2P)",
            object_id="#online_window"
        )

        # ============================================================
        # [THÊM HÌNH NỀN] 1. TẢI VÀ CHUẨN BỊ HÌNH NỀN CHUNG
        # ============================================================
        try:
            # Tải hình ảnh
            self.common_bg_surface = pygame.image.load('ui/assets/images/bg_online_menu.png').convert()
            # Scale hình ảnh cho vừa khít với kích thước cửa sổ (800x600)
            self.common_bg_surface = pygame.transform.scale(self.common_bg_surface, (win_width, win_height))
        except FileNotFoundError:
            print("LỖI: Không tìm thấy file 'bg_online_menu.png'. Sử dụng nền tối mặc định.")
            # Tạo nền màu xám tối nếu không tìm thấy ảnh
            self.common_bg_surface = pygame.Surface((win_width, win_height))
            self.common_bg_surface.fill((40, 40, 40))
        # ============================================================
        
        self.ui_elements = []
        
        self.current_view = "LOGIN" 
        self.setup_login_view()
        
        self.window.hide()

    def show(self):
        self.window.show()
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
        self.close_invite_popup()
        if self.invite_list_window:
            self.invite_list_window.kill()
            self.invite_list_window = None

    # ============================================================
    # [THÊM HÌNH NỀN] 2. HÀM TRỢ GIÚP THÊM NỀN VÀO CỬA SỔ
    # ============================================================
    def _add_common_background(self):
        """Thêm hình nền chung vào đáy của cửa sổ hiện tại."""
        # Tạo UIImage phủ kín cửa sổ, đặt nó là phần tử đầu tiên để nó nằm dưới cùng.
        x_pos = -15   # Số DƯƠNG (+) dịch sang PHẢI, số ÂM (-) dịch sang TRÁI
        y_pos = -10   # Số DƯƠNG (+) dịch xuống DƯỚI, số ÂM (-) dịch lên TRÊN
    
    # Ví dụ: x_pos = -50 (dịch trái 50px), y_pos = -20 (dịch lên 20px)

        bg_image = UIImage(
        # Lưu ý: Thay self.rect.size bằng self.common_bg_surface.get_size() 
        # để khung hình nhận đúng kích thước ảnh bạn đã chỉnh ở bước 1
        relative_rect=pygame.Rect((x_pos, y_pos), self.common_bg_surface.get_size()),
        image_surface=self.common_bg_surface,
        manager=self.ui_manager,
        container=self.window
        )
        self.ui_elements.append(bg_image)
    # ============================================================


    # ==========================================
    # 0. MÀN HÌNH ĐĂNG NHẬP
    # ==========================================
    def setup_login_view(self):
        self.clear_ui()
        self._add_common_background() # Lớp 1: Nền chung
        
        self.current_view = "LOGIN"
        self.window.set_display_title("Đăng Nhập")

        # --- Lớp 2: Tấm bảng gỗ (Hình nền cho ô nhập liệu) ---
        try:
            # Load ảnh nền khung nhập
            image_surface = pygame.image.load('ui/assets/images/id_input_bg.png').convert_alpha()
        except FileNotFoundError:
            image_surface = pygame.Surface((400, 100))
            image_surface.fill((139, 69, 19))

        img_w, img_h = image_surface.get_size()
        
        # Vị trí của tấm bảng (Căn giữa)
        board_rect = pygame.Rect((0, 0), (img_w, img_h))
        board_rect.center = (400, 200) 

        self.img_lobby_board = UIImage(
            relative_rect=board_rect,
            image_surface=image_surface,
            manager=self.ui_manager,
            container=self.window
        )

        # --- Lớp 3: Dòng chữ và Ô nhập liệu ---
        
        # 1. Label tiêu đề
        lbl_title = UILabel(
            relative_rect=pygame.Rect((board_rect.x, board_rect.y - 16), (img_w, 30)), 
            text="Nhập tên hiển thị của bạn:", 
            manager=self.ui_manager, 
            container=self.window
        )

        # 2. Ô nhập liệu (Trong suốt đè lên bảng gỗ)
        input_width = img_w - 40 
        input_height = 40
        input_x = board_rect.x + 20
        input_y = board_rect.y + 40 

        self.entry_login_name = UITextEntryLine(
            relative_rect=pygame.Rect((input_x, input_y), (input_width, input_height)), 
            manager=self.ui_manager, 
            container=self.window,
            # SỬA: Phải dùng ObjectID() bao lại mới nhận diện được theme
            object_id=ObjectID(object_id="#transparent_input") 
        )
        self.entry_login_name.set_text_length_limit(20)
        self.entry_login_name.set_text(self.network_manager.username)
        
        # 3. Nút Kết Nối (Thay thế bằng hình ảnh)
        # SỬA: Chỉ giữ lại đoạn này, XÓA đoạn tạo nút bằng text phía dưới đi
        self.btn_login_connect = UIButton(
            relative_rect=pygame.Rect((250, board_rect.bottom + 20), (300, 80)),
            text="Nhấp vào chơi nào", # Để trống chữ để hiện ảnh
            manager=self.ui_manager,
            container=self.window,
            # SỬA: Dùng ObjectID để nhận ảnh enter_table_btn
            object_id=ObjectID(object_id='#enter_table_btn') 
        )

        # Các nút/nhãn khác
        self.btn_back_login = UIButton(pygame.Rect((20, 480), (100, 40)), "< Quay lại", self.ui_manager, container=self.window)
        self.lbl_login_status = UILabel(pygame.Rect((200, 360), (400, 30)), "", self.ui_manager, container=self.window)

        # --- Gom tất cả vào list quản lý (Chỉ gọi 1 lần) ---
        self.ui_elements.extend([
            self.img_lobby_board, 
            lbl_title, 
            self.entry_login_name, 
            self.btn_login_connect, 
            self.btn_back_login, 
            self.lbl_login_status
        ])

    # ==========================================
    # 1. MENU CHÍNH (DASHBOARD)
    # ==========================================
    def setup_main_view(self):
        self.clear_ui()
        self._add_common_background()  # Nền gỗ tối phía sau cùng

        self.current_view = "MAIN"
        # Tắt thanh tiêu đề mặc định của Window để nhìn thoáng hơn (nếu muốn)
        self.window.set_display_title(f"Sảnh Chính")

        # --- A. PHẦN CHÀO MỪNG (HEADER) ---
        # Tận dụng lại ảnh 'id_input_bg.png' làm nền cho dòng chữ chào mừng
        header_w, header_h = 400, 60
        header_rect = pygame.Rect((0, 0), (header_w, header_h))
        header_rect.centerx = 400 # Giữa màn hình ngang (800/2)
        header_rect.y = 50        # Cách đỉnh 50px

        try:
            banner_img = pygame.image.load('ui/assets/images/id_input_bg.png').convert_alpha()
            banner_img = pygame.transform.smoothscale(banner_img, (header_w, header_h))
        except:
            banner_img = pygame.Surface((header_w, header_h))
            banner_img.fill((50, 30, 20))

        UIImage(relative_rect=header_rect, image_surface=banner_img, manager=self.ui_manager, container=self.window)
        
        # Dòng chữ xin chào đè lên banner
        lbl_welcome = UILabel(
            relative_rect=header_rect, 
            text=f"Xin chào chủ tướng, {self.network_manager.username}!", 
            manager=self.ui_manager, 
            container=self.window,
            object_id=ObjectID(object_id="#lbl_gold_text") # Style chữ màu vàng cho sang
        )
        self.ui_elements.append(lbl_welcome)

        # --- B. HAI THẺ CHỨC NĂNG LỚN (CARDS) ---
        card_w, card_h = 240, 300
        gap = 60
        start_y = 140
        
        # Tọa độ thẻ bên trái (Tạo phòng)
        left_x = (800 - (card_w * 2 + gap)) // 2 
        rect_create = pygame.Rect((left_x, start_y), (card_w, card_h))
        
        # Tọa độ thẻ bên phải (Nhập ID)
        rect_join = pygame.Rect((left_x + card_w + gap, start_y), (card_w, card_h))

        # [1] Tạo thẻ TẠO PHÒNG
        # Bạn nên kiếm 1 ảnh đặt tên là 'card_create_bg.png' (ví dụ hình bàn cờ, quân tướng)
        self.btn_create_main = self._create_card_button(
            rect=rect_create,
            title="TẠO PHÒNG",
            sub_text="Làm chủ phòng đấu & Mời bạn bè",
            color_fallback=(100, 50, 50, 200), # Màu đỏ nâu nhạt nếu không có ảnh
            image_path='ui/assets/images/card_create_bg.png', 
            action_id="#transparent_btn_large"
        )

        # [2] Tạo thẻ NHẬP ID
        # Kiếm ảnh 'card_join_bg.png' (ví dụ hình kính lúp, chìa khóa)
        self.btn_join_main = self._create_card_button(
            rect=rect_join,
            title="NHẬP ID",
            sub_text="Tham chiến vào phòng có sẵn",
            color_fallback=(50, 70, 100, 200), # Màu xanh dương nhạt nếu không có ảnh
            image_path='ui/assets/images/card_join_bg.png',
            action_id="#transparent_btn_large"
        )
        
        self.ui_elements.extend([self.btn_create_main, self.btn_join_main])

        # --- C. NÚT ĐĂNG XUẤT (Góc dưới) ---
        # Làm nhỏ gọn, style gỗ
        # --- C. NÚT ĐĂNG XUẤT (Góc dưới) ---
        self.btn_logout = UIButton(
            relative_rect=pygame.Rect((20, 480), (120, 40)), 
            text="< Đăng xuất", 
            manager=self.ui_manager, 
            container=self.window,
            # XÓA dòng object_id="#wood_btn" đi, hoặc đổi thành:
            # object_id=ObjectID(object_id="#button") 
        )
        self.ui_elements.append(self.btn_logout)
    def _create_card_button(self, rect, title, sub_text, color_fallback, image_path, action_id):
        # --- 1. XỬ LÝ ẢNH NỀN ---
        try:
            # Load ảnh
            raw_img = pygame.image.load(image_path).convert_alpha()
            # Co giãn ảnh đúng kích thước thẻ
            bg_surf = pygame.transform.smoothscale(raw_img, (rect.width, rect.height))
            
            # [MỚI] Thêm lớp phủ đen mờ (Overlay) để chữ dễ đọc hơn
            dark_overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 80)) # Số 80 là độ đậm (0-255), tăng lên nếu muốn tối hơn
            bg_surf.blit(dark_overlay, (0, 0))

            # [MỚI] Cắt bo tròn góc ảnh (Radius = 20)
            bg_surf = self._crop_rounded_image(bg_surf, 20)

            # [MỚI] Vẽ thêm viền sáng bao quanh cho đẹp (Viền vàng/trắng)

        except (FileNotFoundError, pygame.error):
            # Fallback nếu lỗi ảnh (Vẽ khung màu bo tròn)
            bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, color_fallback, bg_surf.get_rect(), border_radius=20)
            pygame.draw.rect(bg_surf, (255, 255, 255), bg_surf.get_rect(), width=2, border_radius=20)

        # Hiển thị nền đã xử lý
        UIImage(relative_rect=rect, image_surface=bg_surf, manager=self.ui_manager, container=self.window)

        # --- 2. TIÊU ĐỀ (Title) ---
        # Chỉnh y xuống một chút (rect.y + 40) để cân đối
        title_rect = pygame.Rect((rect.x, rect.y + 40), (rect.width, 40))
        UILabel(
            relative_rect=title_rect,
            text=title,
            manager=self.ui_manager,
            container=self.window,
            object_id=ObjectID(object_id="#card_title")
        )

        # --- 3. MÔ TẢ (Sub-text) ---
        # Chỉnh bottom lên (-30)
        sub_rect = pygame.Rect((rect.x + 10, rect.bottom - 50), (rect.width - 20, 50))
        UILabel(
            relative_rect=sub_rect,
            text=sub_text,
            manager=self.ui_manager,
            container=self.window,
            object_id=ObjectID(object_id="#card_desc")
        )

        # --- 4. NÚT BẤM TRONG SUỐT ---
        btn = UIButton(
            relative_rect=rect,
            text="", 
            manager=self.ui_manager,
            container=self.window,
            object_id=ObjectID(object_id=action_id)
        )
        return btn
    def _crop_rounded_image(self, surface, radius):
        """
        Hàm cắt bo tròn 4 góc của một bức ảnh (Surface)
        """
        rect = surface.get_rect()
        # 1. Tạo một tấm mặt nạ (mask) trong suốt
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        # 2. Vẽ hình chữ nhật bo tròn màu trắng lên mặt nạ
        pygame.draw.rect(mask, (255, 255, 255), rect, border_radius=radius)
        
        # 3. Tạo ảnh kết quả
        result = pygame.Surface(rect.size, pygame.SRCALPHA)
        # Vẽ ảnh gốc lên
        result.blit(surface, (0, 0))
        # Dùng chế độ BLEND_RGBA_MIN để cắt ảnh theo hình dáng của mask
        result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return result
    # ==========================================
    # 2. NHẬP ID
    # ==========================================
    def setup_join_view(self):
        self.clear_ui()
        # [THÊM HÌNH NỀN] Gọi hàm thêm nền ngay sau khi clear
        self._add_common_background()

        self.current_view = "JOIN"
        self.window.set_display_title("Nhập Mã Phòng")
        
        if not hasattr(self, 'join_input_text'): self.join_input_text = ""

        # --- 1. HÌNH NỀN KHUNG ĐEN (Cái này là nền của ô nhập liệu, nằm trên nền chung) ---
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
        
        # --- 3. BÀN PHÍM SỐ ---
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
    # 3. SẢNH CHỜ
    # ==========================================
    def setup_lobby_view(self, room_id):
        self.clear_ui()
        # [THÊM HÌNH NỀN] Gọi hàm thêm nền ngay sau khi clear.
        # Lưu ý: Hình nền chung sẽ nằm DƯỚI hình 'lobby_board.png'
        self._add_common_background()

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
        
        # Cái này là cái bảng gỗ nhỏ, nó sẽ nằm ĐÈ LÊN nền chung
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
        # 1. Xóa bảng cũ nếu đang mở
        if hasattr(self, 'invite_panel') and self.invite_panel is not None:
            self.invite_panel.kill()

        # 2. Tính toán vị trí
        panel_w, panel_h = 400, 500
        win_w, win_h = 800, 600
        x = (win_w - panel_w) // 2
        y = (win_h - panel_h) // 2

        # 3. Tạo PANEL nền (Container chính)
        from pygame_gui.core import ObjectID 
        self.invite_panel = UIPanel(
            relative_rect=pygame.Rect((x, y), (panel_w, panel_h)),
            manager=self.ui_manager,
            container=self.window,
            object_id=ObjectID(object_id="#invite_board") 
        )

        # 4. Tiêu đề
        UILabel(
            relative_rect=pygame.Rect((0, 20), (panel_w, 40)),
            text="Mời Bạn Bè",
            manager=self.ui_manager,
            container=self.invite_panel,
            object_id=ObjectID(object_id="#lbl_xiangqi_text")
        )

        # ==========================================================
        # [THÊM MỚI] 5. Tạo hình nền cho danh sách (bg_invite.png)
        # ==========================================================
        
        # Xác định vị trí và kích thước chung cho cả Ảnh nền và List
        list_rect = pygame.Rect((30, 70), (panel_w - 60, panel_h - 160))

        try:
            # Load ảnh bg_invite.png
            # LƯU Ý: Đảm bảo file ảnh nằm đúng thư mục này
            bg_list_surf = pygame.image.load('ui/assets/images/bg_list.jpg').convert_alpha()
            # Co giãn ảnh cho vừa khít với khung danh sách
            bg_list_surf = pygame.transform.scale(bg_list_surf, (list_rect.width, list_rect.height))
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy bg_invite.png, dùng nền màu tạm.")
            bg_list_surf = pygame.Surface((list_rect.width, list_rect.height))
            bg_list_surf.fill((100, 80, 50)) # Màu nâu nếu lỗi ảnh

        # Đặt tấm ảnh nền vào Panel
        UIImage(
            relative_rect=list_rect,
            image_surface=bg_list_surf,
            manager=self.ui_manager,
            container=self.invite_panel
        )

        # 6. Tạo Danh Sách (Đè lên trên tấm ảnh vừa tạo)
        self.friend_scroll_container = UIScrollingContainer(
            relative_rect=list_rect, # Dùng lại vị trí bạn đã tính
            manager=self.ui_manager,
            container=self.invite_panel,
            object_id=ObjectID(object_id="#transparent_list")
        )
        self.friend_buttons = [] # Tạo cái list để quản lý mấy cái nút tên
        # ==========================================================

        # 7. Nút Gửi
        self.btn_send_invite_action = UIButton(
            relative_rect=pygame.Rect((panel_w//2 - 100, panel_h - 80), (200, 50)), 
            text="Gửi Lời Mời", 
            manager=self.ui_manager, 
            container=self.invite_panel,
            object_id=ObjectID(object_id="#wood_btn")
        )
        
        # 8. Nút Đóng (X)
        self.btn_close_invite = UIButton(
            relative_rect=pygame.Rect((panel_w - 40, 10), (30, 30)),
            text="X",
            manager=self.ui_manager,
            container=self.invite_panel,
            object_id=ObjectID(object_id="#close_btn_red")
        )

        # Cập nhật dữ liệu
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
            if hasattr(self, 'friend_items'):
                for btn in self.friend_items:
                    # Nếu cái nút vừa bấm (event.ui_element) là một trong các nút bạn bè
                    if event.ui_element == btn and isinstance(btn, UIButton):
                        # Lấy tên người chơi được giấu trong user_data
                        target = getattr(btn, 'user_data', None)
                        if target:
                            print(f"Đang gửi lời mời tới: {target}")
                            # Gửi lời mời ngay lập tức
                            threading.Thread(target=self._thread_send_invite, args=(target,), daemon=True).start()
                            
                            # Thông báo lên màn hình (nếu có label status)
                            if hasattr(self, 'lbl_lobby_status'):
                                self.lbl_lobby_status.set_text(f"Đã mời {target}!")
            if hasattr(self, 'btn_close_invite') and self.btn_close_invite is not None:
                if event.ui_element == self.btn_close_invite:
                    self.close_invite_popup()
            # ----------------
            
            # Các xử lý nút khác (ví dụ nút gửi lời mời)
            if hasattr(self, 'btn_send_invite_action') and self.btn_send_invite_action:
                 if event.ui_element == self.btn_send_invite_action:
                     # Gọi hàm gửi lời mời ở đây...
                     pass
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
        # 1. Ép kiểu dữ liệu an toàn
        current_users_list = list(users) if users is not None else []
        if current_users_list:
            filtered_users = [u for u in current_users_list if isinstance(u, dict) and u.get('lobby_state') == self.current_game_type]
            self.users_data = {u['username']: u for u in filtered_users}

        # 2. BẮT ĐẦU VẼ
        if hasattr(self, 'friend_scroll_container'):
            
            # --- [SỬA LẠI ĐOẠN XÓA] ---
            # Thay vì xóa tất cả (dễ xóa nhầm), ta chỉ xóa những gì ta đã tạo ra trong list 'friend_items'
            if not hasattr(self, 'friend_items'):
                self.friend_items = [] # Tạo sổ quản lý nếu chưa có

            for item in self.friend_items:
                item.kill() # Xóa từng món trong sổ
            self.friend_items.clear() # Xóa xong thì xé nháp sổ
            # --------------------------

            # Tải ảnh thanh gỗ nhỏ
            try:
                raw_img = pygame.image.load('ui/assets/images/bg_invite.png').convert_alpha()
                # [CHỈNH KÍCH THƯỚC THANH GỖ Ở ĐÂY CHO VỪA MẮT]
                ITEM_W = 340 
                ITEM_H = 45  
                scaled_bg = pygame.transform.smoothscale(raw_img, (ITEM_W, ITEM_H))
            except:
                ITEM_W, ITEM_H = 220, 45
                scaled_bg = pygame.Surface((ITEM_W, ITEM_H))

            y = 0
            container_w = self.friend_scroll_container.get_container().get_rect().width 
            center_x = (container_w - ITEM_W) // 2

            for u in self.users_data.values():
                name = u.get('username', 'Unknown')
                if name == self.network_manager.username: continue 

                # A. Vẽ Hình Nền Nhỏ
                img_item = UIImage(
                    relative_rect=pygame.Rect((center_x, y), (ITEM_W, ITEM_H)),
                    image_surface=scaled_bg,
                    manager=self.ui_manager,
                    container=self.friend_scroll_container
                )
                self.friend_items.append(img_item) # Ghi vào sổ để sau này xóa

                # B. Vẽ Nút Trong Suốt
                btn_item = UIButton(
                    relative_rect=pygame.Rect((center_x, y), (ITEM_W, ITEM_H)),
                    text=name,
                    manager=self.ui_manager,
                    container=self.friend_scroll_container,
                    object_id=ObjectID(object_id="#invisible_btn")
                )
                btn_item.user_data = name 
                self.friend_items.append(btn_item) # Ghi vào sổ để sau này xóa
                
                y += (ITEM_H + 5)

            self.friend_scroll_container.set_scrollable_area_dimensions((container_w, y))

        if invite: self._handle_incoming_invite(invite)

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
    def close_invite_popup(self):
        if hasattr(self, 'invite_panel') and self.invite_panel:
            self.invite_panel.kill()
            self.invite_panel = None
        
        # Xóa sạch các nút con
        if hasattr(self, 'friend_items'):
            for item in self.friend_items:
                if item.alive(): item.kill()
            self.friend_items.clear()         