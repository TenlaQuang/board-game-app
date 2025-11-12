# ui/window.py (Phiên bản MỚI NHẤT, hỗ trợ đa menu và nền chuyển động)
import pygame
import pygame_gui
from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)
from core import Board 

# Import TẤT CẢ các "cảnh" (scenes) của bạn
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu       # Cảnh menu cờ vua
from .xiangqi_menu import XiangqiMenu # Cảnh menu cờ tướng
from .animated_background import AnimatedBackground # <-- LỚP NỀN CHUYỂN ĐỘNG

# Import TẤT CẢ các tài nguyên
from ui.assets import (
    load_assets, 
    CHESS_PIECES, XIANGQI_PIECES, 
    MAIN_MENU_BACKGROUND # Chỉ cần nền của menu chính
)

class App:
    def __init__(self):
        """Khởi tạo toàn bộ ứng dụng."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        # 1. Tải tất cả tài nguyên (ảnh nút, ảnh quân cờ, nền menu chính)
        load_assets() 

        # 2. Khởi tạo UI Manager
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # 3. Tạo TẤT CẢ các "màn hình" của game
        # Các màn hình này sẽ được ẩn/hiện khi cần
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)
        
        self.game_screen = None # Màn hình game chỉ được tạo khi vào trận

        # --- 4. TẠO CÁC NỀN CHUYỂN ĐỘNG ---
        self.chess_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80,      # Kích thước ô vuông
            scroll_speed=120,    # Tốc độ (đã sửa cho mượt)
            light_color=LIGHT_SQUARE_COLOR, # Tên tham số đúng
            dark_color=DARK_SQUARE_COLOR  # Tên tham số đúng
        )
        
        self.xiangqi_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80,      # Kích thước ô vuông (bằng nhau)
            scroll_speed=150,    # Tốc độ (đã sửa cho mượt)
            light_color=XIANGQI_LIGHT_BACKGROUND_COLOR, # Tên tham số đúng
            dark_color=XIANGQI_DARK_BACKGROUND_COLOR  # Tên tham số đúng
        )
        # ------------------------------------

        # 5. Đặt trạng thái game ban đầu (FIX LỖI)
        self.state = 'MAIN_MENU'
        self.main_menu.show() # Chỉ hiện menu chính lúc đầu

    def run(self):
        """Vòng lặp game chính (State Machine)."""
        while self.running:
            # 1. Lấy time_delta (quan trọng cho FPS cao)
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # --- 2. XỬ LÝ SỰ KIỆN ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Đưa sự kiện cho UI Manager
                self.ui_manager.process_events(event)
                
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
                    # TODO: Xử lý 'HOST_GAME', 'JOIN_GAME'

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
                    # TODO: Thêm logic quay lại menu

            # --- 3. CẬP NHẬT LOGIC ---
            self.ui_manager.update(time_delta)
            
            # Cập nhật nền chuyển động (nếu đang ở state đó)
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.update(time_delta) # Update nền Cờ Vua
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.update(time_delta) # Update nền Cờ Tướng

            # --- 4. VẼ LÊN MÀN HÌNH ---
            
            # 4a. Vẽ nền (background) tùy theo state
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND:
                    self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else:
                    self.screen.fill((20, 20, 20)) # Nền đen mặc định
            
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.draw(self.screen) # Vẽ nền Cờ Vua
            
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.draw(self.screen) # Vẽ nền Cờ Tướng

            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw() # BoardUI tự vẽ nền

            # 4b. Vẽ các nút UI (luôn ở trên cùng)
            self.ui_manager.draw_ui(self.screen)
            
            # 4c. Cập nhật màn hình
            pygame.display.flip()
            
        pygame.quit()