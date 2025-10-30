# ui/chess_menu.py
import pygame
import pygame_gui
# from ui.assets import CHESS_BUTTONS # <--- XÓA DÒNG NÀY
from utils.constants import WIDTH

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # # Lấy ảnh nút (nếu load thất bại thì không tạo nút) <-- XÓA CẢ KHỐI NÀY
        # quick_play_normal = CHESS_BUTTONS.get('quick_play_normal')
        # quick_play_hover = CHESS_BUTTONS.get('quick_play_hover')

        self.button_list = []
        
        # if quick_play_normal and quick_play_hover: # <-- XÓA CẢ IF NÀY
        # Lấy kích thước ảnh để căn giữa (bạn có thể tự định nghĩa kích thước)
        btn_width = 250 # Kích thước mặc định của nút UI
        btn_height = 60
        x_pos = (WIDTH - btn_width) // 2

        # Tạo nút UI BÌNH THƯỜNG (thay vì UIImageButton)
        self.quick_play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, 300), (btn_width, btn_height)),
            text='Quick Play', # <-- Thêm text cho nút
            manager=self.ui_manager,
            object_id='#play_chess_quick_button' # <-- Thêm object_id nếu muốn style riêng
        )
        self.button_list.append(self.quick_play_button)
        
        # TODO: Tạo thêm các nút "Play with friend", "Find table" tương tự
        
        # Nút Quay Lại (Dùng UIButton bình thường)
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (100, 40)),
            text='< Back',
            manager=self.ui_manager
        )
        self.button_list.append(self.back_button)

        # Mặc định ẩn menu này đi
        self.hide() 

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.quick_play_button:
                return 'PLAY_CHESS_QUICK' # Tín hiệu để window.py bắt
            if event.ui_element == self.back_button:
                return 'BACK_TO_MAIN_MENU'
        return None

    def hide(self):
        """Ẩn tất cả các nút của menu này."""
        for button in self.button_list:
            button.hide()

    def show(self):
        """Hiện tất cả các nút của menu này."""
        for button in self.button_list:
            button.show()