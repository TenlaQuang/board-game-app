# # Trong file: utils/constants.py
import os

# # --- Kích thước cho cờ vua ---
# SQUARE_SIZE = 64  # Kích thước mỗi ô (pixels)
# ROWS = 8
# COLS = 8

# # (Bạn có thể thêm kích thước cờ tướng sau)
# # XIANGQI_ROWS = 10
# # XIANGQI_COLS = 9

# # --- THÊM CÁC HẰNG SỐ CÒN THIẾU VÀO ĐÂY ---
# WIDTH = COLS * SQUARE_SIZE   # (8 * 64 = 512)
# HEIGHT = ROWS * SQUARE_SIZE  # (8 * 64 = 512)
# FPS = 60                     # Frame per second (tốc độ khung hình)

# # --- Đường dẫn ---
# # Lấy đường dẫn tuyệt đối đến thư mục gốc của dự án (thư mục DACS4)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# # Tạo đường dẫn động đến thư mục images
# IMAGES_DIR = os.path.join(BASE_DIR, 'ui', 'assets', 'images')
# utils/constants.py
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT_PATH = os.path.join(BASE_DIR, 'ui', 'assets', 'fonts', 'Roboto-Regular.ttf')  # pygame mặc định
