# Đây là nội dung ĐẦY ĐỦ cho file: ui/window.py

import pygame
import pygame_gui
from .menu import MainMenu
from utils.constants import WIDTH, HEIGHT, FPS  # Import các hằng số

class App:
    
    # --- PHẦN 1: KHỞI TẠO (SETUP) ---
    def __init__(self):
        """Hàm khởi tạo, chạy 1 lần duy nhất khi game bắt đầu."""
        pygame.init()
        
        # 1. Tạo cửa sổ (self.screen)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        
        # 2. Tạo đồng hồ
        self.clock = pygame.time.Clock()
        self.running = True

        # 3. Khởi tạo UI Manager
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json') 

        # 4. Tạo các "màn hình" (phải sau khi có self.screen và self.ui_manager)
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        # self.game_screen = None # Sẽ làm sau
        
        # 5. Đặt trạng thái game ban đầu
        self.state = 'MAIN_MENU'

    # --- PHẦN 2: VÒNG LẶP CHÍNH (ĐỘNG CƠ) ---
    def run(self):
        """Vòng lặp game chính, chạy 60 lần mỗi giây."""
        
        while self.running:
            # 1. Lấy time_delta (quan trọng cho GUI)
            time_delta = self.clock.tick(FPS) / 1000.0
            
            # 2. XỬ LÝ SỰ KIỆN (Fix lỗi "Not Responding")
            events = pygame.event.get()
            for event in events:
                
                # 2a. Bắt sự kiện QUIT (nhấn nút X)
                if event.type == pygame.QUIT:
                    self.running = False
                
                # 2b. Đưa sự kiện cho UI Manager (để xử lý nút bấm)
                self.ui_manager.process_events(event)
                
                # 2c. Đưa sự kiện cho state hiện tại
                if self.state == 'MAIN_MENU':
                    next_state = self.main_menu.handle_events(event)
                    
                    if next_state == 'QUIT':
                        self.running = False
                    elif next_state == 'PLAY_OFFLINE':
                        print("Chuyển sang màn hình chơi game!")
                        self.state = 'GAME_SCREEN'
                    # (Thêm các state 'HOST_GAME', 'JOIN_GAME'...)
                
                elif self.state == 'GAME_SCREEN':
                    # (Sau này sẽ gọi self.game_screen.handle_events(event))
                    pass

            # 3. CẬP NHẬT (Update)
            self.ui_manager.update(time_delta)
            
            # 4. VẼ LÊN MÀN HÌNH (Draw)
            
            # 4a. Xóa màn hình bằng một màu nền
            self.screen.fill((20, 20, 20)) 
            
            # 4b. Vẽ state hiện tại (nếu cần)
            # (Phần draw() của MainMenu không cần gọi vì GUI tự vẽ)
            
            # 4c. Vẽ UI Manager (vẽ các nút bấm lên trên cùng)
            self.ui_manager.draw_ui(self.screen)
            
            # 5. LẬT MÀN HÌNH (Cập nhật những gì đã vẽ)
            pygame.display.flip()
            
        # Hết vòng lặp (self.running = False)
        pygame.quit()