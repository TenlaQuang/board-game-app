import pygame
import pygame_gui
from utils.constants import WIDTH

class XiangqiMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # Kích thước và vị trí nút (Căn giữa)
        w, h = 280, 50  # Chiều rộng nút to hơn chút cho chữ tiếng Việt
        x = (WIDTH - w) // 2
        
        # Vị trí Y bắt đầu
        y = 250 

        # Nút Chơi với Máy (Offline)
        self.btn_pve = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y), (w, h)),
            text="Chơi Cờ Tướng (Offline)",
            manager=ui_manager
        )

        # Nút Chơi Online (P2P)
        self.btn_pvp_online = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y + 70), (w, h)),
            text="Chơi Cờ Tướng (Online)",
            manager=ui_manager
        ) 
        
        # Nút Quay lại
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x, y + 140), (w, h)),
            text="Quay lại Menu Chính",
            manager=ui_manager
        )

        # Mặc định ẩn đi
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
                return 'BACK_TO_MAIN' # Tín hiệu quay lại
            
            if event.ui_element == self.btn_pve:
                return 'PLAY_OFFLINE' # Tín hiệu chơi với máy/tại chỗ
            
            if event.ui_element == self.btn_pvp_online:
                return 'PLAY_ONLINE'  # Tín hiệu mở menu Online
                
        return None