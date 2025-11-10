import pygame
import os

def load_chess_images():
    base_path = os.path.join("ui", "assets", "images", "chess")
    pieces = ["pawn", "rook", "knight", "bishop", "queen", "king"]
    colors = ["white", "black"]

    images = {}
    for color in colors:
        for piece in pieces:
            name = f"{color}_{piece}"
            path = os.path.join(base_path, f"{name}.png")
            images[name] = pygame.transform.scale(pygame.image.load(path), (58, 80))
    return images
