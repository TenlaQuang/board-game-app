# games/chess.py
import pygame
from games.base_game import BaseGame
from utils.constants import WHITE, BLACK

class ChessGame(BaseGame):
    def __init__(self, app, connection, player_name):
        super().__init__(app, connection, player_name)
        self.turn = "white"
        self.title = pygame.font.Font(None, 36).render("CỜ VUA", True, WHITE)

    def handle_game_message(self, msg):
        print("[Chess] Nhận tin:", msg)

    def update(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            else:
                self.handle_event(e)

        self.update_network()

    def draw(self, screen):
        screen.fill((20, 20, 20))
        screen.blit(self.title, (self.board_rect.centerx - 50, 10))
        self.draw_base(screen)

        # Ô vuông bàn cờ
        cell_size = self.board_rect.width // 8
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(
                    self.board_rect.x + col * cell_size,
                    self.board_rect.y + row * cell_size,
                    cell_size,
                    cell_size
                )
                color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                pygame.draw.rect(screen, color, rect)
