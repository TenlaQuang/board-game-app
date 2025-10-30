# ui/window.py (Phiên bản MỚI, hỗ trợ nền chuyển động cho cả 2 loại cờ)
import pygame
import pygame_gui
from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, # Màu bàn cờ vua
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR # Màu nền cờ tướng
)
from core import Board 

# Import TẤT CẢ các "cảnh" (scenes) của bạn
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu
from .xiangqi_menu import XiangqiMenu
from .animated_background import AnimatedBackground # <--- 1. IMPORT LỚP NỀN MỚI

# Import TẤT CẢ các tài nguyên
from ui.assets import (
    load_assets, 
    CHESS_PIECES, XIANGQI_PIECES, 
    MAIN_MENU_BACKGROUND
    # (Không cần import nền chess/xiangqi gradient nữa)
)

class App:
    def __init__(self):
        """Khởi tạo toàn bộ ứng dụng."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        load_assets() # Tải tài nguyên (quân cờ, nút, nền cờ tướng...)

        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # --- TẠO CÁC "MÀN HÌNH" ---
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        self.game_screen = None 

        # --- 3. TẠO CÁC NỀN CHUYỂN ĐỘNG ---
        self.chess_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=100,
            scroll_speed=30, # <--- TĂNG TỪ 20 LÊN 120
            light_color=LIGHT_SQUARE_COLOR,   # <--- SỬA LỖI: 'color_a' -> 'light_color'
            dark_color=DARK_SQUARE_COLOR      # <--- SỬA LỖI: 'color_b' -> 'dark_color'
        )

        self.xiangqi_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=100,
            scroll_speed=30, # <--- TĂNG TỪ 30 LÊN 150
            light_color=XIANGQI_LIGHT_BACKGROUND_COLOR, # <--- SỬA LỖI: 'color_a' -> 'light_color'
            dark_color=XIANGQI_DARK_BACKGROUND_COLOR  # <--- SỬA LỖI: 'color_b' -> 'dark_color'
        ) # <--- ĐÃ SỬA: Thêm dấu ')' bị thiếu

        # --- 4. ĐẶT TRẠNG THÁI BAN ĐẦU (ĐÃ SỬA) ---
        self.state = 'MAIN_MENU'
        self.main_menu.show() # Chỉ hiện menu chính lúc đầu

    def run(self):
        """Vòng lặp game chính (State Machine)."""
        while self.running:
# ... (Phần code còn lại của hàm run() không thay đổi) ...
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # --- 1. XỬ LÝ SỰ KIỆN ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                
                self.ui_manager.process_events(event)
                
                # Xử lý sự kiện dựa trên state
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

                elif self.state == 'CHESS_MENU':
                    next_state = self.chess_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.chess_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_CHESS_QUICK':
                        self.chess_menu.hide()
                        game_logic = Board(game_type='chess')
                        self.game_screen = BoardUI(self.screen, game_logic, CHESS_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'XIANGQI_MENU':
                    next_state = self.xiangqi_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.xiangqi_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_XIANGQI_QUICK':
                        self.xiangqi_menu.hide()
                        game_logic = Board(game_type='chinese_chess')
                        self.game_screen = BoardUI(self.screen, game_logic, XIANGQI_PIECES)
                        self.state = 'GAME_SCREEN'

                elif self.state == 'GAME_SCREEN':
                    if self.game_screen:
                        self.game_screen.handle_events(event)

            # --- 2. CẬP NHẬT LOGIC ---
            self.ui_manager.update(time_delta)
            
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()
            elif self.state == 'CHESS_MENU':
                # Cập nhật nền cờ vua
                self.chess_menu_background_animated.update(time_delta) 
            elif self.state == 'XIANGQI_MENU':
                # Cập nhật nền cờ tướng
                self.xiangqi_menu_background_animated.update(time_delta)

            # --- 3. VẼ LÊN MÀN HÌNH ---
            
            # 3a. Vẽ nền (background) tùy theo state
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND:
                    self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else:
                    self.screen.fill((20, 20, 20)) 
            
            elif self.state == 'CHESS_MENU':
                # Vẽ nền bàn cờ đang cuộn
                self.chess_menu_background_animated.draw(self.screen)
            
            elif self.state == 'XIANGQI_MENU':
                # Vẽ nền ô vuông xanh đang cuộn
                self.xiangqi_menu_background_animated.draw(self.screen)
            
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw() 

            # 3b. Vẽ các nút UI (luôn ở trên cùng)
            self.ui_manager.draw_ui(self.screen)
            
            # 3c. Cập nhật màn hình
            pygame.display.flip()
            
        pygame.quit()

