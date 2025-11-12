# ui/xiangqi_menu.py
import pygame
import pygame_gui
# Import ảnh nút Cờ Tướng
from .assets import XIANGQI_BUTTONS 
from utils.constants import WIDTH

class XiangqiMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # Lấy ảnh nút "Play" (bạn cần tạo file ảnh 'button_play_normal.png'...)
        play_normal = XIANGQI_BUTTONS.get('play_normal')
        play_hover = XIANGQI_BUTTONS.get('play_hover')
        
        self.button_list = [] 

        if play_normal and play_hover:
            btn_width = play_normal.get_width()
            btn_height = play_normal.get_height()
            x_pos = (WIDTH - btn_width) // 2

            self.play_button = pygame_gui.elements.UIImageButton(
                relative_rect=pygame.Rect((x_pos, 550), (btn_width, btn_height)), # Đặt ở vị trí 550
                normal_image=play_normal,
                hovered_image=play_hover,
                manager=self.ui_manager,
                object_id='#image_button'
            )
            self.button_list.append(self.play_button)
        else:
            # Tạo nút dự phòng nếu không có ảnh
            print("Cảnh báo (XiangqiMenu): Không tìm thấy ảnh cho nút 'Play'. Dùng nút dự phòng.")
            self.play_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(((WIDTH-300)//2, 550), (300, 100)),
                text='Play (Missing Image)',
                manager=self.ui_manager
            )
            self.button_list.append(self.play_button)
            
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
            if event.ui_element == self.play_button:
                return 'PLAY_XIANGQI_QUICK'
            if event.ui_element == self.back_button:
                return 'BACK_TO_MAIN_MENU'
        return None

    def hide(self):
        for button in self.button_list:
            button.hide()

    def show(self):
        for button in self.button_list:
            button.show()