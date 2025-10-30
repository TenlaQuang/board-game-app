import pygame
import os
from utils.constants import (
    ASSETS_DIR, WIDTH, HEIGHT,
    CHESS_PIECES_DIR, XIANGQI_PIECES_DIR
)

# --- KHAI BÁO CÁC BIẾN "KHO" ---
# Các file khác sẽ import các biến này
CHESS_PIECES = {}
XIANGQI_PIECES = {}

CHESS_BUTTONS = {}        # Dict chứa ảnh nút cờ vua (ảnh 2)
XIANGQI_BUTTONS = {}      # Dict chứa ảnh nút cờ tướng (ảnh 3)

MAIN_MENU_BACKGROUND = None
# (Không cần CHESS_MENU_BACKGROUND và XIANGQI_MENU_BACKGROUND ở đây nữa)
# ---------------------------------

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
    
    # Chỉ cần global cho nền Menu Chính
    global MAIN_MENU_BACKGROUND

    # --- 1. Tải Quân Cờ ---
    # (Bạn cần copy/paste code tải quân cờ (CHESS_PIECES, XIANGQI_PIECES) của bạn vào đây)
    # (Nếu bạn chưa có, hãy copy từ file "cơ thể hoàn thiện" tôi gửi trước)
    # ... (Giả sử code tải quân cờ của bạn ở đây) ...

    # --- 2. Tạo Ảnh Nền Gradient (Chỉ cho Menu Chính) ---
    print("Đang tạo nền gradient...")
    
    # Màu cho Menu Chính (xám đậm -> đen)
    MAIN_MENU_BACKGROUND = _create_gradient_background(WIDTH, HEIGHT, (40, 40, 40), (10, 10, 10))
    
    # (Đã xóa code tạo nền Cờ Vua và Cờ Tướng)
    
    print("Tạo nền gradient (Menu chính) hoàn tất.")

    # --- 3. Tải Ảnh Nút (Quan trọng) ---
    # (Phần này giữ nguyên để tải ảnh nút tùy chỉnh của bạn)
    try:
        # Tải nút Cờ Vua
        CHESS_BUTTONS['quick_play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_normal.png')).convert_alpha()
        CHESS_BUTTONS['quick_play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_quickplay_hover.png')).convert_alpha()
        
        # Tải nút Cờ Tướng
        XIANGQI_BUTTONS['play_normal'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_normal.png')).convert_alpha()
        XIANGQI_BUTTONS['play_hover'] = pygame.image.load(os.path.join(ASSETS_DIR, 'button_play_hover.png')).convert_alpha()
        
    except (pygame.error, FileNotFoundError) as e: 
        print(f"LỖI (hoặc file không tìm thấy) cho nút: {e}")
        print("BỎ QUA: Vui lòng tạo file ảnh (ví dụ: assets/button_quickplay_normal.png)")

    print("Tải tài nguyên hoàn tất.")

