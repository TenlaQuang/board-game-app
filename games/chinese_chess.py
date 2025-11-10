# games/chinese_chess.py
import pygame
from games.base_game import BaseGame
from utils.constants import WHITE, BLACK

class ChineseChessGame(BaseGame):
    def __init__(self, app, connection, player_name):
        super().__init__(app, connection, player_name)
        self.turn = "red"
        self.title = pygame.font.Font(None, 36).render("CỜ TƯỚNG", True, WHITE)

    def handle_game_message(self, msg):
        print("[ChineseChess] Nhận tin:", msg)

    def update(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            else:
                self.handle_event(e)

        self.update_network()

    def draw(self, screen):
        screen.fill((25, 25, 25))
        screen.blit(self.title, (self.board_rect.centerx - 50, 10))
        self.draw_base(screen)

        # Vẽ bàn cờ 9x10
        cols, rows = 9, 10
        cell_w = self.board_rect.width // (cols - 1)
        cell_h = self.board_rect.height // (rows - 1)

        for i in range(cols):
            x = self.board_rect.x + i * cell_w
            pygame.draw.line(screen, WHITE, (x, self.board_rect.y), (x, self.board_rect.y + self.board_rect.height))

        for j in range(rows):
            y = self.board_rect.y + j * cell_h
            pygame.draw.line(screen, WHITE, (self.board_rect.x, y), (self.board_rect.x + self.board_rect.width, y))
