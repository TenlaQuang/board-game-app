import pygame
from ui.assets import load_chess_images

class BoardUI:
    def __init__(self, screen):
        self.screen = screen
        self.board_size = 8
        self.square_size = 100
        self.images = load_chess_images()

    def draw_board(self):
        colors = [pygame.Color(240, 217, 181), pygame.Color(181, 136, 99)]
        for row in range(self.board_size):
            for col in range(self.board_size):
                color = colors[(row + col) % 2]
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(col * self.square_size, row * self.square_size, self.square_size, self.square_size)
                )

    def draw_pieces(self):
        layout = [
            ["black_rook", "black_knight", "black_bishop", "black_queen", "black_king", "black_bishop", "black_knight", "black_rook"],
            ["black_pawn"] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            ["white_pawn"] * 8,
            ["white_rook", "white_knight", "white_bishop", "white_queen", "white_king", "white_bishop", "white_knight", "white_rook"]
        ]

        for row in range(self.board_size):
            for col in range(self.board_size):
                piece_name = layout[row][col]
                if piece_name:
                    piece = self.images[piece_name]
                    # 🔹 Tính toạ độ giữa ô
                    x = col * self.square_size + (self.square_size - piece.get_width()) // 2
                    y = row * self.square_size + (self.square_size - piece.get_height()) // 2
                    self.screen.blit(piece, (x, y))
