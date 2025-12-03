import pygame
import time
import os
import math
import shutil # Để xóa file tạm
from utils.constants import WHITE, BLACK, RED, BLUE

# [MỚI] Import bộ quản lý âm thanh
try:
    from utils.audio_manager import AudioManager
except ImportError:
    print("Chưa có file utils/audio_manager.py hoặc chưa cài thư viện sounddevice")
    AudioManager = None

class GameSidebar:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        
        # --- TIMER VARIABLES ---
        self.white_time = 600.0 # 10 minutes (seconds)
        self.black_time = 600.0
        self.last_time_update = time.time()
        self.game_active = True # To stop timer when game ends
        
        # --- AUDIO MANAGER ---
        self.audio_mgr = AudioManager() if AudioManager else None
        self.voice_cache = {} # Lưu đường dẫn file âm thanh: {msg_content: filepath}

        # --- CHAT COMPONENT ---
        self.messages = []
        self.input_text = ""
        self.input_active = False
        self.history_rect = pygame.Rect(x + 10, y + 80, w - 20, h - 220)
        
        # [ADJUSTED] Shift history down to make room for Timer
        # Old y was y + 80. Now we need space for timer.
        # Let's say Timer takes 60px.
        self.timer_rect = pygame.Rect(x + 10, y + 50, w - 20, 50)
        # History starts below timer
        self.history_rect = pygame.Rect(x + 10, self.timer_rect.bottom + 10, w - 20, h - 280)
        
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

        if self.emoji_images: self.icon_btn_emoji = self.emoji_images[0]
        else: self.icon_btn_emoji = pygame.Surface((24,24)); self.icon_btn_emoji.fill((255, 200, 0))
        
        # [THÊM] Khởi tạo module âm thanh của Pygame
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except: pass

        # Grid Emoji
        icon_size = 35; padding = 5
        cols = max(1, (w - 20) // (icon_size + padding))
        rows = math.ceil(len(self.emoji_images) / cols)
        panel_h = min(rows * (icon_size + padding) + padding, 300)
        self.emoji_panel_rect = pygame.Rect(x + 10, self.input_rect.y - panel_h - 5, w - 20, panel_h)
        self.emoji_rects = []
        if self.emoji_images:
            for i in range(len(self.emoji_images)):
                r = i // cols; c = i % cols
                rect_x = self.emoji_panel_rect.x + padding + c * (icon_size + padding)
                rect_y = self.emoji_panel_rect.y + padding + r * (icon_size + padding)
                self.emoji_rects.append(pygame.Rect(rect_x, rect_y, icon_size, icon_size))

        # Voice State
        self.is_recording = False
        self.record_start_time = 0
        self.voice_play_buttons = [] 

        # Buttons & Popup
        btn_y = self.input_rect.bottom + 20
        btn_w = (w - 30) // 2
        self.btn_draw = pygame.Rect(x + 10, btn_y, btn_w, 40)     
        self.btn_resign = pygame.Rect(self.btn_draw.right + 10, btn_y, btn_w, 40) 
        self.popup_type = None 
        self.popup_rect = pygame.Rect(x + 10, y + 200, w - 20, 130)
        pw = (self.popup_rect.width - 30) // 2; py = self.popup_rect.bottom - 40
        self.btn_p_yes = pygame.Rect(self.popup_rect.x + 10, py, pw, 30)
        self.btn_p_no = pygame.Rect(self.btn_p_yes.right + 10, py, pw, 30)
    
    # --- [NEW] UPDATE TIMER FUNCTION ---
    def update_timers(self, game_logic):
        """Cập nhật đồng hồ dựa trên lượt đi"""
        
        # [SỬA LẠI] Kiểm tra kết thúc game theo cách cũ của bạn (dựa vào winner)
        # Nếu winner có giá trị (không phải None) -> Game đã xong -> Dừng đếm giờ
        if game_logic.winner:
            return

        current_time = time.time()
        dt = current_time - self.last_time_update
        self.last_time_update = current_time

        # Chặn lỗi tụt giờ khi mới vào game hoặc lag
        if dt > 0.5:
            return

        if not game_logic.promotion_pending: 
            if game_logic.current_turn == 'white':
                self.white_time -= dt
            else:
                self.black_time -= dt

        if self.white_time < 0: self.white_time = 0
        if self.black_time < 0: self.black_time = 0
        
        # Kiểm tra hết giờ
        # Khi hết giờ: Gán người thắng VÀ Khóa bàn cờ (game_over = True)
        if self.white_time == 0 and not game_logic.winner:
             game_logic.winner = 'black'      # Đen thắng
             game_logic.game_over = True      # <--- THÊM DÒNG NÀY ĐỂ KHÓA BÀN CỜ
             self.add_message("System", "Hết giờ! Đen thắng.")
             
        elif self.black_time == 0 and not game_logic.winner:
             game_logic.winner = 'white'      # Trắng thắng
             game_logic.game_over = True      # <--- THÊM DÒNG NÀY ĐỂ KHÓA BÀN CỜ
             self.add_message("System", "Hết giờ! Trắng thắng.")

    def handle_event(self, e, network_manager=None):
        action = None

        # --- [QUAN TRỌNG] XỬ LÝ THU ÂM THẬT ---
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_mic.collidepoint(e.pos):
                if self.audio_mgr:
                    self.is_recording = True
                    self.record_start_time = time.time()
                    print(">> Bắt đầu thu âm...")
                    self.audio_mgr.start_recording()
                else:
                    print(">> Lỗi: Chưa cài thư viện âm thanh!")
                return None

        elif e.type == pygame.MOUSEBUTTONUP:
            if self.is_recording:
                self.is_recording = False
                duration = time.time() - self.record_start_time
                print(f">> Dừng thu âm. ({duration:.1f}s)")
                
                if duration > 0.5 and self.audio_mgr:
                    # 1. Lưu file wav vào máy mình
                    filename = f"voice_sent_{int(time.time())}.wav"
                    path = self.audio_mgr.stop_recording(filename)
                    
                    # 2. Mã hóa thành chuỗi để gửi
                    b64_data = self.audio_mgr.audio_to_string(path)
                    
                    # 3. Tạo tin nhắn protocol: [VOICE:<giây>:<dữ_liệu_base64>]
                    # Lưu ý: Dữ liệu này rất dài, nhưng socket vẫn gửi được
                    full_msg = f"[VOICE:{duration:.1f}:{b64_data}]"
                    
                    # 4. Hiển thị phía mình (Lưu cache để play lại)
                    self.voice_cache[full_msg] = path 
                    self.add_message("Bạn", full_msg) # Add tin nhắn dài vào list
                    
                    # 5. Gửi qua mạng
                    if network_manager: network_manager.send_chat(full_msg)
                
                return None

        if e.type == pygame.MOUSEBUTTONDOWN:
            # --- [QUAN TRỌNG] XỬ LÝ NGHE (PLAY) ---
            for btn_rect, full_msg_content in self.voice_play_buttons:
                if btn_rect.collidepoint(e.pos):
                    print(f">> [LOA] Đang phát âm thanh...")
                    
                    # Kiểm tra xem file đã có trong cache chưa (đã tải chưa)
                    if full_msg_content in self.voice_cache:
                        path = self.voice_cache[full_msg_content]
                        if os.path.exists(path):
                            self.audio_mgr.play_sound(path)
                        else:
                            print("File âm thanh không tồn tại!")
                    else:
                        print("Đang giải mã âm thanh...")
                        # Nếu là tin nhắn nhận được, cần giải mã Base64 ra file
                        try:
                            # Cấu trúc: [VOICE:1.5:ABC...]
                            parts = full_msg_content.split(":") 
                            # parts[0] = [VOICE, parts[1] = 1.5, parts[2] = ABC...]
                            b64_str = parts[2][:-1] # Bỏ dấu ] cuối
                            
                            filename = f"voice_recv_{int(time.time())}_{len(b64_str)}.wav"
                            path = self.audio_mgr.string_to_audio(b64_str, filename)
                            
                            # Lưu vào cache để lần sau bấm không cần giải mã lại
                            self.voice_cache[full_msg_content] = path
                            self.audio_mgr.play_sound(path)
                        except Exception as ex:
                            print(f"Lỗi giải mã voice: {ex}")

                    return None

            # ... (Các phần xử lý Popup, Emoji, Button khác GIỮ NGUYÊN) ...
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

            if self.btn_emoji.collidepoint(e.pos):
                self.show_emoji_panel = not self.show_emoji_panel; return None

            if self.show_emoji_panel:
                for i, rect in enumerate(self.emoji_rects):
                    if rect.collidepoint(e.pos):
                        code = f"[emo{i+1}]" 
                        self.add_message("Bạn", code)
                        if network_manager: network_manager.send_chat(code)
                        self.show_emoji_panel = False; return None

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
        if game_logic.game_over: self.popup_type = None

        # Nền
        pygame.draw.rect(surface, (30, 30, 35), self.rect)
        pygame.draw.line(surface, (100, 100, 100), (self.rect.x, self.rect.y), (self.rect.x, self.rect.bottom), 2)

        # Status
        current_turn = game_logic.current_turn
        my_color = getattr(game_logic, 'my_color', None)
        status_text = ""
        text_color = WHITE
        
        if game_logic.winner:
            w_text = "HÒA!" if game_logic.winner == "draw" else f"{game_logic.winner.upper()} THẮNG"
            status_text = f"KẾT THÚC: {w_text}"
            text_color = (255, 215, 0)
        else:
            turn_vn = "TRẮNG/ĐỎ" if current_turn == 'white' else "ĐEN"
            if my_color:
                if current_turn == my_color:
                    status_text = f"LƯỢT CỦA BẠN"
                    text_color = (100, 255, 100)
                else:
                    status_text = f"Lượt Đối Thủ"
                    text_color = (255, 100, 100)
            else:
                status_text = f"Lượt: {turn_vn}"
                text_color = WHITE

        try: txt_surf = self.font.render(status_text, True, text_color)
        except: txt_surf = pygame.font.SysFont("Arial", 25, bold=True).render(status_text, True, text_color)
        text_x = self.rect.centerx - txt_surf.get_width() // 2
        surface.blit(txt_surf, (text_x, self.rect.y + 20))
        
        def format_t(s): return f"{int(s)//60:02}:{int(s)%60:02}"
        w_str = format_t(self.white_time)
        b_str = format_t(self.black_time)

        # Box dimensions
        box_w = (self.timer_rect.width - 10) // 2
        box_h = 40
        y_timer = self.timer_rect.y

        # White Timer (Left)
        rect_w = pygame.Rect(self.timer_rect.x, y_timer, box_w, box_h)
        # Black Timer (Right)
        rect_b = pygame.Rect(rect_w.right + 10, y_timer, box_w, box_h)

        # Highlight active turn
        col_w = (200, 200, 200)
        col_b = (50, 50, 50)
        border_w = (100, 100, 100)
        border_b = (100, 100, 100)
        width_w = 2
        width_b = 2

        if not game_logic.game_over:
            if game_logic.current_turn == 'white':
                col_w = (240, 240, 240); border_w = (0, 255, 0); width_w = 4
            else:
                col_b = (80, 80, 80); border_b = (0, 255, 0); width_b = 4

        # Draw White
        pygame.draw.rect(surface, col_w, rect_w, border_radius=8)
        pygame.draw.rect(surface, border_w, rect_w, width_w, border_radius=8)
        t_w = self.font.render(w_str, True, BLACK) # White player time in black text
        surface.blit(t_w, (rect_w.centerx - t_w.get_width()//2, rect_w.centery - t_w.get_height()//2))

        # Draw Black
        pygame.draw.rect(surface, col_b, rect_b, border_radius=8)
        pygame.draw.rect(surface, border_b, rect_b, width_b, border_radius=8)
        t_b = self.font.render(b_str, True, WHITE) # Black player time in white text
        surface.blit(t_b, (rect_b.centerx - t_b.get_width()//2, rect_b.centery - t_b.get_height()//2))

        # --- VẼ CHAT ---
        pygame.draw.rect(surface, (20, 20, 20), self.history_rect) 
        self.voice_play_buttons = []
        y_cursor = self.history_rect.bottom - 10 
        
        for sender, msg in reversed(self.messages):
            if y_cursor < self.history_rect.y: break
            is_me = (sender == "Bạn")
            content_surf = None
            content_type = "TEXT"
            extra_data = None

            # [SỬA] Logic hiển thị Voice
            if msg.startswith("[VOICE:"): 
                # msg format: [VOICE:1.5:base64...]
                # Cắt chuỗi để lấy thời gian, không hiển thị mã base64 loằng ngoằng
                try:
                    parts = msg.split(":")
                    seconds = parts[1] # "1.5"
                    content_type = "VOICE"
                    content_surf = pygame.Surface((90, 24), pygame.SRCALPHA)
                    extra_data = f"{seconds}s"
                except:
                    content_type = "TEXT"
                    msg = "[Lỗi Voice Data]" # Nếu tin nhắn bị hỏng

            elif msg.startswith("[emo") and msg.endswith("]"):
                content_type = "EMOJI"
                try:
                    idx = int(msg[4:-1]) - 1
                    if 0 <= idx < len(self.emoji_images):
                        content_surf = self.emoji_images[idx]
                except: pass
            
            if content_surf is None: 
                content_type = "TEXT"
                text_col = WHITE 
                if sender == "System": text_col = (200, 200, 200)
                content_surf = self.font.render(msg, True, text_col)

            # Bubble Calculation
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

            pygame.draw.rect(surface, bubble_color, bubble_rect, border_radius=12)
            content_x = bubble_rect.x + bubble_padding
            content_y = bubble_rect.y + bubble_padding

            if content_type == "TEXT" or content_type == "EMOJI":
                surface.blit(content_surf, (content_x, content_y))
            
            elif content_type == "VOICE":
                # Nút Play
                play_rect = pygame.Rect(content_x, content_y + 2, 50, 20)
                # QUAN TRỌNG: Lưu toàn bộ tin nhắn gốc (msg) vào nút Play để tí nữa giải mã
                self.voice_play_buttons.append((play_rect, msg))
                
                c_btn = (255, 255, 255)
                pygame.draw.rect(surface, c_btn, play_rect, border_radius=10)
                tri_col = bubble_color 
                pygame.draw.polygon(surface, tri_col, [(play_rect.x + 18, play_rect.centery-5), (play_rect.x + 18, play_rect.centery+5), (play_rect.x + 28, play_rect.centery)])
                t_surf = pygame.font.SysFont("Arial", 10).render(extra_data, True, WHITE)
                surface.blit(t_surf, (play_rect.right + 5, play_rect.y + 4))

            y_cursor -= (bubble_h + 5)

        # Input
        color_input = (255, 255, 255) if self.input_active else (150, 150, 150)
        pygame.draw.rect(surface, (50, 50, 50), self.input_rect, border_radius=15)
        pygame.draw.rect(surface, color_input, self.input_rect, 2, border_radius=15)
        surface.blit(self.font.render(self.input_text, True, WHITE), (self.input_rect.x + 10, self.input_rect.y + 5))

        # Icons
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

        # Buttons Draw/Resign & Popup (GIỮ NGUYÊN CODE CŨ)
        # ... (Phần vẽ nút và popup bạn giữ nguyên như cũ nhé) ...
        c_draw = (100, 100, 100) if self.btn_draw.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(surface, c_draw, self.btn_draw, border_radius=5)
        t_draw = self.font.render("Cầu Hòa", True, WHITE)
        surface.blit(t_draw, (self.btn_draw.centerx - t_draw.get_width()//2, self.btn_draw.centery - t_draw.get_height()//2))

        c_resign = (200, 50, 50) if self.btn_resign.collidepoint(mouse_pos) else (150, 30, 30)
        pygame.draw.rect(surface, c_resign, self.btn_resign, border_radius=5)
        t_resign = self.font.render("Đầu Hàng", True, WHITE)
        surface.blit(t_resign, (self.btn_resign.centerx - t_resign.get_width()//2, self.btn_resign.centery - t_resign.get_height()//2))

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