# ui/menu.py
import pygame
import pygame_gui
from utils.constants import WIDTH

class MainMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager

        # Layout
        button_width = 250
        button_height = 60
        x_pos = (WIDTH - button_width) // 2
        start_y = 250

        self.button_list = []

        # Nút Cờ Vua
        self.btn_chess = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, start_y), (button_width, button_height)),
            text='Cờ Vua',
            manager=self.ui_manager
        )
        self.button_list.append(self.btn_chess)

        # Nút Cờ Tướng
        self.btn_xiangqi = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, start_y + 80), (button_width, button_height)),
            text='Cờ Tướng',
            manager=self.ui_manager
        )
        self.button_list.append(self.btn_xiangqi)
        
        # Nút Thoát
        self.btn_quit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((x_pos, start_y + 160), (button_width, button_height)),
            text='Thoát',
            manager=self.ui_manager
        )
        self.button_list.append(self.btn_quit)

        self.hide()

    def show(self):
        for btn in self.button_list: btn.show()

    def hide(self):
        for btn in self.button_list: btn.hide()

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_chess:
                return 'GOTO_CHESS_MENU'
            if event.ui_element == self.btn_xiangqi:
                return 'GOTO_XIANGQI_MENU'
            if event.ui_element == self.btn_quit:
                return 'QUIT'
        return None