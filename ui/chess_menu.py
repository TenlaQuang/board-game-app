# ui/chess_menu.py
import pygame
import pygame_gui
# Import UIContainer từ core để sửa lỗi import
from pygame_gui.core import UIContainer
from pygame_gui.elements import UIWindow, UILabel, UIButton, UIImage
import os
from utils.constants import WIDTH, HEIGHT

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # --- KÍCH THƯỚC & VỊ TRÍ MENU CHÍNH ---
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
        self.diff_container = None 
        self.img_easy = None
        self.img_medium = None
        self.img_hard = None

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

    def create_text_button_image(self, image_path, text, size):
        """Hàm hỗ trợ: Load ảnh nút, scale và viết chữ lên đó"""
        try:
            if not os.path.exists(image_path):
                surf = pygame.Surface(size)
                surf.fill((200, 150, 50))
            else:
                surf = pygame.image.load(image_path).convert_alpha()
                surf = pygame.transform.smoothscale(surf, size)
            
            font = pygame.font.SysFont("Arial", 28, bold=True)
            text_surf = font.render(text, True, (60, 30, 10)) 
            text_rect = text_surf.get_rect(center=(size[0] // 2, size[1] // 2))
            surf.blit(text_surf, text_rect)
            return surf
        except Exception as e:
            print(f"Lỗi tạo nút ảnh: {e}")
            return pygame.Surface(size)

    # ĐÃ XÓA HÀM set_main_menu_enabled ĐỂ TRÁNH BỊ LỖI HIỂN THỊ MÀU XÁM

    def show_difficulty_dialog(self):
        """Hiển thị bảng chọn độ khó"""
        if getattr(self, 'diff_container', None) is not None:
            return

        # 1. Kích thước Popup
        window_w, window_h = 320, 420
        
        # Tạo Container
        self.diff_container = UIContainer(
            relative_rect=pygame.Rect((WIDTH//2 - window_w//2, HEIGHT//2 - window_h//2), (window_w, window_h)),
            manager=self.ui_manager
        )

        # 2. Ảnh nền Bảng gỗ
        try:
            bg_path = 'ui/assets/images/board_bg.png' 
            bg_surf = pygame.image.load(bg_path).convert_alpha()
            bg_surf = pygame.transform.smoothscale(bg_surf, (window_w, window_h))
            
            UIImage(
                relative_rect=pygame.Rect(0, 0, window_w, window_h),
                image_surface=bg_surf,
                manager=self.ui_manager,
                container=self.diff_container
            )
        except: pass

        # --- [MỚI] THÊM TIÊU ĐỀ VÀO KHUNG XANH ---
        # Tinh chỉnh vị trí y=20 để lọt vào khung xanh
        UILabel(
            relative_rect=pygame.Rect((10, 20), (window_w - 20, 40)), 
            text="CHỌN CẤP ĐỘ",
            manager=self.ui_manager,
            container=self.diff_container,
            object_id="#diff_title" # Đặt ID để chỉnh màu/font trong JSON nếu cần
        )
        # ------------------------------------------

        # 3. Tạo 3 Nút chọn độ khó
        btn_path = 'ui/assets/images/btn_bg.png' 
        btn_size = (150, 65)
        start_y_btn = 110 
        gap_btn = 20
        move_right = 5
        center_x_btn = ((window_w - btn_size[0]) // 2) + move_right
      
        surf_easy = self.create_text_button_image(btn_path, "EASY", btn_size)
        surf_medium = self.create_text_button_image(btn_path, "MEDIUM", btn_size)
        surf_hard = self.create_text_button_image(btn_path, "HARD", btn_size)

        self.img_easy = UIImage(
            relative_rect=pygame.Rect((center_x_btn, start_y_btn), btn_size),
            image_surface=surf_easy,
            manager=self.ui_manager,
            container=self.diff_container
        )

        self.img_medium = UIImage(
            relative_rect=pygame.Rect((center_x_btn, start_y_btn + btn_size[1] + gap_btn), btn_size),
            image_surface=surf_medium,
            manager=self.ui_manager,
            container=self.diff_container
        )

        self.img_hard = UIImage(
            relative_rect=pygame.Rect((center_x_btn, start_y_btn + (btn_size[1] + gap_btn)*2), btn_size),
            image_surface=surf_hard,
            manager=self.ui_manager,
            container=self.diff_container
        )

    def close_diff_window(self):
        if self.diff_container:
            self.diff_container.kill()
            self.diff_container = None
            self.img_easy = None
            self.img_medium = None
            self.img_hard = None

    def show(self):
        self.btn_pve.show()
        self.btn_pvp_online.show()
        self.btn_back.show()

    def hide(self):
        self.btn_pve.hide()
        self.btn_pvp_online.hide()
        self.btn_back.hide()
        self.close_diff_window()
        
    def draw(self):
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((45, 35, 25)) 

    def handle_events(self, event):
        # 1. XỬ LÝ SỰ KIỆN NÚT CHÍNH (PvE, PvP, Back)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # --- QUAN TRỌNG: CHẶN BẤM KHI POPUP ĐANG MỞ ---
            # Nếu popup đang mở (diff_container khác None), thì không xử lý nút menu chính
            if self.diff_container is not None:
                return None 
            # ----------------------------------------------

            if event.ui_element == self.btn_back:
                return 'BACK_TO_MAIN'
            if event.ui_element == self.btn_pve:
                self.show_difficulty_dialog()
            if event.ui_element == self.btn_pvp_online:
                return 'PLAY_ONLINE'

        # 2. XỬ LÝ CLICK CHUỘT VÀO POPUP (Easy/Medium/Hard)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.diff_container: 
                mouse_pos = event.pos
                
                # Check các nút trong popup
                if self.img_easy and self.img_easy.rect.collidepoint(mouse_pos):
                    self.close_diff_window()
                    return ('PLAY_OFFLINE', 'EASY')
                
                if self.img_medium and self.img_medium.rect.collidepoint(mouse_pos):
                    self.close_diff_window()
                    return ('PLAY_OFFLINE', 'MEDIUM')
                
                if self.img_hard and self.img_hard.rect.collidepoint(mouse_pos):
                    self.close_diff_window()
                    return ('PLAY_OFFLINE', 'HARD')
                
                # Check click ra ngoài bảng -> Đóng popup
                if not self.diff_container.rect.collidepoint(mouse_pos):
                    self.close_diff_window()

        return None