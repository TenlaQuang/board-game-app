# ui/chess_menu.py
import pygame
import pygame_gui
from utils.constants import WIDTH

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        w, h = 250, 50
        x = (WIDTH - w) // 2
        y = 200

        self.btn_pve = pygame_gui.elements.UIButton(pygame.Rect((x, y), (w, h)), "Chơi với Máy (PvE)", ui_manager)
        self.btn_pvp_online = pygame_gui.elements.UIButton(pygame.Rect((x, y+70), (w, h)), "Chơi Online (PvP)", ui_manager) # <--- Nút mới
        self.btn_back = pygame_gui.elements.UIButton(pygame.Rect((x, y+140), (w, h)), "Quay lại", ui_manager)

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
                return 'PLAY_ONLINE' # <--- Tín hiệu mới
        return None