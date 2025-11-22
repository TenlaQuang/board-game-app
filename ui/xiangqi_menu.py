import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT
import os
class XiangqiMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # --- ĐÃ SỬA: GIẢM KÍCH THƯỚC XUỐNG ---
        # Lúc trước là 280, 95 (hơi to)
        # Giảm xuống 220, 80 để nút gọn gàng, không bị bè
        w, h = 220, 80  
        
        # Khoảng cách giữa các nút
        gap = 16
        
        x = (WIDTH - w) // 2
        # Căn giữa màn hình theo chiều dọc
        start_y = HEIGHT * 0.38 
        

        # --- Nút Chơi Offline ---
        self.btn_pve = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, start_y), (w, h)),
            text="Chơi với Máy",
            manager=ui_manager,
            object_id='#xiangqi_btn'
        )

        # --- Nút Chơi Online ---
        self.btn_pvp_online = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, start_y + h + gap), (w, h)),
            text="Chơi Online",
            manager=ui_manager,
            object_id='#xiangqi_btn'
        ) 
        
        # --- Nút Quay lại ---
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, start_y + (h + gap) * 2), (w, h)),
            text="Quay lại",
            manager=ui_manager,
            object_id='#xiangqi_btn'
        )
        
        self.bg_image = None
        possible_paths = ["ui/assets/images/menu_bg_xiang.jpg", "ui/assets/images/menu_bg_xiang.png"]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.bg_image = pygame.transform.scale(pygame.image.load(path), (WIDTH, HEIGHT))
                    break
                except: pass

        self.hide()

    def show(self):
        self.btn_pve.show()
        self.btn_pvp_online.show()
        self.btn_back.show()

    def hide(self):
        self.btn_pve.hide()
        self.btn_pvp_online.hide()
        self.btn_back.hide()

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_back:
                return 'BACK_TO_MAIN' 
            if event.ui_element == self.btn_pve:
                return 'PLAY_OFFLINE' 
            if event.ui_element == self.btn_pvp_online:
                return 'PLAY_ONLINE'  
        return None
    def draw(self):
        """Vẽ hình nền cho menu Tướng"""
        if self.bg_image:
            # Vẽ ảnh nền nếu đã tải được
            self.screen.blit(self.bg_image, (0, 0))
        else:
            # Nếu không có ảnh, tô màu nâu đỏ để dễ nhìn
            self.screen.fill((60, 20, 20))