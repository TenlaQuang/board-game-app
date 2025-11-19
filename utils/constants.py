import os
import pygame

# --- KÍCH THƯỚC CỬA SỔ (ĐÃ ĐIỀU CHỈNH) ---
# Mình tăng chiều rộng lên: 800 (Bàn cờ) + 320 (Sidebar) = 1120
WIDTH = 1120  
HEIGHT = 800
FPS = 60  # 60 là đủ mượt rồi, 120 có thể gây nóng máy không cần thiết

# --- ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'ui', 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')

CHESS_PIECES_DIR = os.path.join(IMAGES_DIR, 'chess')
XIANGQI_PIECES_DIR = os.path.join(IMAGES_DIR, 'xiangqi') 

# --- MÀU SẮC ---
LIGHT_SQUARE_COLOR = (240, 217, 181) # Màu be
DARK_SQUARE_COLOR = (181, 136, 99)   # Màu nâu gỗ

XIANGQI_LIGHT_BACKGROUND_COLOR = (255, 228, 196) # Màu gỗ sáng cho cờ tướng
XIANGQI_DARK_BACKGROUND_COLOR = (210, 180, 140) 

HIGHLIGHT_COLOR = (255, 255, 0) # Vàng
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 50, 50)
BLUE  = (50, 50, 255)
GREY  = (128, 128, 128)

# --- [QUAN TRỌNG] HẰNG SỐ KÍCH THƯỚC BÀN CỜ ---
# Phải có đoạn này thì core/board.py mới hiểu được
CHESS_ROWS = 8
CHESS_COLS = 8

XIANGQI_ROWS = 10
XIANGQI_COLS = 9

# --- Các thông số dưới đây chỉ để tham khảo (BoardUI mới tự tính lại) ---
PADDING_X = 50 
PADDING_Y = 50
SQUARE_SIZE_W = (WIDTH - 2 * PADDING_X) / (XIANGQI_COLS - 1)
SQUARE_SIZE_H = (HEIGHT - 2 * PADDING_Y) / (XIANGQI_ROWS - 1)