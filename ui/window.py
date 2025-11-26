# ui/window.py
import threading
import pygame
import pygame_gui
import os 
from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)
from core.board import Board 

# --- IMPORT SCENES ---
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu      
from .xiangqi_menu import XiangqiMenu 
from .animated_background import AnimatedBackground
from network import web_matchmaking
try:
    from .online_menu import OnlineMenu
except ImportError:
    OnlineMenu = None

from ui.assets import load_assets, CHESS_PIECES, XIANGQI_PIECES

class App:
    def __init__(self, network_manager, server_ip, server_port):
        self.network_manager = network_manager
        self.server_ip = server_ip
        self.server_port = server_port
        web_matchmaking.wake_up_server()
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        load_assets()
        # Nạp theme.json
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')

        # --- 1. TẢI HÌNH NỀN TRỰC TIẾP (MAIN MENU) ---
        try:
            bg_path = os.path.join("ui", "assets", "images", "background.png")
            if os.path.exists(bg_path):
                self.main_background = pygame.image.load(bg_path)
                self.main_background = pygame.transform.smoothscale(self.main_background, (WIDTH, HEIGHT))
                print("✅ Đã tải hình nền background.png thành công!")
            else:
                print(f"⚠️ CẢNH BÁO: Không tìm thấy file tại {bg_path}")
                self.main_background = None
        except Exception as e:
            print(f"⚠️ LỖI khi tải hình nền: {e}")
            self.main_background = None

        # Initialize Menus
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        self.online_menu = None
        if OnlineMenu:
            self.online_menu = OnlineMenu(self.screen, self.ui_manager, self.network_manager)

        self.game_screen = None
        self.selected_game_type = 'chess' 

        # Backgrounds động (chỉ dùng khi cần hiệu ứng)
        self.chess_bg = AnimatedBackground(WIDTH, HEIGHT, 80, 120, LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)
        self.xiangqi_bg = AnimatedBackground(WIDTH, HEIGHT, 80, 150, XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR)

        self.state = 'MAIN_MENU'
        self.main_menu.show()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT: 
                    self.running = False
                    if self.network_manager: self.network_manager.shutdown()

                self.ui_manager.process_events(event)

                # --- XỬ LÝ LOGIC MENU ---
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
                    elif isinstance(action, tuple) and action[0] == 'PLAY_OFFLINE':
                        _, difficulty = action 
                        self.chess_menu.hide()
                        self._start_game_session('chess', online=False, difficulty=difficulty) 
                    # ----------------------
                    # elif action == 'PLAY_OFFLINE':
                    #     self.chess_menu.hide(); self._start_game_session('chess', online=False) 
                    elif action == 'PLAY_ONLINE':
                        self.chess_menu.hide(); 
                        if self.online_menu: 
                            # 1. Cập nhật cho UI (để hiện đúng tiêu đề, đúng luật)
                            self.online_menu.current_game_type = 'chess'
                            self.online_menu.reset_ui_state()
                            
                            # [THÊM DÒNG NÀY] 2. Cập nhật cho NetworkManager (để báo Server biết mình ở đâu)
                            self.network_manager.current_lobby_state = 'chess' 
                            self.network_manager.force_update()
                            self.online_menu.show(); 
                            self.state = 'ONLINE_MENU'

                elif self.state == 'XIANGQI_MENU':
                    action = self.xiangqi_menu.handle_events(event)
                    if action == 'BACK_TO_MAIN':
                        self.xiangqi_menu.hide(); self.main_menu.show(); self.state = 'MAIN_MENU'
                    elif action == 'PLAY_OFFLINE': 
                        self.xiangqi_menu.hide(); self._start_game_session('chinese_chess', online=False)
                    
                    elif action == 'PLAY_ONLINE': 
                        self.xiangqi_menu.hide(); 
                        if self.online_menu: 
                            # 1. Cập nhật cho UI
                            self.online_menu.current_game_type = 'chinese_chess'
                            self.online_menu.reset_ui_state()
                            
                            # [THÊM DÒNG NÀY] 2. Cập nhật cho NetworkManager (QUAN TRỌNG)
                            self.network_manager.current_lobby_state = 'chinese_chess'
                            self.network_manager.force_update()
                            self.online_menu.show(); 
                            self.state = 'ONLINE_MENU'

                elif self.state == 'ONLINE_MENU':
                    if self.online_menu:
                        self.online_menu.current_game_type = self.selected_game_type
                        self.network_manager.current_lobby_state = self.selected_game_type
                        
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
                        action = self.game_screen.handle_events(event)
                        if action == 'QUIT_GAME':
                            if self.network_manager:
                                self.network_manager.reset_connection()
                            self.game_screen = None
                            self.main_menu.show()
                            self.state = 'MAIN_MENU'

            # --- VẼ GIAO DIỆN (DRAW) ---
            self.ui_manager.update(time_delta)
            
            # [THÊM ĐOẠN NÀY VÀO ĐÂY] =====================================
            # Gọi hàm update của OnlineMenu để tính toán góc xoay spinner
            if self.online_menu:
                self.online_menu.update(time_delta)
            # =============================================================
            
            if self.state == 'MAIN_MENU':
                # 1. Vẽ nền Main Menu
                if self.main_background: 
                    self.screen.blit(self.main_background, (0, 0))
                else: 
                    self.screen.fill((30, 30, 30))
                self.main_menu.draw_custom_effects() 
            
            elif self.state == 'CHESS_MENU':
                # --- ĐOẠN ĐÃ SỬA ---
                # CŨ: self.chess_bg.update(time_delta); self.chess_bg.draw(self.screen)
                # MỚI: Gọi hàm draw của menu để vẽ ảnh tĩnh poster
                self.chess_menu.draw()

            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu.draw()
            
            elif self.state == 'ONLINE_MENU':
                self.screen.fill((20, 25, 40))
            
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                # (Tùy chọn) Nếu bạn muốn nền động KHI CHƠI GAME, 
                # bạn có thể bật dòng này lên trước khi vẽ game_screen:
                # if self.selected_game_type == 'chess':
                #     self.chess_bg.update(time_delta)
                #     self.chess_bg.draw(self.screen)
                
                self.game_screen.update() 
                self.game_screen.draw()

            # Vẽ các thành phần UI khác (nút trong suốt, chữ,...) đè lên trên
            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()

        self.network_manager.shutdown()
        pygame.quit()

    # Thêm tham số difficulty=None vào hàm
    def _start_game_session(self, game_type, online=False, difficulty=None):
        pieces_img = CHESS_PIECES if game_type == 'chess' else XIANGQI_PIECES
        game_logic = Board(game_type=game_type) 
        net_mgr = None
        role = None
        
        # --- [THÊM] KHỞI TẠO AI ---
        ai_engine = None
        if not online and difficulty and game_type == 'chess':
            try:
                from ai.engines.stockfish_adapter import StockfishAdapter
                ai_engine = StockfishAdapter(difficulty)
                print(f"✅ Đã tải AI Stockfish: Mức {difficulty}")
            except Exception as e:
                print(f"❌ Lỗi tải AI: {e}")
        # --------------------------
        # Chỉ cần là offline và là cờ tướng -> Load luôn CustomBot
        if not online and game_type == 'chinese_chess':
            try:
                from ai.custom_bot import CustomXiangqiBot
                # Load file model bạn đã train
                ai_engine = CustomXiangqiBot(model_path="ai/weights/xiangqi_model.pth")
                print(f"✅ Đã tải AI Cờ Tướng Tự Train!")
            except Exception as e:
                print(f"❌ Lỗi tải AI Cờ Tướng: {e}")
                import traceback
                traceback.print_exc() # In lỗi chi tiết để dễ sửa

        # --------------------------

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
            board_rect=board_rect,          
            sidebar_rect=sidebar_rect, 
            network_manager=net_mgr,
            my_role=role,
            ai_engine=ai_engine  # <--- TRUYỀN AI VÀO ĐÂY
        )
        self.state = 'GAME_SCREEN'