import threading
import pygame
import pygame_gui
from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)
from core import Board

# Import các Scene
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu      
from .xiangqi_menu import XiangqiMenu 
from .animated_background import AnimatedBackground
from core.game_state import GameState

try:
    from .online_menu import OnlineMenu
except ImportError:
    OnlineMenu = None

from ui.assets import load_assets, CHESS_PIECES, XIANGQI_PIECES, MAIN_MENU_BACKGROUND

class App:
    def __init__(self, network_manager, server_ip, server_port):
        self.network_manager = network_manager
        self.server_ip = server_ip
        self.server_port = server_port

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        load_assets()
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')

        # Khởi tạo các Menu
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        self.online_menu = None
        if OnlineMenu:
            self.online_menu = OnlineMenu(self.screen, self.ui_manager, self.network_manager)

        self.game_screen = None
        self.selected_game_type = 'chess' 

        # Backgrounds
        self.chess_bg = AnimatedBackground(WIDTH, HEIGHT, 80, 120, LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)
        self.xiangqi_bg = AnimatedBackground(WIDTH, HEIGHT, 80, 150, XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR)

        self.state = 'MAIN_MENU'
        self.main_menu.show()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT: self.running = False
                self.ui_manager.process_events(event)

                if self.state == 'MAIN_MENU':
                    action = self.main_menu.handle_events(event)
                    if action == 'QUIT': self.running = False
                    elif action == 'GOTO_CHESS_MENU':
                        self.main_menu.hide(); self.chess_menu.show(); self.selected_game_type = 'chess'; self.state = 'CHESS_MENU'
                    elif action == 'GOTO_XIANGQI_MENU':
                        self.main_menu.hide(); self.xiangqi_menu.show(); self.selected_game_type = 'chinese_chess'; self.state = 'XIANGQI_MENU'

                elif self.state == 'CHESS_MENU':
                    action = self.chess_menu.handle_events(event)
                    if action == 'BACK_TO_MAIN':
                        self.chess_menu.hide(); self.main_menu.show(); self.state = 'MAIN_MENU'
                    elif action == 'PLAY_OFFLINE':
                        self.chess_menu.hide(); self._start_game_session('chess', online=False) 
                    elif action == 'PLAY_ONLINE':
                        self.chess_menu.hide(); 
                        if self.online_menu: self.online_menu.show(); self.state = 'ONLINE_MENU'

                elif self.state == 'XIANGQI_MENU':
                    action = self.xiangqi_menu.handle_events(event)
                    if action == 'BACK_TO_MAIN':
                        self.xiangqi_menu.hide(); self.main_menu.show(); self.state = 'MAIN_MENU'
                    elif action == 'PLAY_OFFLINE': 
                        self.xiangqi_menu.hide(); self._start_game_session('chinese_chess', online=False)
                    elif action == 'PLAY_ONLINE': 
                        self.xiangqi_menu.hide(); 
                        if self.online_menu: self.online_menu.show(); self.state = 'ONLINE_MENU'

                elif self.state == 'ONLINE_MENU':
                    if self.online_menu:
                        self.online_menu.current_game_type = self.selected_game_type
                        action = self.online_menu.handle_events(event)
                        
                        if action == 'BACK':
                            self.online_menu.hide()
                            if self.selected_game_type == 'chess': self.chess_menu.show(); self.state = 'CHESS_MENU'
                            else: self.xiangqi_menu.show(); self.state = 'XIANGQI_MENU'
                        
                        if self.network_manager.p2p_socket:
                            print(f">>> VÀO GAME ONLINE ({self.selected_game_type}) <<<")
                            self.online_menu.hide()
                            self._start_game_session(self.selected_game_type, online=True)

                elif self.state == 'GAME_SCREEN':
                    if self.game_screen:
                        self.game_screen.handle_events(event)

            self.ui_manager.update(time_delta)
            
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND: self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else: self.screen.fill((30, 30, 30))
            elif self.state == 'CHESS_MENU':
                self.chess_bg.update(time_delta); self.chess_bg.draw(self.screen)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_bg.update(time_delta); self.xiangqi_bg.draw(self.screen)
            elif self.state == 'ONLINE_MENU':
                self.screen.fill((20, 25, 40))
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update() 
                self.game_screen.draw()

            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()

        self.network_manager.shutdown()
        pygame.quit()

    def _start_game_session(self, game_type, online=False):
        pieces_img = CHESS_PIECES if game_type == 'chess' else XIANGQI_PIECES
        
        # --- [FIX] SỬ DỤNG GAMESTATE THAY VÌ BOARD ---
        # GameState sẽ quản lý cả Board và Lượt đi (current_turn)
        game_logic = GameState(game_type=game_type) 
        # ---------------------------------------------
        
        net_mgr = None
        role = None
        
        if online:
            net_mgr = self.network_manager
            role = 'host' if self.network_manager.is_host else 'client'
        
        SIDEBAR_WIDTH = 320
        BOARD_WIDTH = WIDTH - SIDEBAR_WIDTH
        
        board_rect = pygame.Rect(0, 0, BOARD_WIDTH, HEIGHT)
        sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
        
        self.game_screen = BoardUI(
            self.screen, 
            game_logic, 
            pieces_img, 
            board_rect, 
            sidebar_rect=sidebar_rect,
            network_manager=net_mgr,
            my_role=role
        )
        self.state = 'GAME_SCREEN'