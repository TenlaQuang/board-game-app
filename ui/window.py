# ui/window.py (Phiên bản MỚI NHẤT, hỗ trợ đa menu, nền chuyển động VÀ MẠNG)
import pygame
import pygame_gui
import queue # <-- NEW: Import queue để đọc dữ liệu mạng

from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)
# MODIFIED: Import đầy đủ
from core.board import Board 
from core.game_state import GameState
from core.move_validator import MoveValidator

# Import TẤT CẢ các "cảnh" (scenes) của bạn
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu      # Cảnh menu cờ vua
from .xiangqi_menu import XiangqiMenu # Cảnh menu cờ tướng
from .animated_background import AnimatedBackground # LỚP NỀN CHUYỂN ĐỘNG

# Import TẤT CẢ các tài nguyên
from ui.assets import (
    load_assets, 
    CHESS_PIECES, XIANGQI_PIECES, 
    MAIN_MENU_BACKGROUND 
)

# NEW: Import NetworkManager (chỉ để type hinting)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from network.network_manager import NetworkManager


class App:
    # MODIFIED: __init__ nhận NetworkManager và thông tin server
    def __init__(self, network_manager: 'NetworkManager', server_ip: str, server_port: int, username: str):
        """Khởi tạo toàn bộ ứng dụng."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- 1. NEW: Thiết lập mạng ---
        self.network = network_manager
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username
        self.my_role = None # Sẽ là 'host' hoặc 'client' khi vào game
        self.opponent_username = None
        self.invite_from = None # Lưu tên người mời bạn

        # --- 2. Tải tài nguyên ---
        load_assets() 

        # --- 3. Khởi tạo UI Manager ---
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # --- 4. Tạo TẤT CẢ các "màn hình" của game ---
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        # NEW: Giao diện cho Lobby
        self.lobby_label = None
        self.lobby_player_list = None
        self.lobby_invite_button = None
        self.lobby_back_button = None

        # NEW: Màn hình game
        self.game_screen: BoardUI | None = None # Màn hình game
        self.game_logic: Board | None = None # Logic game

        # NEW: Cửa sổ pop-up
        self.connecting_popup = None
        self.invite_confirm_dialog = None
        
        # --- 5. TẠO CÁC NỀN CHUYỂN ĐỘNG ---
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
        # ------------------------------------

        # --- 6. Đặt trạng thái game ban đầu ---
        self.state = 'MAIN_MENU'
        self.main_menu.show() # Chỉ hiện menu chính lúc đầu

    # ---
    # NEW: CÁC HÀM QUẢN LÝ UI MẠNG
    # ---
    
    def _show_lobby(self):
        """Hiển thị giao diện Lobby."""
        self.lobby_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, 50), (300, 50)),
            text="Lobby - Online Players", manager=self.ui_manager
        )
        self.lobby_player_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, 110), (300, 300)),
            item_list=[], manager=self.ui_manager
        )
        self.lobby_invite_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, 420), (200, 50)),
            text="Invite to Play", manager=self.ui_manager
        )
        self.lobby_back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH // 2 - 100, 480), (200, 50)),
            text="Back to Menu", manager=self.ui_manager
        )
        # Yêu cầu server cập nhật danh sách
        self.network.send_to_matchmaker({"type": "get_lobby"})

    def _hide_lobby(self):
        """Ẩn giao diện Lobby."""
        if self.lobby_label: self.lobby_label.kill()
        if self.lobby_player_list: self.lobby_player_list.kill()
        if self.lobby_invite_button: self.lobby_invite_button.kill()
        if self.lobby_back_button: self.lobby_back_button.kill()
        self.lobby_label = self.lobby_player_list = self.lobby_invite_button = self.lobby_back_button = None

    def _show_connecting_popup(self, text: str):
        """Hiển thị pop-up chờ (không có nút)."""
        if self.connecting_popup: self.connecting_popup.kill()
        self.connecting_popup = pygame_gui.windows.UIMessageWindow(
            rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 100), (300, 200)),
            html_message=f"<p align='center'>{text}</p>",
            manager=self.ui_manager, window_title="Connecting..."
        )
    
    def _hide_connecting_popup(self):
        if self.connecting_popup:
            self.connecting_popup.kill()
            self.connecting_popup = None

    # ---
    # NEW: HÀM XỬ LÝ MẠNG (QUEUE)
    # ---

    def _process_network_queues(self):
        """Xử lý các hàng đợi mạng (không chặn)."""
        
        # 1. Hàng đợi Server "Mai Mối" (Lobby, Mời)
        try:
            server_cmd = self.network.server_queue.get_nowait()
            
            if server_cmd['type'] == 'invited':
                self.invite_from = server_cmd['from']
                self.invite_confirm_dialog = pygame_gui.windows.UIConfirmationDialog(
                    rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 100), (300, 200)),
                    manager=self.ui_manager,
                    window_title="Game Invite",
                    action_long_desc=f"<b>{self.invite_from}</b> wants to play with you!",
                    action_short_name="Accept",
                    blocking=True
                )
            
            elif server_cmd['type'] == 'lobby_list':
                if self.state == 'LOBBY' and self.lobby_player_list:
                    self.lobby_player_list.set_item_list(server_cmd['players'])

            elif server_cmd['type'] == 'start_game':
                # Server ra lệnh Start Game, đã được xử lý tự động bởi NetworkManager
                # NetworkManager sẽ gọi _initiate_p2p_connection
                self.my_role = server_cmd.get('role')
                # Cập nhật UI
                if self.my_role == 'host':
                    self.opponent_username = server_cmd.get('opponent_username', 'Client') # Sẽ được cập nhật sau
                else: # role == 'client'
                    self.opponent_username = server_cmd.get('opponent_username', 'Host')

                self.state = 'CONNECTING_P2P'
                self._hide_lobby()
                self._show_connecting_popup(f"Connecting to {self.opponent_username}...")

            elif server_cmd['type'] == 'p2p_waiting':
                self._show_connecting_popup("Waiting for opponent to connect...")
                
            elif server_cmd['type'] == 'p2p_connected':
                # P2P Thành công!
                self._hide_connecting_popup()
                self.state = 'GAME_SCREEN'
                # NEW: Khởi tạo game
                # (Giả sử bắt đầu với Cờ Vua, bạn cần logic để chọn cờ)
                self.game_logic = Board(game_type='chess')
                self.game_screen = BoardUI(self.screen, self.game_logic, CHESS_PIECES)
                # TODO: Cần logic để biết ai đi trước (ví dụ: host luôn là Trắng)
                print(f"GAME START! My role: {self.my_role}")
                
            elif server_cmd['type'] == 'p2p_error':
                self.state = 'LOBBY'
                self._hide_connecting_popup()
                # TODO: Hiện lỗi cho người dùng
                
            elif server_cmd['type'] == 'disconnect':
                self.running = False # Mất kết nối server
                
        except queue.Empty:
            pass # Không có lệnh gì từ server

        # 2. Hàng đợi P2P (Trong Game)
        if self.state == 'GAME_SCREEN' and self.game_logic:
            try:
                p2p_cmd = self.network.p2p_queue.get_nowait()
                
                if p2p_cmd['type'] == 'move':
                    # Đối thủ gửi nước đi
                    print(f"Opponent move: {p2p_cmd['from']} -> {p2p_cmd['to']}")
                    # TODO: Cần chuyển đổi format 'e2' sang (row, col)
                    # Giả sử self.game_logic.move chấp nhận (from_row, from_col), (to_row, to_col)
                    # from_pos = self.game_screen.convert_notation_to_pos(p2p_cmd['from'])
                    # to_pos = self.game_screen.convert_notation_to_pos(p2p_cmd['to'])
                    
                    # TẠM THỜI DÙNG DỮ LIỆU THÔ (bạn cần hàm chuyển đổi)
                    # self.game_logic.move(from_pos, to_pos) 
                    # self.game_screen.update_board() # Cập nhật UI
                    pass
                    
                elif p2p_cmd['type'] == 'disconnect':
                    self.state = 'LOBBY'
                    self.game_screen = None # Xóa màn hình game
                    self.game_logic = None
                    self._show_lobby()
                    # TODO: Hiện thông báo "Đối thủ ngắt kết nối!"
                    
            except queue.Empty:
                pass # Không có lệnh gì từ P2P

    def run(self):
        """Vòng lặp game chính (State Machine)."""
        while self.running:
            # 1. Lấy time_delta
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # --- 2. XỬ LÝ SỰ KIỆN ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Đưa sự kiện cho UI Manager
                self.ui_manager.process_events(event)
                
                # --- NEW: XỬ LÝ NÚT BẤM CỦA PYGAME_GUI ---
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # Nút trong LOBBY
                    if event.ui_element == self.lobby_invite_button:
                        selected = self.lobby_player_list.get_single_selection()
                        if selected:
                            self.network.send_to_matchmaker({"type": "invite", "target": selected})
                            self._show_connecting_popup(f"Inviting {selected}...")
                    elif event.ui_element == self.lobby_back_button:
                        self.state = 'MAIN_MENU'
                        self._hide_lobby()
                        self.main_menu.show()
                        # TODO: Gửi tin nhắn "rời lobby" cho server?

                # NEW: Xử lý Hộp thoại Xác nhận
                if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if event.ui_element == self.invite_confirm_dialog:
                        # Người dùng bấm "Accept"
                        self.network.send_to_matchmaker({"type": "accept", "target": self.invite_from})
                        self._show_connecting_popup(f"Accepting invite from {self.invite_from}...")
                        self.invite_confirm_dialog = None
                
                # Đưa sự kiện cho "cảnh" (state) hiện tại
                if self.state == 'MAIN_MENU':
                    next_state = self.main_menu.handle_events(event)
                    if next_state == 'QUIT':
                        self.running = False
                    elif next_state == 'PLAY_CHESS':
                        self.main_menu.hide()
                        self.chess_menu.show()
                        self.state = 'CHESS_MENU'
                    elif next_state == 'PLAY_XIANGQI':
                        self.main_menu.hide()
                        self.xiangqi_menu.show()
                        self.state = 'XIANGQI_MENU'
                    # MODIFIED: Xử lý nút "Chơi Online" (Giả sử tên nút là 'PLAY_ONLINE')
                    elif next_state == 'PLAY_ONLINE': 
                        self.main_menu.hide()
                        self.state = 'CONNECTING_MATCHMAKER'

                elif self.state == 'CHESS_MENU':
                    next_state = self.chess_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.chess_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_CHESS_QUICK':
                        self.chess_menu.hide()
                        self.game_logic = Board(game_type='chess') # MODIFIED: Dùng Board
                        self.game_screen = BoardUI(self.screen, self.game_logic, CHESS_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'XIANGQI_MENU':
                    next_state = self.xiangqi_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.xiangqi_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_XIANGQI_QUICK':
                        self.xiangqi_menu.hide()
                        self.game_logic = Board(game_type='chinese_chess') # MODIFIED: Dùng Board
                        self.game_screen = BoardUI(self.screen, self.game_logic, XIANGQI_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'GAME_SCREEN':
                    if self.game_screen:
                        # MODIFIED: Chỉ xử lý click nếu là lượt mình
                        # (Giả sử my_role 'host' là Trắng, 'client' là Đen)
                        # TODO: Bạn cần logic is_my_turn() chuẩn
                        # is_my_turn = (self.my_role == 'host' and self.game_logic.turn == 'white') or \
                        #              (self.my_colw == 'client' and self.game_logic.turn == 'black')
                        is_my_turn = True # TẠM THỜI LUÔN LÀ LƯỢT MÌNH ĐỂ TEST
                        
                        if is_my_turn:
                            move = self.game_screen.handle_events(event) # Lấy nước đi từ UI
                            if move:
                                # move là (from_pos, to_pos)
                                # TODO: Chuyển đổi (row, col) sang 'e2'
                                # from_notation = self.game_screen.convert_pos_to_notation(move[0])
                                # to_notation = self.game_screen.convert_pos_to_notation(move[1])
                                
                                # Gửi nước đi cho đối thủ
                                self.network.send_to_p2p({
                                    "type": "move",
                                    "from": "e2", # Tạm thời
                                    "to": "e4"   # Tạm thời
                                })
                                # TODO: Tắt cờ 'is_my_turn'
                
                # NEW: Các state mạng (không cần xử lý input gì đặc biệt)
                elif self.state == 'LOBBY':
                    pass # Input đã được xử lý bởi UI_BUTTON_PRESSED
                elif self.state == 'CONNECTING_MATCHMAKER':
                    pass # Chờ
                elif self.state == 'CONNECTING_P2P':
                    pass # Chờ
                elif self.state == 'WAITING_FOR_OPPONENT':
                    pass # Chờ

            # --- 3. CẬP NHẬT LOGIC ---
            
            # NEW: XỬ LÝ HÀNG ĐỢI MẠNG (RẤT QUAN TRỌNG)
            self._process_network_queues()

            self.ui_manager.update(time_delta)
            
            # Cập nhật logic của state hiện tại
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.update(time_delta)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.update(time_delta)
            
            # NEW: Logic kết nối ban đầu
            elif self.state == 'CONNECTING_MATCHMAKER':
                self._show_connecting_popup(f"Connecting to Matchmaker as {self.username}...")
                if self.network.connect_to_matchmaker(self.server_ip, self.server_port, self.username):
                    self.state = 'LOBBY'
                    self._hide_connecting_popup()
                    self._show_lobby()
                else:
                    self.state = 'MAIN_MENU' # Quay về menu chính
                    self.main_menu.show()
                    self._hide_connecting_popup()
                    # TODO: Hiển thị lỗi "Không thể kết nối server"

            # --- 4. VẼ LÊN MÀN HÌNH ---
            
            # 4a. Vẽ nền (background) tùy theo state
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND:
                    self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else:
                    self.screen.fill((20, 20, 20))
            
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.draw(self.screen)
            
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.draw(self.screen)

            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw()
            
            # NEW: Nền cho các state mạng (tạm thời là màu xám)
            elif self.state in ['LOBBY', 'CONNECTING_MATCHMAKER', 'CONNECTING_P2P', 'WAITING_FOR_OPPONENT']:
                self.screen.fill((50, 50, 50)) # Nền xám

            # 4b. Vẽ các nút UI (luôn ở trên cùng)
            self.ui_manager.draw_ui(self.screen)
            
            # 4c. Cập nhật màn hình
            pygame.display.flip()
            
        pygame.quit()