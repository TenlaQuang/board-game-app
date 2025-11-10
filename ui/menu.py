# Trong ui/menu.py
import pygame
import pygame_gui

class MainMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager

        # Tọa độ và kích thước
        button_width = 200
        button_height = 50
        x_pos = (screen.get_width() - button_width) // 2
        
        # Tạo các nút bấm bằng pygame_gui
        self.host_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 200), (button_width, button_height)),
            text='Host Game (P2P)',
            manager=self.ui_manager,
            object_id='#host_button' # Dùng để styling trong theme.json
        )
        
        self.join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 270), (button_width, button_height)),
            text='Join Game (P2P)',
            manager=self.ui_manager
        )
        
        self.offline_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 340), (button_width, button_height)),
            text='Play Offline',
            manager=self.ui_manager
        )
        # ... (thêm nút Quit) ...

    def handle_events(self, event):
        """Xử lý input và trả về trạng thái tiếp theo."""
        
        # pygame-gui có cách xử lý sự kiện riêng
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.host_button:
                print("Host button clicked!")
                return 'HOST_GAME'
            if event.ui_element == self.join_button:
                return 'JOIN_GAME'
            if event.ui_element == self.offline_button:
                return 'PLAY_OFFLINE'
            # ...
        return None

    def draw(self):
        # Bạn không cần code draw nữa!
        # self.ui_manager.draw_ui(self.screen) sẽ làm việc này trong vòng lặp chính
        pass