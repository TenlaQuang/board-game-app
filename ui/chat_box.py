import pygame
from utils.constants import WHITE, BLACK, RED, BLUE

class GameSidebar:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        
        # --- CHAT COMPONENT ---
        self.messages = []
        self.input_text = ""
        self.input_active = False
        # Khu vực hiển thị tin nhắn (chiếm phần giữa)
        self.history_rect = pygame.Rect(x + 10, y + 80, w - 20, h - 220)
        # Khu vực nhập liệu (dưới khu vực tin nhắn)
        self.input_rect = pygame.Rect(x + 10, self.history_rect.bottom + 10, w - 20, 30)

        # --- BUTTONS ---
        btn_y = self.input_rect.bottom + 20
        btn_w = (w - 30) // 2
        self.btn_draw = pygame.Rect(x + 10, btn_y, btn_w, 40)     # Nút Cầu hòa
        self.btn_resign = pygame.Rect(self.btn_draw.right + 10, btn_y, btn_w, 40) # Nút Đầu hàng

    def handle_event(self, e, network_manager=None):
        """
        Xử lý sự kiện: Nhập chat, click nút.
        Trả về action string (ví dụ: 'OFFER_DRAW', 'RESIGN') để BoardUI xử lý.
        """
        action = None

        # 1. XỬ LÝ CLICK CHUỘT
        if e.type == pygame.MOUSEBUTTONDOWN:
            # Active ô nhập liệu nếu click vào nó
            if self.input_rect.collidepoint(e.pos):
                self.input_active = True
            else:
                self.input_active = False
            
            # Click nút Cầu Hòa
            if self.btn_draw.collidepoint(e.pos):
                print(">> Click Cầu hòa")
                action = "OFFER_DRAW"
                if network_manager:
                    network_manager.send_command("DRAW_OFFER")

            # Click nút Đầu Hàng
            elif self.btn_resign.collidepoint(e.pos):
                print(">> Click Đầu hàng")
                action = "RESIGN"
                if network_manager:
                    network_manager.send_command("RESIGN")

        # 2. XỬ LÝ BÀN PHÍM (CHAT)
        elif e.type == pygame.KEYDOWN and self.input_active:
            if e.key == pygame.K_RETURN:
                if self.input_text:
                    msg = self.input_text
                    # Hiển thị lên máy mình
                    self.add_message("Bạn", msg)
                    # Gửi qua mạng
                    if network_manager:
                        network_manager.send_chat(msg)
                    self.input_text = ""
            elif e.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                # Giới hạn độ dài tin nhắn
                if len(self.input_text) < 40:
                    self.input_text += e.unicode
        
        return action

    def add_message(self, sender, text):
        self.messages.append((sender, text))
        # Chỉ giữ lại 15 tin nhắn gần nhất để không bị tràn
        if len(self.messages) > 15:
            self.messages.pop(0)

    def draw(self, surface, game_logic):
        # 1. Vẽ nền Sidebar
        pygame.draw.rect(surface, (30, 30, 35), self.rect)
        pygame.draw.line(surface, (100, 100, 100), (self.rect.x, self.rect.y), (self.rect.x, self.rect.bottom), 2)

        # 2. HIỂN THỊ LƯỢT ĐI (TURN INFO)
        # Lấy thông tin từ GameState
        current_turn = game_logic.current_turn # 'white' or 'black'
        my_color = getattr(game_logic, 'my_color', None) # 'white' or 'black' or None
        
        status_text = ""
        text_color = WHITE
        
        if game_logic.winner:
            status_text = f"KẾT THÚC: {game_logic.winner.upper()} THẮNG"
            text_color = (255, 215, 0) # Gold
        else:
            turn_vn = "TRẮNG" if current_turn == 'white' else "ĐEN"
            if game_logic.game_type == 'chinese_chess':
                turn_vn = "ĐỎ" if current_turn == 'white' else "ĐEN" # Mapping logic cờ tướng
            
            status_text = f"Lượt đi: {turn_vn}"
            
            # Hiển thị thêm "Là bạn!" hoặc "Đối thủ..."
            if my_color:
                if current_turn == my_color:
                    status_text += " (Bạn)"
                    text_color = (100, 255, 100) # Green
                else:
                    text_color = (200, 200, 200) # Grey

        # Vẽ Text Lượt đi ở trên cùng
        font_big = pygame.font.SysFont("Arial", 24, bold=True)
        txt_surf = font_big.render(status_text, True, text_color)
        surface.blit(txt_surf, (self.rect.x + 20, self.rect.y + 20))

        # 3. VẼ KHUNG CHAT (Lịch sử)
        pygame.draw.rect(surface, (20, 20, 20), self.history_rect)
        y_offset = self.history_rect.bottom - 25
        # Vẽ từ dưới lên
        for sender, msg in reversed(self.messages):
            if y_offset < self.history_rect.y: break # Hết chỗ thì thôi
            
            color = (100, 200, 255) if sender == "Bạn" else (255, 200, 100)
            if sender == "System": color = (200, 200, 200)

            line_surf = self.font.render(f"{sender}: {msg}", True, color)
            surface.blit(line_surf, (self.history_rect.x + 5, y_offset))
            y_offset -= 25

        # 4. VẼ Ô NHẬP LIỆU (INPUT)
        color_input = (255, 255, 255) if self.input_active else (150, 150, 150)
        pygame.draw.rect(surface, (50, 50, 50), self.input_rect, border_radius=5)
        pygame.draw.rect(surface, color_input, self.input_rect, 2, border_radius=5)
        
        txt_input = self.font.render(self.input_text, True, WHITE)
        surface.blit(txt_input, (self.input_rect.x + 5, self.input_rect.y + 5))

        # 5. VẼ NÚT CHỨC NĂNG
        # Nút Hòa
        mouse_pos = pygame.mouse.get_pos()
        color_draw = (100, 100, 100) if self.btn_draw.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(surface, color_draw, self.btn_draw, border_radius=5)
        txt_draw = self.font.render("Cầu Hòa", True, WHITE)
        surface.blit(txt_draw, (self.btn_draw.centerx - txt_draw.get_width()//2, self.btn_draw.centery - txt_draw.get_height()//2))

        # Nút Đầu hàng
        color_resign = (200, 50, 50) if self.btn_resign.collidepoint(mouse_pos) else (150, 30, 30)
        pygame.draw.rect(surface, color_resign, self.btn_resign, border_radius=5)
        txt_resign = self.font.render("Đầu Hàng", True, WHITE)
        surface.blit(txt_resign, (self.btn_resign.centerx - txt_resign.get_width()//2, self.btn_resign.centery - txt_resign.get_height()//2))