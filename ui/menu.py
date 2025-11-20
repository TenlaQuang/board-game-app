# ui/menu.py
import pygame
import pygame_gui
import math 
from utils.constants import WIDTH, HEIGHT

class MainMenu:
    def __init__(self, screen, ui_manager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.button_list = []
        
        # --- Tải ảnh quân cờ & Tạo bóng ---
        try:
            self.img_chess = pygame.image.load("ui/assets/images/chess_3d_hover.png").convert_alpha()
            self.img_xiangqi = pygame.image.load("ui/assets/images/xiangqi_3d_hover.png").convert_alpha()
            
            # Kích thước nút
            self.btn_size = 220
            self.img_chess = pygame.transform.smoothscale(self.img_chess, (self.btn_size, self.btn_size))
            self.img_xiangqi = pygame.transform.smoothscale(self.img_xiangqi, (self.btn_size, self.btn_size))
            
            # TẠO BÓNG PHẢN CHIẾU (REFLECTION)
            self.ref_chess = pygame.transform.flip(self.img_chess, False, True)
            self.ref_xiangqi = pygame.transform.flip(self.img_xiangqi, False, True)
            
            # Làm mờ bóng (Alpha thấp) và ép dẹp xuống
            self.ref_chess.set_alpha(60) 
            self.ref_xiangqi.set_alpha(60)
            self.ref_chess = pygame.transform.scale(self.ref_chess, (self.btn_size, int(self.btn_size * 0.6)))
            self.ref_xiangqi = pygame.transform.scale(self.ref_xiangqi, (self.btn_size, int(self.btn_size * 0.6)))

        except Exception as e:
            print(f"Lỗi tải ảnh hiệu ứng: {e}")
            self.img_chess = None

        # --- VỊ TRÍ ---
        gap = 120
        total_width = (self.btn_size * 2) + gap
        self.start_x = (WIDTH - total_width) // 2
        self.start_y = (HEIGHT - self.btn_size) // 2 - 50

        # --- TẠO NÚT BẤM (Trong suốt - Chỉ để bắt click) ---
        
        self.btn_chess = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.start_x, self.start_y), (self.btn_size, self.btn_size)),
            text='',
            manager=self.ui_manager,
            object_id='#btn_chess'
        )
        self.button_list.append(self.btn_chess)

        self.btn_xiangqi = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.start_x + self.btn_size + gap, self.start_y), (self.btn_size, self.btn_size)),
            text='', 
            manager=self.ui_manager,
            object_id='#btn_xiangqi'
        )
        self.button_list.append(self.btn_xiangqi)

        # Nhãn tên
        self.lbl_chess = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.start_x, self.start_y + self.btn_size), (self.btn_size, 40)),
            text="Cờ Vua",
            manager=self.ui_manager,
            object_id='#lbl_chess_text'
        )
        self.button_list.append(self.lbl_chess)

        self.lbl_xiangqi = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.start_x + self.btn_size + gap, self.start_y + self.btn_size), (self.btn_size, 40)),
            text="Cờ Tướng",
            manager=self.ui_manager,
            object_id='#lbl_xiangqi_text'
        )
        self.button_list.append(self.lbl_xiangqi)
        
        # Nút Thoát
        quit_width = 160
        quit_height = 50
        quit_x = (WIDTH - quit_width) // 2
        self.btn_quit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((quit_x, self.start_y + self.btn_size + 100), (quit_width, quit_height)),
            text='Thoát Game',
            manager=self.ui_manager,
            object_id='#btn_quit'
        )
        self.button_list.append(self.btn_quit)

        self.hide()

    def show(self):
        for btn in self.button_list: btn.show()

    def hide(self):
        for btn in self.button_list: btn.hide()

    def draw_custom_effects(self):
        """Vẽ hiệu ứng 3D: Chỉ bay bay khi chuột hover vào"""
        if not self.btn_chess.visible: return 
        
        # 1. Lấy vị trí chuột và thời gian
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()
        
        # 2. Xử lý Logic cho CỜ VUA
        # Kiểm tra: Chuột có chạm vào nút Cờ Vua không?
        if self.btn_chess.rect.collidepoint(mouse_pos):
            # Nếu chạm: Tính toán độ bay (dập dềnh nhanh hơn xíu cho đẹp: 0.005)
            offset_chess = math.sin(current_time * 0.005) * 15 
        else:
            # Nếu không chạm: Đứng im
            offset_chess = 0

        # 3. Xử lý Logic cho CỜ TƯỚNG
        if self.btn_xiangqi.rect.collidepoint(mouse_pos):
            offset_xiangqi = math.sin(current_time * 0.005) * 15
        else:
            offset_xiangqi = 0

        # 4. Tính tọa độ cuối cùng
        chess_pos = (self.start_x, self.start_y + offset_chess)
        xiangqi_pos = (self.start_x + self.btn_size + 120, self.start_y + offset_xiangqi)

        # 5. VẼ BÓNG (Reflection)
        if self.img_chess:
            # Bóng cách chân một đoạn cố định
            self.screen.blit(self.ref_chess, (chess_pos[0], chess_pos[1] + self.btn_size - 15))
            self.screen.blit(self.ref_xiangqi, (xiangqi_pos[0], xiangqi_pos[1] + self.btn_size - 15))

        # 6. VẼ ẢNH CHÍNH
        if self.img_chess:
            self.screen.blit(self.img_chess, chess_pos)
            self.screen.blit(self.img_xiangqi, xiangqi_pos)
            
            # Cập nhật vị trí nút bấm chạy theo hình ảnh 
            # (Để chuột vẫn bắt dính được khi nút đang bay)
            self.btn_chess.set_relative_position((chess_pos[0], chess_pos[1]))
            self.btn_xiangqi.set_relative_position((xiangqi_pos[0], xiangqi_pos[1]))

    def handle_events(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_chess:
                return 'GOTO_CHESS_MENU'
            if event.ui_element == self.btn_xiangqi:
                return 'GOTO_XIANGQI_MENU'
            if event.ui_element == self.btn_quit:
                return 'QUIT'
        return None