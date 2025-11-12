# ui/assets.py (Phiên bản MỚI NHẤT, hỗ trợ nền chuyển động)
import pygame
import os
from utils.constants import (
    ASSETS_DIR, WIDTH, HEIGHT,
    CHESS_PIECES_DIR, XIANGQI_PIECES_DIR
)

# --- KHAI BÁO CÁC BIẾN "KHO" ---
# Các file khác (như window.py) sẽ import các biến này
CHESS_PIECES = {}
XIANGQI_PIECES = {}

CHESS_BUTTONS = {}        # Dict chứa ảnh nút cờ vua
XIANGQI_BUTTONS = {}      # Dict chứa ảnh nút cờ tướng

MAIN_MENU_BACKGROUND = None
# CHESS_MENU_BACKGROUND (Đã xóa, dùng nền chuyển động)
# XIANGQI_MENU_BACKGROUND (Đã xóa, dùng nền chuyển động)
# ---------------------------------

# Kích thước quân cờ (tính toán 1 lần)
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
    
    # Cần global để gán giá trị cho biến "kho" ở trên
    global MAIN_MENU_BACKGROUND

    # --- 1. Tải Quân Cờ ---
    # ----- Tải hình ảnh Cờ Vua -----
    chess_symbols = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']
    for symbol in chess_symbols:
        filepath = os.path.join(CHESS_PIECES_DIR, f'{symbol}.png')
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                CHESS_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_CHESS_PIECE_SIZE, DEFAULT_CHESS_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ vua {filepath}: {e}")
        # else:
            # print(f"File ảnh cờ vua không tìm thấy: {filepath}")

    # ----- Tải hình ảnh Cờ Tướng -----
    xiangqi_symbols = ['C', 'H', 'E', 'A', 'G', 'O', 'S', 'c', 'h', 'e', 'a', 'g', 'o', 's']
    for symbol in xiangqi_symbols:
        filepath = os.path.join(XIANGQI_PIECES_DIR, f'{symbol}.png')
        if os.path.exists(filepath):
            try:
                image = pygame.image.load(filepath).convert_alpha()
                XIANGQI_PIECES[symbol] = pygame.transform.scale(image, (DEFAULT_XIANGQI_PIECE_SIZE, DEFAULT_XIANGQI_PIECE_SIZE))
            except pygame.error as e:
                print(f"Không thể tải ảnh cờ tướng {filepath}: {e}")
        # else:
            # print(f"File ảnh cờ tướng không tìm thấy: {filepath}")

    # --- 2. Tạo Ảnh Nền Gradient (Chỉ cho Menu Chính) ---
    print("Đang tạo nền gradient...")
    
    # Màu cho Menu Chính (xám đậm -> đen)
    MAIN_MENU_BACKGROUND = _create_gradient_background(WIDTH, HEIGHT, (40, 40, 40), (10, 10, 10))
    
    # (Đã xóa code tạo nền Cờ Vua và Cờ Tướng vì dùng nền chuyển động)
    
    print("Tạo nền gradient (Menu chính) hoàn tất.")

    # --- 3. Tải Ảnh Nút (Quan trọng) ---
    # (Phần này giữ nguyên để tải ảnh nút tùy chỉnh)
    try:
        # Tải nút Cờ Vua
        CHESS_BUTTONS['quick_play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_normal.png')).convert_alpha()
        CHESS_BUTTONS['quick_play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_hover.png')).convert_alpha()
        
        # Tải nút Cờ Tướng
        XIANGQI_BUTTONS['play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_normal.png')).convert_alpha()
        XIANGQI_BUTTONS['play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_hover.png')).convert_alpha()
        
    except (pygame.error, FileNotFoundError) as e: 
        print(f"CẢNH BÁO (hoặc file không tìm thấy) cho nút: {e}")
        print("BỎ QUA: Vui lòng tạo file ảnh (ví dụ: assets/button_quickplay_normal.png)")

    print("Tải tài nguyên hoàn tất.")
