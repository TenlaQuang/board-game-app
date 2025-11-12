# ui/menu.py (Phiên bản MỚI, có .show() và .hide())
import pygame
import pygame_gui
from utils.constants import WIDTH

class MainMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager

        # Kích thước và vị trí nút
        button_width = 250
        button_height = 60
        x_pos = (WIDTH - button_width) // 2 # Căn giữa

        # self.button_list dùng để quản lý ẩn/hiện
        self.button_list = [] 

        # --- Duay lai các nút bấm ban đầu ---
        self.chess_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 200), (button_width, button_height)),
            text='Chơi Cờ Vua', 
            manager=self.ui_manager,
            object_id='#chess_button'
        )
        self.button_list.append(self.chess_button)

        self.xiangqi_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 280), (button_width, button_height)), # Cách 80px
            text='Chơi Cờ Tướng', 
            manager=self.ui_manager,
            object_id='#xiangqi_button'
        )
        self.button_list.append(self.xiangqi_button)

        self.server_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 360), (button_width, button_height)),
            text='Bật Server (Host)',
            manager=self.ui_manager,
            object_id='#server_button'
        )
        self.button_list.append(self.server_button)
        
        # (Tôi thêm lại nút Thoát để dễ sử dụng)
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 440), (button_width, button_height)),
            text='Thoát Game',
            manager=self.ui_manager,
            object_id='#quit_button'
        )
        self.button_list.append(self.quit_button)

        # Mặc định là KHÔNG hiện, window.py sẽ gọi .show()
        self.hide() 

    def handle_events(self, event):
        """Xử lý input và trả về trạng thái tiếp theo"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.chess_button:
                return 'PLAY_CHESS' # Tín hiệu mở menu cờ vua
            if event.ui_element == self.xiangqi_button:
                return 'PLAY_XIANGQI' # Tín hiệu mở menu cờ tướng
            if event.ui_element == self.server_button:
                print("Bật server...")
                return 'HOST_GAME' # (Sẽ xử lý sau)
            if event.ui_element == self.quit_button:
                return 'QUIT'
        return None

    def hide(self):
        """Ẩn tất cả các nút của menu này."""
        for button in self.button_list:
            button.hide()

    def show(self):
        """Hiện tất cả các nút của menu này."""
        for button in self.button_list:
            button.show()