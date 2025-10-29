# utils/constants.py

# Kích thước cửa sổ tổng thể
WIDTH = 800
HEIGHT = 800

# Tốc độ game
FPS = 60

# Màu sắc (thêm các màu cho bàn cờ)
LIGHT_SQUARE_COLOR = (240, 217, 181) # Màu ô cờ sáng (be)
DARK_SQUARE_COLOR = (181, 136, 99)   # Màu ô cờ tối (nâu)
HIGHLIGHT_COLOR = (255, 255, 0)      # Màu highlight (vàng)

# Các đường dẫn ảnh (ví dụ)
# Tạo các thư mục con 'chess_pieces' và 'xiangqi_pieces' trong thư mục 'assets'
# Ví dụ: board-game-app/assets/chess_pieces/wK.png
ASSETS_DIR = 'assets'
CHESS_PIECES_DIR = f'{ASSETS_DIR}/chess_pieces'
XIANGQI_PIECES_DIR = f'{ASSETS_DIR}/xiangqi_pieces'