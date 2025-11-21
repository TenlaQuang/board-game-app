# games/base_game.py
import pygame
from ui.chat_box import ChatBox
# Đảm bảo constants có đủ màu
from utils.constants import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, BLACK, FPS 

class BaseGame:
    def __init__(self, app, connection, player_name):
        self.app = app
        self.conn = connection
        self.player_name = player_name
        self.running = True

        # Kích thước bàn cờ 480x480 (mỗi ô 60px)
        self.board_rect = pygame.Rect(50, 50, 480, 480)
        self.font = pygame.font.Font(None, 24)

        # Chat nằm bên phải bàn cờ
        self.chat = ChatBox(560, 50, 300, 480, self.font)

    def update_network(self):
        """Nhận dữ liệu từ đối thủ (Chỉ chạy nếu có mạng)"""
        # --- [SỬA] THÊM DÒNG NÀY ---
        if not self.conn: 
            return 
        # ---------------------------

        msg = self.conn.get_message()
        if msg:
            if msg.startswith("CHAT:"):
                content = msg.split("CHAT:", 1)[1]
                self.chat.messages.append((self.conn.peer_name, content))
            else:
                self.handle_game_message(msg)

    def handle_game_message(self, msg: str):
        pass

    def handle_event(self, e):
        # Chỉ xử lý chat nếu có kết nối mạng
        if self.conn:
            self.chat.handle_event(e, self.conn)

    def draw_base(self, screen):
        pygame.draw.rect(screen, (80, 80, 80), self.board_rect)
        # Chỉ vẽ chat nếu online (hoặc vẽ trống cũng được)
        if self.conn:
            self.chat.draw(screen)