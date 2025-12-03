# Trong file: ui/assets.py

import pygame
import os
from utils.constants import (
    ASSETS_DIR, WIDTH, HEIGHT,
    CHESS_PIECES_DIR, XIANGQI_PIECES_DIR,
    IMAGES_DIR  # <--- CHẮC CHẮN RẰNG BẠN ĐÃ IMPORT IMAGES_DIR
)

# --- KHAI BÁO CÁC BIẾN "KHO" ---
CHESS_PIECES = {}
XIANGQI_PIECES = {}
CHESS_BUTTONS = {}
XIANGQI_BUTTONS = {}
MAIN_MENU_BACKGROUND = None
XIANGQI_BOARD_IMG = None # <-- Đã có
CHESS_BOARD_IMG = None

# (Tôi sửa lại lỗi typo ở đây, Cờ Vua là 8 ô)
DEFAULT_CHESS_PIECE_SIZE = WIDTH // 8 
DEFAULT_XIANGQI_PIECE_SIZE = WIDTH // 9 

def _create_gradient_background(width, height, start_color, end_color):
    """
    Hàm helper: Tạo một surface với dải màu gradient dọc.
    """
    surface = pygame.Surface((width, height))
    start_r, start_g, start_b = start_color
    end_r, end_g, end_b = end_color

    for y in range(height):
        t = y / height
        r = int(start_r + (end_r - start_r) * t)
        g = int(start_g + (end_g - start_g) * t)
        b = int(start_b + (end_b - start_b) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface

def load_assets():
    """Tải TẤT CẢ tài nguyên (ảnh nền, ảnh nút, ảnh quân cờ)."""
    print("Đang tải tài nguyên...")
    
    # <-- THÊM XIANGQI_BOARD_IMG VÀO GLOBAL
    global MAIN_MENU_BACKGROUND, CHESS_PIECES, XIANGQI_PIECES, XIANGQI_BOARD_IMG, CHESS_BOARD_IMG

    # --- 1. Tải Quân Cờ ---
    
   # ----- Tải hình ảnh Cờ Vua (ĐÃ SỬA CHO BỘ ẢNH MỚI) -----
    print("Đang tải ảnh Cờ Vua...")
    
    # [THAY ĐỔI Ở ĐÂY] Cập nhật tên file tương ứng với bộ ảnh mới
    # Logic cũ: 'P': 'white_pawn' -> File cũ: white_pawn.png
    # Logic mới: 'P': 'chess-pawn-white' -> File mới: chess-pawn-white.png
    
    chess_file_map = {
        # QUÂN TRẮNG (Chữ hoa)
        'P': 'chess-pawn-white', 
        'R': 'chess-rook-white', 
        'N': 'chess-knight-white', 
        'B': 'chess-bishop-white', 
        'Q': 'chess-queen-white', 
        'K': 'chess-king-white',
        
        # QUÂN ĐEN (Chữ thường)
        'p': 'chess-pawn-black', 
        'r': 'chess-rook-black', 
        'n': 'chess-knight-black', 
        'b': 'chess-bishop-black', 
        'q': 'chess-queen-black', 
        'k': 'chess-king-black'
    }
    
    # Đoạn vòng lặp dưới này GIỮ NGUYÊN KHÔNG ĐỔI
    for symbol, file_name in chess_file_map.items():
        # Nó sẽ tự động nối đuôi .png vào -> 'chess-pawn-white.png'
        filepath = os.path.join(CHESS_PIECES_DIR, f'{file_name}.png')
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                # Scale về kích thước ô cờ (như cũ)
                CHESS_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_CHESS_PIECE_SIZE, DEFAULT_CHESS_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ vua {filepath}: {e}")
        else:
            print(f"File ảnh cờ vua không tìm thấy: {filepath}")

            
    # ----- Tải hình ảnh Cờ Tướng (ĐÃ THÊM LOGIC MỚI) -----
    print("Đang tải ảnh Cờ Tướng...")
    xiangqi_file_map = {
        'G': 'red_general', 'A': 'red_advisor', 'E': 'red_elephant', 'H': 'red_horse', 'C': 'red_chariot', 'O': 'red_cannon', 'S': 'red_soldier',
        'g': 'black_general', 'a': 'black_advisor', 'e': 'black_elephant', 'h': 'black_horse', 'c': 'black_chariot', 'o': 'black_cannon', 's': 'black_soldier'
    }
    for symbol, file_name in xiangqi_file_map.items():
        filepath = os.path.join(XIANGQI_PIECES_DIR, f'{file_name}.png')
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                XIANGQI_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_XIANGQI_PIECE_SIZE, DEFAULT_XIANGQI_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ tướng {filepath}: {e}")
        else:
            print(f"File ảnh cờ tướng không tìm thấy: {filepath}")
            

    # --- 2. Tạo Ảnh Nền Gradient (Chỉ cho Menu Chính) ---
    print("Đang tạo nền gradient...")
    MAIN_MENU_BACKGROUND = _create_gradient_background(WIDTH, HEIGHT, (40, 40, 40), (10, 10, 10))
    print("Tạo nền gradient (Menu chính) hoàn tất.")

    # --- 3. TẢI ẢNH NỀN BÀN CỜ (PHẦN BỊ THIẾU) ---
    print("Đang tải ảnh nền bàn cờ...")
    try:
        # Tải và scale ảnh cho vừa màn hình
        img_path = os.path.join(IMAGES_DIR, 'xiangqi_board.png')
        img = pygame.image.load(img_path).convert()
        XIANGQI_BOARD_IMG = pygame.transform.scale(img, (WIDTH, HEIGHT))
        print("Đã tải ảnh nền Cờ Tướng.")
    except Exception as e:
        print(f"LỖI: Không tải được 'xiangqi_board.png': {e}")
        print("Bàn cờ tướng sẽ dùng màu nền dự phòng.")
        
    # [THÊM ĐOẠN NÀY ĐỂ TẢI BÀN CỜ VUA]
    try:
        # Đường dẫn tới file chess_board.png
        # Đảm bảo file nằm trong thư mục images được trỏ bởi IMAGES_DIR (hoặc ASSETS_DIR)
        chess_path = os.path.join(IMAGES_DIR, 'chess_board.png') 
        
        if os.path.exists(chess_path):
            CHESS_BOARD_IMG = pygame.image.load(chess_path).convert_alpha()
            print("✅ Đã tải ảnh nền Cờ Vua (chess_board.png).")
        else:
            print(f"⚠️ Không tìm thấy file: {chess_path}")
            
    except Exception as e:
        print(f"LỖI tải chess_board.png: {e}")

    # --- 4. Tải Ảnh Nút ---
    try:
        CHESS_BUTTONS['quick_play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_normal.png')).convert_alpha()
        CHESS_BUTTONS['quick_play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_hover.png')).convert_alpha()
        XIANGQI_BUTTONS['play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_normal.png')).convert_alpha()
        XIANGQI_BUTTONS['play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_hover.png')).convert_alpha()
    except (pygame.error, FileNotFoundError) as e: 
        print(f"CẢNH BÁO (hoặc file không tìm thấy) cho nút: {e}")

    print("Tải tài nguyên hoàn tất.")
    # --- 5. Tải Font ---  
UI_FONTS = {}

def load_font(filename, size):
    """Load font từ thư mục assets, nếu lỗi thì dùng font mặc định."""
    font_path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"[Font Error] Không thể load font {filename}: {e}")
    else:
        print(f"[Font Missing] Không tìm thấy file font: {font_path}")

    return pygame.font.SysFont(None, size)  # fallback

def init_fonts():
    """Khởi tạo font kích cỡ phổ biến."""
    global UI_FONTS
    UI_FONTS = {
        "winner": lambda size: load_font("myfont.ttf", size),
        "info": lambda size: load_font("myfont.ttf", size),
        "menu": lambda size: load_font("myfont.ttf", size),
    }
