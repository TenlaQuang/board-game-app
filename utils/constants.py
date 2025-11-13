# Trong file: utils/constants.py
import os
import pygame

# --- Kích thước cửa sổ ---
WIDTH = 800
HEIGHT = 800
FPS = 120 # Bạn đã tăng FPS

# --- ĐƯỜNG DẪN (ĐÃ SỬA LẠI CHO ĐÚNG) ---

# 1. Lấy đường dẫn thư mục gốc (BOARD-GAME-APP)
#    (Giả sử file constants.py nằm trong thư mục 'utils')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Đường dẫn đến thư mục 'assets' (nằm trong 'ui')
ASSETS_DIR = os.path.join(BASE_DIR, 'ui', 'assets')

# 3. Đường dẫn đến thư mục 'images' (nằm trong 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')

# 4. Đường dẫn chính xác đến thư mục quân cờ
#    (trỏ đến: BOARD-GAME-APP/ui/assets/images/chess)
CHESS_PIECES_DIR = os.path.join(IMAGES_DIR, 'chess')

#    (trỏ đến: BOARD-GAME-APP/ui/assets/images/xiangqi)
XIANGQI_PIECES_DIR = os.path.join(IMAGES_DIR, 'xiangqi') # Giả sử thư mục cờ tướng tên là 'xiangqi'

# ---------------------------------------------

# --- Màu sắc ---
LIGHT_SQUARE_COLOR = (240, 217, 181) # Màu ô sáng (be)
DARK_SQUARE_COLOR = (181, 136, 99)   # Màu ô tối (nâu)

XIANGQI_LIGHT_BACKGROUND_COLOR = (70, 130, 180) # Steel Blue
XIANGQI_DARK_BACKGROUND_COLOR = (50, 90, 140)   # Darker Steel Blue

HIGHLIGHT_COLOR = (255, 255, 0) # Vàng


# --- Hằng số Cờ Tướng (Cho board_ui.py) ---
XIANGQI_ROWS = 10
XIANGQI_COLS = 9
PADDING_X = 50 # 50 pixel lề
PADDING_Y = 50
# Kích thước ô Cờ Tướng
SQUARE_SIZE_W = (WIDTH - 2 * PADDING_X) / (XIANGQI_COLS - 1)
SQUARE_SIZE_H = (HEIGHT - 2 * PADDING_Y) / (XIANGQI_ROWS - 1)