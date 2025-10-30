# ui/menu.py
import pygame
import pygame_gui
from utils.constants import WIDTH, HEIGHT # Cần để căn giữa nút bấm

class MainMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager

        # Tọa độ và kích thước nút
        button_width = 250
        button_height = 60
        x_pos = (WIDTH - button_width) // 2 # Dùng WIDTH từ constants

        # Tạo các nút bấm
        self.play_chess_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 200), (button_width, button_height)),
            text='Play Chess Offline',
            manager=self.ui_manager,
            object_id='#play_chess_button'
        )
        
        self.play_xiangqi_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 280), (button_width, button_height)), # Cách 80px
            text='Play Xiangqi Offline',
            manager=self.ui_manager,
            object_id='#play_xiangqi_button'
        )

        self.host_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 360), (button_width, button_height)),
            text='Tạo Phòng (P2P)',
            manager=self.ui_manager,
            object_id='#host_button'
        )
        
        self.join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 440), (button_width, button_height)),
            text='Vào Phòng (P2P)',
            manager=self.ui_manager,
            object_id='#join_button'
        )
        
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 520), (button_width, button_height)),
            text='Thoát Game',
            manager=self.ui_manager,
            object_id='#quit_button'
        )

    def handle_events(self, event):
        """Xử lý input và trả về trạng thái tiếp theo."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_chess_button:
                print("Chơi Cờ Vua Offline!")
                self.hide() # Ẩn các nút menu khi chuyển cảnh
                return 'PLAY_CHESS'
            if event.ui_element == self.play_xiangqi_button:
                print("Chơi Cờ Tướng Offline!")
                self.hide() # Ẩn các nút menu khi chuyển cảnh
                return 'PLAY_XIANGQI'
            if event.ui_element == self.host_button:
                print("Tạo phòng clicked!")
                self.hide()
                return 'HOST_GAME'
            if event.ui_element == self.join_button:
                print("Vào phòng clicked!")
                self.hide()
                return 'JOIN_GAME'
            if event.ui_element == self.quit_button:
                print("Thoát game clicked!")
                return 'QUIT'
        return None

    def hide(self):
        """Ẩn tất cả các nút của menu này."""
        self.play_chess_button.hide()
        self.play_xiangqi_button.hide()
        self.host_button.hide()
        self.join_button.hide()
        self.quit_button.hide()

    def show(self):
        """Hiện tất cả các nút của menu này."""
        self.play_chess_button.show()
        self.play_xiangqi_button.show()
        self.host_button.show()
        self.join_button.show()
        self.quit_button.show()