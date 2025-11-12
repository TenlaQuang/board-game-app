# ui/chess_menu.py
import pygame
import pygame_gui
# Import ảnh nút Cờ Vua
from .assets import CHESS_BUTTONS 
from utils.constants import WIDTH

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # Lấy ảnh nút (đã được load từ assets.py)
        quick_play_normal = CHESS_BUTTONS.get('quick_play_normal')
        quick_play_hover = CHESS_BUTTONS.get('quick_play_hover')
        
        self.button_list = [] # List để quản lý ẩn/hiện

        # Tạo nút "Quick play" bằng hình ảnh (nếu có)
        if quick_play_normal and quick_play_hover:
            btn_width = quick_play_normal.get_width()
            btn_height = quick_play_normal.get_height()
            x_pos = (WIDTH - btn_width) // 2

            self.quick_play_button = pygame_gui.elements.UIImageButton(
                relative_rect=pygame.Rect((x_pos, 300), (btn_width, btn_height)),
                normal_image=quick_play_normal,
                hovered_image=quick_play_hover,
                manager=self.ui_manager,
                object_id='#image_button' # Dùng chung 1 style cho các nút ảnh
            )
            self.button_list.append(self.quick_play_button)
        else:
            # Tạo nút dự phòng nếu không có ảnh
            print("Cảnh báo (ChessMenu): Không tìm thấy ảnh cho nút 'Quick play'. Dùng nút dự phòng.")
            self.quick_play_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(((WIDTH-300)//2, 300), (300, 70)),
                text='Quick Play (Missing Image)',
                manager=self.ui_manager
            )
            self.button_list.append(self.quick_play_button)
            
        # Nút Quay Lại
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (100, 40)),
            text='< Back',
            manager=self.ui_manager,
            object_id='#back_button'
        )
        self.button_list.append(self.back_button)

        self.hide() # Mặc định ẩn

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.quick_play_button:
                return 'PLAY_CHESS_QUICK' # Tín hiệu để window.py bắt
            if event.ui_element == self.back_button:
                return 'BACK_TO_MAIN_MENU'
        return None

    def hide(self):
        for button in self.button_list:
            button.hide()

    def show(self):
        for button in self.button_list:
            button.show()