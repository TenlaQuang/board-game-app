import pygame
import time
import os
import math
from utils.constants import WHITE, BLACK, RED, BLUE

class GameSidebar:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        
        # --- CHAT COMPONENT ---
        self.messages = []
        self.input_text = ""
        self.input_active = False
        
        self.history_rect = pygame.Rect(x + 10, y + 80, w - 20, h - 220)
        
        # Input Area
        input_w = w - 90
        self.input_rect = pygame.Rect(x + 10, self.history_rect.bottom + 10, input_w, 30)
        self.btn_emoji = pygame.Rect(self.input_rect.right + 5, self.input_rect.y, 30, 30)
        self.btn_mic = pygame.Rect(self.btn_emoji.right + 5, self.input_rect.y, 30, 30)

        # --- LOAD EMOJI ---
        self.show_emoji_panel = False
        self.emoji_images = [] 
        self.emoji_count = 33 
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        emoji_dir = os.path.join(base_path, "assets", "emojis")

        for i in range(1, self.emoji_count + 1):
            try:
                img = None
                for ext in [".gif", ".png", ".jpg", ".webp"]:
                    p = os.path.join(emoji_dir, f"{i}{ext}")
                    if os.path.exists(p):
                        img = pygame.image.load(p).convert_alpha()
                        img = pygame.transform.smoothscale(img, (28, 28))
                        break
                if img is None: 
                    img = pygame.Surface((28, 28)); img.fill((50, 50, 50))
                self.emoji_images.append(img)
            except: pass

        # [MỚI] TẠO ICON CHO NÚT EMOJI
        # Lấy hình đầu tiên (1.gif) làm icon cho nút bấm. Nếu không có thì tạo ô màu vàng.
        if self.emoji_images:
            self.icon_btn_emoji = self.emoji_images[6] # Lấy hình mặt cười số 1
        else:
            self.icon_btn_emoji = pygame.Surface((24,24))
            self.icon_btn_emoji.fill((255, 200, 0))

        # Tính toán Grid Emoji
        icon_size = 35; padding = 5
        cols = max(1, (w - 20) // (icon_size + padding))
        rows = math.ceil(len(self.emoji_images) / cols)
        panel_h = min(rows * (icon_size + padding) + padding, 300) # Giới hạn chiều cao max 300px
        
        self.emoji_panel_rect = pygame.Rect(x + 10, self.input_rect.y - panel_h - 5, w - 20, panel_h)
        
        self.emoji_rects = []
        if self.emoji_images:
            for i in range(len(self.emoji_images)):
                r = i // cols; c = i % cols
                rect_x = self.emoji_panel_rect.x + padding + c * (icon_size + padding)
                rect_y = self.emoji_panel_rect.y + padding + r * (icon_size + padding)
                self.emoji_rects.append(pygame.Rect(rect_x, rect_y, icon_size, icon_size))

        # Voice
        self.is_recording = False
        self.record_start_time = 0
        self.voice_play_buttons = [] 

        # Buttons
        btn_y = self.input_rect.bottom + 20
        btn_w = (w - 30) // 2
        self.btn_draw = pygame.Rect(x + 10, btn_y, btn_w, 40)     
        self.btn_resign = pygame.Rect(self.btn_draw.right + 10, btn_y, btn_w, 40) 

        # Popup
        self.popup_type = None 
        self.popup_rect = pygame.Rect(x + 10, y + 200, w - 20, 130)
        pw = (self.popup_rect.width - 30) // 2; py = self.popup_rect.bottom - 40
        self.btn_p_yes = pygame.Rect(self.popup_rect.x + 10, py, pw, 30)
        self.btn_p_no = pygame.Rect(self.btn_p_yes.right + 10, py, pw, 30)

    def handle_event(self, e, network_manager=None):
        action = None

        # Voice Press/Release
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_mic.collidepoint(e.pos):
                self.is_recording = True; self.record_start_time = time.time(); return None
        elif e.type == pygame.MOUSEBUTTONUP:
            if self.is_recording:
                self.is_recording = False
                duration = time.time() - self.record_start_time
                if duration > 0.5:
                    msg = f"[Voice:{duration:.1f}s]" 
                    self.add_message("Bạn", msg)
                    if network_manager: network_manager.send_chat(msg)
                return None

        if e.type == pygame.MOUSEBUTTONDOWN:
            # Play Voice
            for btn_rect, voice_msg in self.voice_play_buttons:
                if btn_rect.collidepoint(e.pos):
                    print(f">> [LOA] Playing: {voice_msg}"); return None

            # Popup
            if self.popup_type:
                if self.btn_p_yes.collidepoint(e.pos):
                    if self.popup_type == 'RESIGN_CONFIRM':
                        action = "RESIGN"
                        if network_manager: network_manager.send_command("RESIGN")
                        self.add_message("Bạn", "Đã đầu hàng.")
                    elif self.popup_type == 'DRAW_RECEIVE':
                        if network_manager: network_manager.send_command("DRAW_ACCEPT")
                        self.add_message("Bạn", "Đã chấp nhận hòa!")
                        action = "DRAW_ACCEPTED"
                    self.popup_type = None; return action
                elif self.btn_p_no.collidepoint(e.pos):
                    if self.popup_type == 'RESIGN_CONFIRM': self.add_message("System", "Đã hủy.")
                    elif self.popup_type == 'DRAW_RECEIVE': self.add_message("Bạn", "Đã từ chối.")
                    self.popup_type = None; return None
                return None

            # Emoji Button & Panel
            if self.btn_emoji.collidepoint(e.pos):
                self.show_emoji_panel = not self.show_emoji_panel; return None

            if self.show_emoji_panel:
                for i, rect in enumerate(self.emoji_rects):
                    if rect.collidepoint(e.pos):
                        code = f"[emo{i+1}]" 
                        self.add_message("Bạn", code)
                        if network_manager: network_manager.send_chat(code)
                        self.show_emoji_panel = False; return None

            # Input & Game Buttons
            if self.input_rect.collidepoint(e.pos): self.input_active = True; self.show_emoji_panel = False
            else: self.input_active = False
            
            if self.btn_draw.collidepoint(e.pos):
                action = "OFFER_DRAW"
                if network_manager: network_manager.send_command("DRAW_OFFER")
                self.add_message("Bạn", "Đã gửi lời cầu hòa...")
            elif self.btn_resign.collidepoint(e.pos): self.popup_type = 'RESIGN_CONFIRM'

        elif e.type == pygame.KEYDOWN and self.input_active and not self.popup_type:
            if e.key == pygame.K_RETURN:
                if self.input_text:
                    msg = self.input_text
                    self.add_message("Bạn", msg)
                    if network_manager: network_manager.send_chat(msg)
                    self.input_text = ""
            elif e.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
            else:
                if len(self.input_text) < 40: self.input_text += e.unicode
        
        return action

    def add_message(self, sender, text):
        if text == "Đối thủ muốn hòa": self.popup_type = 'DRAW_RECEIVE'
        self.messages.append((sender, text))
        if len(self.messages) > 20: self.messages.pop(0)

    def draw(self, surface, game_logic):
        # Tắt popup nếu game kết thúc
        if game_logic.game_over:
            self.popup_type = None

        # 1. Vẽ nền Sidebar
        pygame.draw.rect(surface, (30, 30, 35), self.rect)
        pygame.draw.line(surface, (100, 100, 100), (self.rect.x, self.rect.y), (self.rect.x, self.rect.bottom), 2)

        # 2. [ĐÃ KHÔI PHỤC] HIỂN THỊ TRẠNG THÁI (LƯỢT AI)
        current_turn = game_logic.current_turn
        my_color = getattr(game_logic, 'my_color', None)
        
        status_text = ""
        text_color = WHITE
        
        # A. Nếu Game đã kết thúc
        if game_logic.winner:
            if game_logic.winner == "draw":
                status_text = "VÁN ĐẤU HÒA!"
                text_color = (200, 200, 200)
            elif my_color and game_logic.winner == my_color:
                status_text = "🎉 BẠN THẮNG! 🎉"
                text_color = (255, 215, 0) # Màu vàng Gold
            elif my_color and game_logic.winner != my_color:
                status_text = "💀 BẠN THUA!"
                text_color = (255, 50, 50) # Màu đỏ
            else:
                # Trường hợp chơi Offline hoặc xem
                w_name = "TRẮNG/ĐỎ" if game_logic.winner == 'white' else "ĐEN"
                status_text = f"{w_name} THẮNG!"
                text_color = (255, 215, 0)

        # B. Nếu Game đang chạy
        else:
            turn_vn = "TRẮNG/ĐỎ" if current_turn == 'white' else "ĐEN"
            
            if my_color:
                if current_turn == my_color:
                    # --- LƯỢT MÌNH ---
                    status_text = f"LƯỢT CỦA BẠN"
                    text_color = (100, 255, 100) # Chữ xanh lá nhạt
                else:
                    # --- LƯỢT ĐỐI THỦ ---
                    status_text = f"Lượt Đối Thủ"
                    text_color = (255, 100, 100) # Chữ đỏ nhạt  
            else:
                # Chơi Offline (2 người trên 1 máy)
                status_text = f"Lượt: {turn_vn}"
                text_color = WHITE

        # Vẽ chữ trạng thái (Có xử lý lỗi font)
        try:
            txt_surf = self.font.render(status_text, True, text_color)
        except:
            # Fallback nếu font lỗi
            font_big = pygame.font.SysFont("Arial", 25, bold=True)
            txt_surf = font_big.render(status_text, True, text_color)
            
        # Căn giữa chữ trạng thái trong Sidebar
        text_x = self.rect.centerx - txt_surf.get_width() // 2
        surface.blit(txt_surf, (text_x, self.rect.y + 20))

        # -----------------------------------------------------------
        # CÁC PHẦN DƯỚI (CHAT BONG BÓNG, EMOJI...) GIỮ NGUYÊN
        # -----------------------------------------------------------

        # 3. Vẽ Lịch Sử Chat (Bong bóng)
        pygame.draw.rect(surface, (20, 20, 20), self.history_rect) 
        self.voice_play_buttons = []
        
        y_cursor = self.history_rect.bottom - 10 
        
        for sender, msg in reversed(self.messages):
            if y_cursor < self.history_rect.y: break
            
            is_me = (sender == "Bạn")
            content_surf = None
            content_type = "TEXT"
            extra_data = None

            # Check Voice
            if msg.startswith("[Voice:") and msg.endswith("s]"):
                content_type = "VOICE"
                duration_str = msg[7:-1]
                content_surf = pygame.Surface((90, 24), pygame.SRCALPHA)
                extra_data = duration_str

            # Check Emoji Ảnh
            elif msg.startswith("[emo") and msg.endswith("]"):
                content_type = "EMOJI"
                try:
                    idx = int(msg[4:-1]) - 1
                    if 0 <= idx < len(self.emoji_images):
                        content_surf = self.emoji_images[idx]
                except: pass
            
            # Check Text thường
            if content_surf is None: 
                content_type = "TEXT"
                text_col = WHITE 
                if sender == "System": text_col = (200, 200, 200)
                content_surf = self.font.render(msg, True, text_col)

            # Tính toán Bong bóng
            bubble_padding = 8
            bubble_w = content_surf.get_width() + bubble_padding * 2
            bubble_h = content_surf.get_height() + bubble_padding * 2
            
            if is_me:
                bubble_x = self.history_rect.right - bubble_w - 10
                bubble_color = (0, 132, 255) 
            else:
                bubble_x = self.history_rect.x + 10
                bubble_color = (60, 60, 60)
                if sender == "System": bubble_color = (100, 50, 50)

            bubble_y = y_cursor - bubble_h
            if bubble_y < self.history_rect.y: break

            bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)

            # Vẽ Bong bóng
            pygame.draw.rect(surface, bubble_color, bubble_rect, border_radius=12)
            
            # Vẽ Nội dung
            content_x = bubble_rect.x + bubble_padding
            content_y = bubble_rect.y + bubble_padding

            if content_type == "TEXT" or content_type == "EMOJI":
                surface.blit(content_surf, (content_x, content_y))
            
            elif content_type == "VOICE":
                play_rect = pygame.Rect(content_x, content_y + 2, 50, 20)
                self.voice_play_buttons.append((play_rect, msg))
                c_btn = (255, 255, 255)
                pygame.draw.rect(surface, c_btn, play_rect, border_radius=10)
                tri_col = bubble_color 
                pygame.draw.polygon(surface, tri_col, [(play_rect.x + 18, play_rect.centery-5), (play_rect.x + 18, play_rect.centery+5), (play_rect.x + 28, play_rect.centery)])
                t_surf = pygame.font.SysFont("Arial", 10).render(extra_data, True, WHITE)
                surface.blit(t_surf, (play_rect.right + 5, play_rect.y + 4))

            y_cursor -= (bubble_h + 5)

        # 4. Vẽ Input
        color_input = (255, 255, 255) if self.input_active else (150, 150, 150)
        pygame.draw.rect(surface, (50, 50, 50), self.input_rect, border_radius=15)
        pygame.draw.rect(surface, color_input, self.input_rect, 2, border_radius=15)
        surface.blit(self.font.render(self.input_text, True, WHITE), (self.input_rect.x + 10, self.input_rect.y + 5))

        # 5. Vẽ Nút Icon Emoji & Mic
        mouse_pos = pygame.mouse.get_pos()
        
        c_emo = (80, 80, 80) if self.btn_emoji.collidepoint(mouse_pos) or self.show_emoji_panel else (50, 50, 50)
        pygame.draw.rect(surface, c_emo, self.btn_emoji, border_radius=5)
        if hasattr(self, 'icon_btn_emoji'):
            icon_rect = self.icon_btn_emoji.get_rect(center=self.btn_emoji.center)
            surface.blit(self.icon_btn_emoji, icon_rect)

        c_mic = (255, 50, 50) if self.is_recording else ((80, 80, 80) if self.btn_mic.collidepoint(mouse_pos) else (50, 50, 50))
        pygame.draw.rect(surface, c_mic, self.btn_mic, border_radius=5)
        cx, cy = self.btn_mic.centerx, self.btn_mic.centery
        pygame.draw.rect(surface, WHITE, (cx-4, cy-7, 8, 14), border_radius=4)
        pygame.draw.line(surface, WHITE, (cx, cy+8), (cx, cy+12), 2)
        pygame.draw.line(surface, WHITE, (cx-6, cy+12), (cx+6, cy+12), 2)

        # 6. Vẽ Bảng Emoji
        if self.show_emoji_panel:
            pygame.draw.rect(surface, (40, 40, 45), self.emoji_panel_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 100, 100), self.emoji_panel_rect, 1, border_radius=5)
            for i, rect in enumerate(self.emoji_rects):
                if i < len(self.emoji_images):
                    c = (80, 80, 90) if rect.collidepoint(mouse_pos) else (50, 50, 60)
                    pygame.draw.rect(surface, c, rect, border_radius=3)
                    img = self.emoji_images[i]
                    img_rect = img.get_rect(center=rect.center)
                    surface.blit(img, img_rect)

        # 7. Vẽ Nút Cầu Hòa / Đầu Hàng
        c_draw = (100, 100, 100) if self.btn_draw.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(surface, c_draw, self.btn_draw, border_radius=5)
        t_draw = self.font.render("Cầu Hòa", True, WHITE)
        surface.blit(t_draw, (self.btn_draw.centerx - t_draw.get_width()//2, self.btn_draw.centery - t_draw.get_height()//2))

        c_resign = (200, 50, 50) if self.btn_resign.collidepoint(mouse_pos) else (150, 30, 30)
        pygame.draw.rect(surface, c_resign, self.btn_resign, border_radius=5)
        t_resign = self.font.render("Đầu Hàng", True, WHITE)
        surface.blit(t_resign, (self.btn_resign.centerx - t_resign.get_width()//2, self.btn_resign.centery - t_resign.get_height()//2))

        # 8. Vẽ Popup
        if self.popup_type:
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            surface.blit(overlay, (self.rect.x, self.rect.y))
            pygame.draw.rect(surface, (60, 60, 70), self.popup_rect, border_radius=10)
            pygame.draw.rect(surface, (255, 255, 255), self.popup_rect, 2, border_radius=10)
            if self.popup_type == 'RESIGN_CONFIRM':
                msg1, msg2, c_y = "Bạn có chắc chắn", "muốn ĐẦU HÀNG?", (200, 50, 50)
            else:
                msg1, msg2, c_y = "Đối thủ cầu hòa.", "Bạn đồng ý không?", (0, 180, 0)
            t1 = self.font.render(msg1, True, WHITE); t2 = self.font.render(msg2, True, WHITE)
            surface.blit(t1, (self.popup_rect.centerx - t1.get_width()//2, self.popup_rect.y + 15))
            surface.blit(t2, (self.popup_rect.centerx - t2.get_width()//2, self.popup_rect.y + 40))
            
            c_yes = c_y if not self.btn_p_yes.collidepoint(mouse_pos) else (min(c_y[0]+50,255), min(c_y[1]+50,255), min(c_y[2]+50,255))
            pygame.draw.rect(surface, c_yes, self.btn_p_yes, border_radius=5)
            t_yes = self.font.render("Có", True, WHITE)
            surface.blit(t_yes, (self.btn_p_yes.centerx - t_yes.get_width()//2, self.btn_p_yes.centery - t_yes.get_height()//2))
            c_no = (100, 100, 100) if not self.btn_p_no.collidepoint(mouse_pos) else (150, 150, 150)
            pygame.draw.rect(surface, c_no, self.btn_p_no, border_radius=5)
            t_no = self.font.render("Không", True, WHITE)
            surface.blit(t_no, (self.btn_p_no.centerx - t_no.get_width()//2, self.btn_p_no.centery - t_no.get_height()//2))