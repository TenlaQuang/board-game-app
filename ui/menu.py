import pygame
from utils.constants import WHITE, BLACK, FONT_PATH, WINDOW_WIDTH, WINDOW_HEIGHT
from network.server import start_server
from network.client import connect_to_server
from games.chess import ChessGame
from games.chinese_chess import ChineseChessGame
import threading
import os # <-- THÊM IMPORT NÀY

class MenuScreen:
    def __init__(self, app):
        self.app = app
        
        # --- PHẦN SỬA FONT ---
        try:
            # 1. Kiểm tra xem file font có thực sự tồn tại không
            if not os.path.exists(FONT_PATH):
                raise FileNotFoundError(f"Không tìm thấy font tại: {FONT_PATH}")
            
            # 2. Tải font từ file
            self.font = pygame.font.Font(FONT_PATH, 32)
            self.small_font = pygame.font.Font(FONT_PATH, 22)
            print(f"Đã tải font Tiếng Việt thành công từ: {FONT_PATH}")
        
        except Exception as e:
            # 3. Nếu lỗi, dùng font mặc định để không sập
            print(f"LỖI FONT: {e}")
            print("Đang dùng font mặc định (sẽ bị lỗi Tiếng Việt).")
            self.font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 22)
        # --- KẾT THÚC PHẦN SỬA ---

        self.player_name = ""
        self.game_choice = None
        self.status = "Chọn game và nhập tên"

        self.textbox = pygame.Rect(WINDOW_WIDTH//2 - 150, 400, 300, 40)
        self.active = False

        self.buttons = {
            "chess": pygame.Rect(WINDOW_WIDTH//2 - 200, 250, 180, 60),
            "xiangqi": pygame.Rect(WINDOW_WIDTH//2 + 20, 250, 180, 60)
        }

    def update(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.textbox.collidepoint(e.pos):
                    self.active = True
                else:
                    self.active = False

                for name, rect in self.buttons.items():
                    if rect.collidepoint(e.pos) and self.player_name:
                        self.status = "Đang tìm đối thủ..."
                        self.game_choice = name
                        threading.Thread(target=self.connect_to_peer, daemon=True).start()

            elif e.type == pygame.KEYDOWN and self.active:
                if e.key == pygame.K_RETURN:
                    self.active = False
                elif e.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                else:
                    self.player_name += e.unicode

    def connect_to_peer(self):
        try:
            conn = start_server(self.player_name)
            player_role = "host" # Thêm vai trò
        except OSError:
            conn = connect_to_server(self.player_name)
            player_role = "client" # Thêm vai trò

        # Khi kết nối xong -> mở game tương ứng
        if self.game_choice == "chess":
            # Truyền thêm player_role vào Game
            game_screen = ChessGame(self.app, conn, self.player_name, player_role)
            self.app.change_screen(game_screen)
        else:
            # game_screen = ChineseChessGame(self.app, conn, self.player_name, player_role)
            # self.app.change_screen(game_screen)
            print("Lỗi: Chưa cài đặt ChineseChessGame")

    def draw(self, surface):
        surface.fill((30, 30, 30))
        title = self.font.render("CHỌN TRÒ CHƠI", True, WHITE)
        surface.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

        # Buttons
        pygame.draw.rect(surface, (100, 100, 255), self.buttons["chess"])
        pygame.draw.rect(surface, (255, 100, 100), self.buttons["xiangqi"])

        txt1 = self.small_font.render("Cờ vua", True, WHITE)
        txt2 = self.small_font.render("Cờ tướng", True, WHITE)
        # Căn chữ vào giữa button
        surface.blit(txt1, (self.buttons["chess"].centerx - txt1.get_width()//2, self.buttons["chess"].centery - txt1.get_height()//2))
        surface.blit(txt2, (self.buttons["xiangqi"].centerx - txt2.get_width()//2, self.buttons["xiangqi"].centery - txt2.get_height()//2))

        # Textbox
        color = (200, 200, 200) if self.active else (100, 100, 100)
        pygame.draw.rect(surface, color, self.textbox, 2)
        
        # Cải thiện hiển thị "Nhập tên..."
        display_text = self.player_name
        text_color = WHITE
        if not self.player_name and not self.active:
            display_text = "Nhập tên..."
            text_color = (150, 150, 150) # Màu mờ
        
        text_surface = self.small_font.render(display_text, True, text_color)
        # Căn chữ vào giữa ô textbox
        surface.blit(text_surface, (self.textbox.x + 10, self.textbox.y + (self.textbox.height - text_surface.get_height()) // 2))

        # Status
        status_text = self.small_font.render(self.status, True, WHITE)
        surface.blit(status_text, (WINDOW_WIDTH//2 - status_text.get_width()//2, 480))