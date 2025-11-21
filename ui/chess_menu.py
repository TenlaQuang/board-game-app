# ui/chess_menu.py
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UILabel, UIDropDownMenu, UIButton
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
        # Nếu cửa sổ đang mở rồi thì không mở nữa
        if self.diff_window is not None:
            return

        # 1. Tạo cửa sổ (Window)
        window_rect = pygame.Rect(0, 0, 300, 220)
        window_rect.center = (WIDTH // 2, HEIGHT // 2) # Căn giữa màn hình
        
        self.diff_window = UIWindow(
            rect=window_rect,
            manager=self.ui_manager,
            window_display_title="Cấu hình trận đấu",
            object_id="#diff_window"
        )

        # 2. Label "Chọn độ khó"
        UILabel(
            relative_rect=pygame.Rect((10, 20), (280, 30)),
            text="Chọn mức độ:",
            manager=self.ui_manager,
            container=self.diff_window # Gắn vào cửa sổ
        )

        # 3. Dropdown chọn mức độ
        self.diff_selector = UIDropDownMenu(
            options_list=['EASY', 'MEDIUM', 'HARD'],
            starting_option='MEDIUM',
            relative_rect=pygame.Rect((50, 60), (200, 30)),
            manager=self.ui_manager,
            container=self.diff_window
        )

        # 4. Nút Bắt đầu (Nhỏ gọn nằm trong cửa sổ)
        self.btn_confirm_start = UIButton(
            relative_rect=pygame.Rect((50, 120), (200, 50)),
            text="BẮT ĐẦU",
            manager=self.ui_manager,
            container=self.diff_window,
            object_id="#wood_btn_small" # Bạn có thể CSS thêm cho id này
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