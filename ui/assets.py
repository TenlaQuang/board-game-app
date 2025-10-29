# ui/assets.py
import pygame
import os
from utils.constants import (
    CHESS_PIECES_DIR, XIANGQI_PIECES_DIR, 
    WIDTH, HEIGHT # Cần để tính toán kích thước quân cờ mặc định
)

# Khai báo các dict sẽ chứa ảnh đã load
CHESS_PIECES = {}
XIANGQI_PIECES = {}

# Tạm thời dùng kích thước này, sau này có thể tính lại tùy loại cờ
DEFAULT_CHESS_PIECE_SIZE = WIDTH // 8 
DEFAULT_XIANGQI_PIECE_SIZE = WIDTH // 9 # Cờ tướng có 9 cột

def load_assets():
    """Tải tất cả hình ảnh quân cờ cho cả Cờ Vua và Cờ Tướng."""
    print("Đang tải tài nguyên...")

    # ----- Tải hình ảnh Cờ Vua -----
    # Các ký hiệu quân cờ vua (theo quy ước của bạn trong core/piece.py)
    chess_symbols = [
        'K', 'Q', 'R', 'B', 'N', 'P', # White (uppercase)
        'k', 'q', 'r', 'b', 'n', 'p'  # Black (lowercase)
    ]
    
    for symbol in chess_symbols:
        filename = f'{symbol}.png'
        filepath = os.path.join(CHESS_PIECES_DIR, filename)
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                CHESS_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_CHESS_PIECE_SIZE, DEFAULT_CHESS_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ vua {filepath}: {e}")
        else:
            print(f"File ảnh cờ vua không tìm thấy: {filepath}")

    # ----- Tải hình ảnh Cờ Tướng -----
    # Các ký hiệu quân cờ tướng (theo quy ước của bạn: G, g, A, a, ...)
    # Chú ý: Cờ Tướng có màu đỏ/đen, không phải trắng/đen.
    # Ký hiệu của bạn: uppercase cho white/red, lowercase cho black.
    # C (Chariot), H (Horse), E (Elephant), A (Advisor), G (General), O (Cannon), S (Soldier)
    xiangqi_symbols = [
        'C', 'H', 'E', 'A', 'G', 'O', 'S', # White (Red)
        'c', 'h', 'e', 'a', 'g', 'o', 's'  # Black
    ]

    for symbol in xiangqi_symbols:
        filename = f'{symbol}.png'
        filepath = os.path.join(XIANGQI_PIECES_DIR, filename)
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                XIANGQI_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_XIANGQI_PIECE_SIZE, DEFAULT_XIANGQI_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ tướng {filepath}: {e}")
        else:
            print(f"File ảnh cờ tướng không tìm thấy: {filepath}")

    print("Tải tài nguyên hoàn tất.")

# Ví dụ về cấu trúc thư mục ảnh:
# board-game-app/
# ├── assets/
# │   ├── chess_pieces/
# │   │   ├── bB.png
# │   │   ├── bK.png
# │   │   └── ...
# │   └── xiangqi_pieces/
# │       ├── g.png (tướng đen)
# │       ├── G.png (tướng đỏ)
# │       └── ...
# └── ... (các file code khác)