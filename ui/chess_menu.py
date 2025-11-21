# ui/chess_menu.py
import pygame
import pygame_gui
import os  # Thêm thư viện này để kiểm tra file
from utils.constants import WIDTH, HEIGHT

class ChessMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        
        # --- KÍCH THƯỚC NÚT ---
        # 360x90 là kích thước đẹp để hiện hết nút gỗ nhọn 2 đầu
        btn_w, btn_h = 360, 90 
        gap = 25
        
        center_x = (WIDTH - btn_w) // 2
        
        # --- CHỈNH VỊ TRÍ NÚT ---
        # Đặt ở khoảng 35% chiều cao màn hình để né chữ "Tournament" ở trên
        start_y = HEIGHT * 0.41 

        # --- CÁC NÚT ---
        self.btn_pve = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((center_x, start_y), (btn_w, btn_h)),
            text="Chơi với Máy (PvE)",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        self.btn_pvp_online = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((center_x, start_y + btn_h + gap), (btn_w, btn_h)),
            text="Chơi Online (PvP)",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((center_x, start_y + (btn_h + gap) * 2), (btn_w, btn_h)),
            text="Quay lại",
            manager=ui_manager,
            object_id="#wood_btn"
        )

        # --- LOAD ẢNH NỀN (CODE ĐÃ SỬA ĐỂ TÌM FILE) ---
        self.bg_image = None
        
        # Danh sách các đường dẫn có thể (jpg hoặc png)
        possible_paths = [
            "ui/assets/images/menu_bg.jpg",
            "ui/assets/images/menu_bg.png"
        ]
        
        found_bg = False
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    loaded_img = pygame.image.load(path)
                    self.bg_image = pygame.transform.scale(loaded_img, (WIDTH, HEIGHT))
                    print(f"--> THÀNH CÔNG: Đã load ảnh nền từ: {path}")
                    found_bg = True
                    break
                except Exception as e:
                    print(f"--> LỖI khi đọc file {path}: {e}")

        if not found_bg:
            print("--> CẢNH BÁO: Không tìm thấy file 'menu_bg.jpg' hoặc 'menu_bg.png' trong thư mục ui/assets/images/")
            print("    (Hãy chắc chắn bạn đã đổi tên file ảnh và để đúng thư mục)")

        self.hide()

    def show(self):
        self.btn_pve.show()
        self.btn_pvp_online.show()
        self.btn_back.show()

    def hide(self):
        self.btn_pve.hide()
        self.btn_pvp_online.hide()
        self.btn_back.hide()
        
    def draw(self):
        # Nếu có ảnh thì vẽ ảnh, không thì vẽ màu nâu đất
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((45, 35, 25)) 

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_back:
                return 'BACK_TO_MAIN'
            if event.ui_element == self.btn_pve:
                return 'PLAY_OFFLINE'
            if event.ui_element == self.btn_pvp_online:
                return 'PLAY_ONLINE'
        return None