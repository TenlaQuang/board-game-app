# fix_assets.py
import pygame
import os

# Cấu hình kích thước mục tiêu
BUTTON_SIZE = (220, 220)
BACKGROUND_SIZE = (800, 600) # Kích thước cửa sổ game

# Đường dẫn (Kiểm tra kỹ xem đúng thư mục máy bạn không)
IMG_DIR = "ui/assets/images/"

def resize_image(filename, size, is_background=False):
    path = os.path.join(IMG_DIR, filename)
    
    if not os.path.exists(path):
        print(f"❌ LỖI: Không tìm thấy file {path}")
        return

    try:
        img = pygame.image.load(path)
        
        # Nếu là background thì scale vừa màn hình, nếu là nút thì scale vuông
        img_scaled = pygame.transform.smoothscale(img, size)
        
        # Lưu đè lại file cũ
        pygame.image.save(img_scaled, path)
        print(f"✅ Đã sửa xong file: {filename} -> Kích thước mới: {size}")
    except Exception as e:
        print(f"❌ Lỗi khi xử lý {filename}: {e}")

def main():
    pygame.init()
    # Tạo một màn hình ảo để pygame hoạt động
    pygame.display.set_mode((1, 1))
    
    print("--- ĐANG TỰ ĐỘNG SỬA KÍCH THƯỚC ẢNH ---")
    
    # 1. Sửa ảnh các nút bấm (Về 220x220)
    resize_image("chess_3d.png", BUTTON_SIZE)
    resize_image("chess_3d_hover.png", BUTTON_SIZE)
    resize_image("xiangqi_3d.png", BUTTON_SIZE)
    resize_image("xiangqi_3d_hover.png", BUTTON_SIZE)
    
    # 2. Sửa ảnh nền (Nếu có)
    # resize_image("background.png", BACKGROUND_SIZE, is_background=True)
    
    print("---------------------------------------")
    print("Hoàn tất! Hãy chạy lại main.py để xem kết quả.")

if __name__ == "__main__":
    main()