# ui/window.py
import pygame
import pygame_gui
from .menu import MainMenu
from .board_ui import BoardUI
from ui.assets import load_assets, CHESS_PIECES, XIANGQI_PIECES # Đảm bảo import cả dict assets
from utils.constants import WIDTH, HEIGHT, FPS
from core import Board # Import lớp Board của bạn

class App:
    def __init__(self):
        """Khởi tạo toàn bộ ứng dụng."""
        pygame.init()
        
        # 1. Tạo cửa sổ chính
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        
        # 2. Tạo đồng hồ
        self.clock = pygame.time.Clock()
        self.running = True

        # 3. Tải tất cả tài nguyên (ảnh quân cờ)
        load_assets() # Gọi hàm từ ui/assets.py

        # 4. Khởi tạo UI Manager (cho pygame_gui)
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # 5. Tạo các "màn hình" của game
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.game_screen = None # Màn hình game sẽ được tạo khi chọn loại cờ

        # 6. Đặt trạng thái game ban đầu
        self.state = 'MAIN_MENU'

    def run(self):
        """Vòng lặp game chính."""
        while self.running:
            # 1. Lấy time_delta (quan trọng cho GUI)
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # 2. Xử lý sự kiện (Input từ người dùng)
            events = pygame.event.get()
            for event in events:
                # 2a. Bắt sự kiện QUIT (nhấn nút X)
                if event.type == pygame.QUIT:
                    self.running = False
                
                # 2b. Đưa sự kiện cho UI Manager (luôn xử lý để các nút hoạt động)
                self.ui_manager.process_events(event)
                
                # 2c. Xử lý sự kiện tùy theo trạng thái game hiện tại
                if self.state == 'MAIN_MENU':
                    next_state = self.main_menu.handle_events(event)
                    
                    if next_state == 'QUIT':
                        self.running = False
                    elif next_state == 'PLAY_CHESS':
                        print("Khởi tạo Cờ Vua...")
                        game_logic = Board(game_type='chess')
                        self.game_screen = BoardUI(self.screen, game_logic, CHESS_PIECES)
                        self.state = 'GAME_SCREEN'
                    elif next_state == 'PLAY_XIANGQI':
                        print("Khởi tạo Cờ Tướng...")
                        game_logic = Board(game_type='chinese_chess')
                        self.game_screen = BoardUI(self.screen, game_logic, XIANGQI_PIECES)
                        self.state = 'GAME_SCREEN'
                    # TODO: Xử lý 'HOST_GAME', 'JOIN_GAME' sau
                
                elif self.state == 'GAME_SCREEN':
                    # Đưa sự kiện chuột/bàn phím cho màn hình chơi game
                    if self.game_screen: # Đảm bảo game_screen đã được tạo
                        self.game_screen.handle_events(event)
                
            # 3. Cập nhật logic game (Update)
            self.ui_manager.update(time_delta)
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()

            # 4. VẼ LÊN MÀN HÌNH (Draw)
            self.screen.fill((20, 20, 20)) # Nền đen

            if self.state == 'MAIN_MENU':
                # main_menu không cần hàm draw() vì các nút được pygame_gui tự vẽ
                pass 
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw() # Vẽ bàn cờ và quân cờ

            # Luôn vẽ UI Manager cuối cùng để đảm bảo các yếu tố GUI nằm trên cùng
            self.ui_manager.draw_ui(self.screen)
            
            # 5. Cập nhật màn hình hiển thị
            pygame.display.flip()
            
        # Thoát Pygame khi vòng lặp kết thúc
        pygame.quit()