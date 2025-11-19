import os
import pygame

# --- Kích thước cửa sổ ---
# Tăng WIDTH lên để chứa Sidebar (ví dụ: 800 -> 1100)
# BOARD_WIDTH là chiều rộng cũ dành cho bàn cờ
BOARD_WIDTH = 800
SIDEBAR_WIDTH = 350
WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH 
HEIGHT = 800
FPS = 120

# --- ĐƯỜNG DẪN (GIỮ NGUYÊN) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'ui', 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
CHESS_PIECES_DIR = os.path.join(IMAGES_DIR, 'chess')
XIANGQI_PIECES_DIR = os.path.join(IMAGES_DIR, 'xiangqi')
XIANGQI_BOARD_IMG_PATH = os.path.join(XIANGQI_PIECES_DIR, 'xiangqi_board.png')

# --- MÀU SẮC ---
LIGHT_SQUARE_COLOR = (240, 217, 181)
DARK_SQUARE_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR = (255, 255, 0)

XIANGQI_LIGHT_BACKGROUND_COLOR = (70, 130, 180)
XIANGQI_DARK_BACKGROUND_COLOR = (50, 90, 140)

# --- MÀU SẮC UI MỚI ---
SIDEBAR_BG_COLOR = (40, 44, 52)
TEXT_COLOR = (220, 220, 220)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 149, 237)
CHAT_BG_COLOR = (30, 33, 39)

# --- HẰNG SỐ CỜ TƯỚNG ---
XIANGQI_ROWS = 10
XIANGQI_COLS = 9
PADDING_X = 50
PADDING_Y = 50
# Lưu ý: Kích thước ô cờ phải tính dựa trên BOARD_WIDTH chứ không phải toàn bộ WIDTH
SQUARE_SIZE_W = (BOARD_WIDTH - 2 * PADDING_X) / (XIANGQI_COLS - 1)
SQUARE_SIZE_H = (HEIGHT - 2 * PADDING_Y) / (XIANGQI_ROWS - 1)