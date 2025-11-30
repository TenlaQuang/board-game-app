# ui/chess_menu.py
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UILabel, UIDropDownMenu, UIButton, UIImage
import os
from utils.constants import WIDTH, HEIGHT

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # --- KÍCH THƯỚC & VỊ TRÍ CHÍNH ---
        btn_w, btn_h = 360, 90 
        gap = 25
        center_x = (WIDTH - btn_w) // 2
        start_y = HEIGHT * 0.41 

        # --- CÁC NÚT MENU CHÍNH ---
        self.btn_pve = UIButton(
            relative_rect=pygame.Rect((center_x, start_y), (btn_w, btn_h)),
            text="Chơi với Máy (PvE)",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        self.btn_pvp_online = UIButton(
            relative_rect=pygame.Rect((center_x, start_y + btn_h + gap), (btn_w, btn_h)),
            text="Chơi Online (PvP)",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x, start_y + (btn_h + gap) * 2), (btn_w, btn_h)),
            text="Quay lại",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        # --- BIẾN QUẢN LÝ POPUP ---
        self.diff_window = None         # Cửa sổ popup
        self.diff_selector = None       # Dropdown trong popup
        self.btn_confirm_start = None   # Nút Confirm trong popup

        # --- LOAD ẢNH NỀN ---
        self.bg_image = None
        possible_paths = ["ui/assets/images/menu_bg.jpg", "ui/assets/images/menu_bg.png"]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.bg_image = pygame.transform.scale(pygame.image.load(path), (WIDTH, HEIGHT))
                    break
                except: pass
        
        self.hide()

    def show_difficulty_dialog(self):
        """Hàm tạo và hiển thị cửa sổ chọn độ khó"""
        if getattr(self, 'diff_window', None) is not None:
            return

        # 1. Tạo cửa sổ (Window)
        # Tăng kích thước xíu cho thoáng (300x250)
        window_rect = pygame.Rect(0, 0, 310, 280)
        window_rect.center = (WIDTH // 2, HEIGHT // 2)
        
        self.diff_window = UIWindow(
            rect=window_rect,
            manager=self.ui_manager,
            window_display_title="Cấu hình trận đấu",
            object_id="#diff_window"
        )

        # --- [THÊM] HÌNH NỀN GỖ CHO CỬA SỔ ---
        # Lấy ảnh bảng gỗ hoặc ảnh nền tối làm background cho window này
        try:
            # Bạn có thể dùng 'ui/assets/images/lobby_board.png' hoặc ảnh khác
            bg_surf = pygame.image.load('ui/assets/images/bg_online_menu.png').convert_alpha()
            # Cắt hoặc scale ảnh cho vừa cửa sổ
            bg_surf = pygame.transform.smoothscale(bg_surf, (300, 250))
        except:
            bg_surf = pygame.Surface((300, 250))
            bg_surf.fill((50, 40, 30)) # Màu nâu gỗ dự phòng

        # Đặt ảnh nền nằm dưới cùng (layer thấp nhất trong window)
        UIImage(
            relative_rect=pygame.Rect(0, 0, 300, 250),
            image_surface=bg_surf,
            manager=self.ui_manager,
            container=self.diff_window
        )
        # -------------------------------------

        # 2. Label "Chọn độ khó" (Thêm ID #diff_label để chỉnh font to/màu vàng)
        UILabel(
            relative_rect=pygame.Rect((10, 30), (280, 40)),
            text="CHỌN ĐỘ KHÓ",
            manager=self.ui_manager,
            container=self.diff_window,
            object_id="#diff_label" 
        )

        # 3. Dropdown chọn mức độ (Thêm ID #diff_dropdown)
        self.diff_selector = UIDropDownMenu(
            options_list=['EASY', 'MEDIUM', 'HARD'],
            starting_option='MEDIUM',
            relative_rect=pygame.Rect((50, 80), (200, 40)), # Cao hơn xíu cho dễ bấm
            manager=self.ui_manager,
            container=self.diff_window,
            object_id="#diff_dropdown"
        )

        # 4. Nút Bắt đầu (Dùng style nút gỗ #wood_btn)
        self.btn_confirm_start = UIButton(
            relative_rect=pygame.Rect((50, 160), (200, 50)),
            text="VÀO TRẬN",
            manager=self.ui_manager,
            container=self.diff_window,
            object_id="#wood_btn" # Dùng lại style nút gỗ đẹp có sẵn
        )
    def show(self):
        self.btn_pve.show()
        self.btn_pvp_online.show()
        self.btn_back.show()

    def hide(self):
        self.btn_pve.hide()
        self.btn_pvp_online.hide()
        self.btn_back.hide()
        # Nếu đang mở popup thì đóng luôn khi ẩn menu
        if self.diff_window:
            self.diff_window.kill()
            self.diff_window = None
        
    def draw(self):
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((45, 35, 25)) 

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # 1. Nút Quay lại
            if event.ui_element == self.btn_back:
                return 'BACK_TO_MAIN'
            
            # 2. Nút PvE -> Mở Popup (Chưa vào game ngay)
            if event.ui_element == self.btn_pve:
                self.show_difficulty_dialog()
            
            # 3. Nút "BẮT ĐẦU" (Trong Popup) -> Vào Game
            if event.ui_element == self.btn_confirm_start:
                # Lấy độ khó từ dropdown
                selected_diff = self.diff_selector.selected_option
                
                # Đóng cửa sổ popup
                self.diff_window.kill()
                self.diff_window = None
                self.btn_confirm_start = None
                
                # Trả về lệnh vào game
                return ('PLAY_OFFLINE', selected_diff)

            # 4. Nút PvP Online
            if event.ui_element == self.btn_pvp_online:
                return 'PLAY_ONLINE'

        # Xử lý sự kiện đóng cửa sổ popup (dấu X)
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.diff_window:
                self.diff_window = None
                self.btn_confirm_start = None

        return None