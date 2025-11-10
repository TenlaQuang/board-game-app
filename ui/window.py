import pygame
from ui.menu import MenuScreen
from games.chess import ChessGame
from games.chinese_chess import ChineseChessGame
from utils.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS

class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("P2P Chess Game")
        self.clock = pygame.time.Clock()

        # Màn hình đầu tiên
        self.current_screen = MenuScreen(self)

    def change_screen(self, new_screen):
        """Chuyển giữa các màn hình"""
        self.current_screen = new_screen

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    running = False

            self.current_screen.update(events)
            self.current_screen.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
