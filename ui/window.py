import pygame
import pygame_gui
import queue 

from pygame_gui.elements import UILabel, UISelectionList, UIButton, UITextEntryBox
from pygame_gui.windows import UIConfirmationDialog, UIMessageWindow

from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)

from core.board import Board 
from core.game_state import GameState
from core.move_validator import MoveValidator

from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu      
from .xiangqi_menu import XiangqiMenu 
from .animated_background import AnimatedBackground

from ui.assets import (
    load_assets, 
    CHESS_PIECES, XIANGQI_PIECES, 
    MAIN_MENU_BACKGROUND 
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from network.network_manager import NetworkManager


class App:
    def __init__(self, network_manager: 'NetworkManager', server_ip: str, server_port: int):
        """Khởi tạo toàn bộ ứng dụng."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- 1. Thiết lập mạng ---
        self.network = network_manager
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = None 
        self.my_role = None 
        self.opponent_username = None
        self.invite_from = None 

        # --- 2. Tải tài nguyên ---
        load_assets() 

        # --- 3. Khởi tạo UI Manager ---
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # --- 4. Tạo các "màn hình" (Scenes) ---
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        self.login_label = None
        self.login_text_entry = None
        self.login_button = None
        self.login_back_button = None
        self.lobby_label = None
        self.lobby_player_list = None
        self.lobby_invite_button = None
        self.lobby_back_button = None
        self.game_screen: BoardUI | None = None
        self.game_logic: Board | None = None
        self.connecting_popup = None
        self.invite_confirm_dialog = None
        
        self.chess_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80, scroll_speed=120, 
            light_color=LIGHT_SQUARE_COLOR, dark_color=DARK_SQUARE_COLOR
        )
        self.xiangqi_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80, scroll_speed=150,
            light_color=XIANGQI_LIGHT_BACKGROUND_COLOR, dark_color=XIANGQI_DARK_BACKGROUND_COLOR
        )
        
        # --- SỬA LỖI 1: Dùng custom_type() để tránh xung đột event với UI ---
        try:
            self.lobby_refresh_timer = pygame.event.custom_type()
        except AttributeError:
            # Fallback cho bản pygame cũ
            self.lobby_refresh_timer = pygame.USEREVENT + 100 

        self.state = 'MAIN_MENU'
        self.main_menu.show() 

    # --- UI HELPERS (Giữ nguyên) ---
    def _show_login_screen(self):
        self.login_label = UILabel(pygame.Rect((WIDTH//2-150, 150), (300, 50)), "Nhap ten cua ban", manager=self.ui_manager)
        self.login_text_entry = UITextEntryBox(pygame.Rect((WIDTH//2-150, 210), (300, 50)), manager=self.ui_manager)
        self.login_button = UIButton(pygame.Rect((WIDTH//2-100, 280), (200, 50)), "Dang Nhap", manager=self.ui_manager)
        self.login_back_button = UIButton(pygame.Rect((WIDTH//2-100, 340), (200, 50)), "Quay Lai", manager=self.ui_manager)

    def _hide_login_screen(self):
        if self.login_label: self.login_label.kill()
        if self.login_text_entry: self.login_text_entry.kill()
        if self.login_button: self.login_button.kill()
        if self.login_back_button: self.login_back_button.kill()
        self.login_label = self.login_text_entry = self.login_button = self.login_back_button = None
    
    def _show_lobby(self):
        self.lobby_label = UILabel(pygame.Rect((WIDTH//2-150, 50), (300, 50)), "Lobby - Online Players", manager=self.ui_manager)
        self.lobby_player_list = UISelectionList(pygame.Rect((WIDTH//2-150, 110), (300, 300)), item_list=[], manager=self.ui_manager)
        self.lobby_invite_button = UIButton(pygame.Rect((WIDTH//2-100, 420), (200, 50)), "Invite to Play", manager=self.ui_manager)
        self.lobby_back_button = UIButton(pygame.Rect((WIDTH//2-100, 480), (200, 50)), "Back to Menu", manager=self.ui_manager)
        self.network.send_to_matchmaker({"type": "get_lobby"})

    def _hide_lobby(self):
        if self.lobby_label: self.lobby_label.kill()
        if self.lobby_player_list: self.lobby_player_list.kill()
        if self.lobby_invite_button: self.lobby_invite_button.kill()
        if self.lobby_back_button: self.lobby_back_button.kill()
        self.lobby_label = self.lobby_player_list = self.lobby_invite_button = self.lobby_back_button = None

    def _show_connecting_popup(self, text: str):
        if self.connecting_popup: self.connecting_popup.kill()
        self.connecting_popup = UIMessageWindow(
            rect=pygame.Rect((WIDTH//2-150, HEIGHT//2-100), (300, 200)),
            html_message=f"<p align='center'>{text}</p>",
            manager=self.ui_manager, window_title="Connecting..."
        )
    
    def _hide_connecting_popup(self):
        if self.connecting_popup: self.connecting_popup.kill(); self.connecting_popup = None

    def _process_network_queues(self):
        # Matchmaker Queue
        try:
            while True:
                server_cmd = self.network.server_queue.get_nowait()
                if server_cmd['type'] == 'invited':
                    self._hide_connecting_popup() 
                    self.invite_from = server_cmd['from']
                    self.invite_confirm_dialog = UIConfirmationDialog(
                        rect=pygame.Rect((WIDTH//2-150, HEIGHT//2-100), (300, 200)),
                        manager=self.ui_manager, window_title="Game Invite",
                        action_long_desc=f"<b>{self.invite_from}</b> wants to play with you!",
                        action_short_name="Accept", blocking=True
                    )
                elif server_cmd['type'] == 'lobby_list':
                    if self.state == 'LOBBY' and self.lobby_player_list:
                        current_items = [item['text'] for item in self.lobby_player_list.item_list]
                        new_items = server_cmd['players']
                        if current_items != new_items: self.lobby_player_list.set_item_list(new_items)
                elif server_cmd['type'] == 'start_game':
                    self.my_role = server_cmd.get('role')
                    self.opponent_username = server_cmd.get('opponent_username', 'Opponent')
                    self.state = 'CONNECTING_P2P'
                    self._hide_lobby()
                    self._hide_connecting_popup() 
                    pygame.time.set_timer(self.lobby_refresh_timer, 0) 
                    self._show_connecting_popup(f"Connecting to {self.opponent_username}...")
                elif server_cmd['type'] == 'p2p_waiting':
                    self._show_connecting_popup("Waiting for opponent to connect...")
                elif server_cmd['type'] == 'p2p_connected':
                    self._hide_connecting_popup()
                    self.state = 'GAME_SCREEN'
                    self.game_logic = Board(game_type='chess') 
                    self.game_screen = BoardUI(self.screen, self.game_logic, CHESS_PIECES)
                    print(f"GAME START! My role: {self.my_role}")
                elif server_cmd['type'] == 'p2p_error':
                    self.state = 'LOBBY'
                    self._hide_connecting_popup()
                    self._show_lobby()
                    pygame.time.set_timer(self.lobby_refresh_timer, 3000)
                elif server_cmd['type'] == 'disconnect':
                    print("Lost connection to server")
                    self.running = False
        except queue.Empty: pass 

        # P2P Queue
        if self.state == 'GAME_SCREEN' and self.game_logic:
            try:
                while True:
                    p2p_cmd = self.network.p2p_queue.get_nowait()
                    if p2p_cmd['type'] == 'move':
                        print(f"Opponent move: {p2p_cmd}") # TODO: Implement move
                    elif p2p_cmd['type'] == 'disconnect':
                        self.state = 'LOBBY'
                        self.game_screen = None; self.game_logic = None
                        self._show_lobby()
                        pygame.time.set_timer(self.lobby_refresh_timer, 3000)
            except queue.Empty: pass 

    # --- HÀM RUN QUAN TRỌNG (ĐÃ SỬA) ---
    def run(self):
        """Vòng lặp game chính."""
        while self.running:
            time_delta = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    continue

                # 1. Xử lý Timer (Mạng)
                if event.type == self.lobby_refresh_timer:
                    if self.state == 'LOBBY':
                        self.network.send_to_matchmaker({"type": "get_lobby"})
                    continue # Bỏ qua các xử lý UI cho sự kiện này

                # 2. Đưa sự kiện cho UI Manager (QUAN TRỌNG: Phải chạy trước logic nút bấm)
                self.ui_manager.process_events(event)
                
                # 3. Xử lý Logic Nút bấm của App (Login/Lobby)
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.login_button:
                        username = self.login_text_entry.get_text()
                        if username:
                            self.username = username; self.state = 'CONNECTING_MATCHMAKER'; self._hide_login_screen()
                    elif event.ui_element == self.login_back_button:
                        self.state = 'MAIN_MENU'; self._hide_login_screen(); self.main_menu.show()
                    elif event.ui_element == self.lobby_invite_button:
                        selected = self.lobby_player_list.get_single_selection()
                        if selected:
                            self.network.send_to_matchmaker({"type": "invite", "target": selected})
                            self._show_connecting_popup(f"Inviting {selected}...")
                    elif event.ui_element == self.lobby_back_button:
                        self.state = 'MAIN_MENU'; self._hide_lobby(); self.main_menu.show()
                        pygame.time.set_timer(self.lobby_refresh_timer, 0)
                        try: self.network.shutdown()
                        except: pass

                # 4. Xử lý Confirm Dialog
                if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if event.ui_element == self.invite_confirm_dialog:
                        self.network.send_to_matchmaker({"type": "accept", "target": self.invite_from})
                        self._show_connecting_popup(f"Accepting invite from {self.invite_from}...")
                        self.invite_confirm_dialog = None
                
                # 5. Chuyển sự kiện cho các Menu con (Main Menu, Chess Menu...)
                if self.state == 'MAIN_MENU':
                    next_state = self.main_menu.handle_events(event)
                    if next_state == 'QUIT': self.running = False
                    elif next_state == 'PLAY_CHESS':
                        self.main_menu.hide(); self.chess_menu.show(); self.state = 'CHESS_MENU'
                    elif next_state == 'PLAY_XIANGQI':
                        self.main_menu.hide(); self.xiangqi_menu.show(); self.state = 'XIANGQI_MENU'
                    elif next_state == 'PLAY_ONLINE': 
                        self.main_menu.hide(); self.state = 'LOGIN_SCREEN'; self._show_login_screen() 

                elif self.state == 'CHESS_MENU':
                    next_state = self.chess_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.chess_menu.hide(); self.main_menu.show(); self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_CHESS_QUICK':
                        self.chess_menu.hide()
                        self.game_logic = Board(game_type='chess') 
                        self.game_screen = BoardUI(self.screen, self.game_logic, CHESS_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'XIANGQI_MENU':
                    next_state = self.xiangqi_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.xiangqi_menu.hide(); self.main_menu.show(); self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_XIANGQI_QUICK':
                        self.xiangqi_menu.hide()
                        self.game_logic = Board(game_type='chinese_chess')
                        self.game_screen = BoardUI(self.screen, self.game_logic, XIANGQI_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'GAME_SCREEN' and self.game_screen:
                    self.game_screen.handle_events(event) 

            # --- CẬP NHẬT UI (NẰM NGOÀI VÒNG LẶP FOR - QUAN TRỌNG) ---
            self._process_network_queues()
            
            # Hàm này giúp nút bấm "sáng lên" khi di chuột
            self.ui_manager.update(time_delta) 
            
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.update(time_delta)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.update(time_delta)
            
            # Logic Connect (Non-blocking để UI không bị đơ)
            elif self.state == 'CONNECTING_MATCHMAKER':
                self._show_connecting_popup(f"Connecting... {self.username}")
                if self.network.connect_to_matchmaker(self.server_ip, self.server_port, self.username):
                    self.state = 'LOBBY'
                    self._hide_connecting_popup()
                    self._show_lobby()
                    pygame.time.set_timer(self.lobby_refresh_timer, 3000)
                else:
                    self.state = 'LOGIN_SCREEN'
                    self._hide_connecting_popup()
                    self._show_login_screen()

            # --- VẼ HÌNH ---
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND: self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else: self.screen.fill((20, 20, 20))
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.draw(self.screen)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.draw(self.screen)
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw()
            elif self.state in ['LOGIN_SCREEN', 'LOBBY', 'CONNECTING_MATCHMAKER', 'CONNECTING_P2P']:
                self.screen.fill((50, 50, 50))

            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()
            
        pygame.quit()