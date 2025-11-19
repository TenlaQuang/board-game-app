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
        
        self.history_rect = pygame.Rect(x + 10, y + 80, w - 20, h - 220)
        self.input_rect = pygame.Rect(x + 10, self.history_rect.bottom + 10, w - 20, 30)

        # --- BUTTONS ---
        btn_y = self.input_rect.bottom + 20
        btn_w = (w - 30) // 2
        self.btn_draw = pygame.Rect(x + 10, btn_y, btn_w, 40)     
        self.btn_resign = pygame.Rect(self.btn_draw.right + 10, btn_y, btn_w, 40) 

        # --- POPUP VARIABLES ---
        self.popup_type = None # 'DRAW_RECEIVE' (Nhận hòa), 'RESIGN_CONFIRM' (Xác nhận đầu hàng)
        self.popup_rect = pygame.Rect(x + 10, y + 200, w - 20, 130)
        
        # Nút trong Popup
        pw = (self.popup_rect.width - 30) // 2
        py = self.popup_rect.bottom - 40
        self.btn_p_yes = pygame.Rect(self.popup_rect.x + 10, py, pw, 30)
        self.btn_p_no = pygame.Rect(self.btn_p_yes.right + 10, py, pw, 30)

    def handle_event(self, e, network_manager=None):
        action = None

        if e.type == pygame.MOUSEBUTTONDOWN:
            # 1. XỬ LÝ POPUP (NẾU ĐANG HIỆN)
            if self.popup_type:
                if self.btn_p_yes.collidepoint(e.pos):
                    # Bấm ĐỒNG Ý
                    if self.popup_type == 'RESIGN_CONFIRM':
                        print(">> Xác nhận đầu hàng")
                        action = "RESIGN" # Báo cho board_ui biết để xử lý thua
                        if network_manager:
                            network_manager.send_command("RESIGN")
                        self.add_message("Bạn", "Đã đầu hàng.")
                    
                    elif self.popup_type == 'DRAW_RECEIVE':
                        print(">> Chấp nhận hòa")
                        if network_manager:
                            network_manager.send_command("DRAW_ACCEPT")
                        self.add_message("Bạn", "Đã chấp nhận hòa!")
                        action = "DRAW_ACCEPTED"

                    self.popup_type = None # Tắt popup
                    return action
                
                elif self.btn_p_no.collidepoint(e.pos):
                    # Bấm TỪ CHỐI / HỦY
                    if self.popup_type == 'RESIGN_CONFIRM':
                        self.add_message("System", "Đã hủy đầu hàng.")
                    elif self.popup_type == 'DRAW_RECEIVE':
                        self.add_message("Bạn", "Đã từ chối hòa.")
                    
                    self.popup_type = None # Tắt popup
                    return None
                
                return None # Chặn click xuyên qua popup

            # 2. XỬ LÝ CÁC NÚT CHÍNH
            if self.input_rect.collidepoint(e.pos):
                self.input_active = True
            else:
                self.input_active = False
            
            if self.btn_draw.collidepoint(e.pos):
                # Cầu hòa: Gửi luôn không cần hỏi lại (hoặc thêm popup nếu muốn)
                action = "OFFER_DRAW"
                if network_manager:
                    network_manager.send_command("DRAW_OFFER")
                self.add_message("Bạn", "Đã gửi lời cầu hòa...")

            elif self.btn_resign.collidepoint(e.pos):
                # Đầu hàng: HIỆN POPUP HỎI LẠI
                self.popup_type = 'RESIGN_CONFIRM'

        # 3. XỬ LÝ PHÍM
        elif e.type == pygame.KEYDOWN and self.input_active and not self.popup_type:
            if e.key == pygame.K_RETURN:
                if self.input_text:
                    msg = self.input_text
                    self.add_message("Bạn", msg)
                    if network_manager:
                        network_manager.send_chat(msg)
                    self.input_text = ""
            elif e.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if len(self.input_text) < 40:
                    self.input_text += e.unicode
        
        return action

    def add_message(self, sender, text):
        # Tự động bật popup khi nhận tin cầu hòa từ đối thủ
        if text == "Đối thủ muốn hòa": 
            self.popup_type = 'DRAW_RECEIVE'
            
        self.messages.append((sender, text))
        if len(self.messages) > 15:
            self.messages.pop(0)

    def draw(self, surface, game_logic):
        # --- [FIX QUAN TRỌNG] TỰ ĐỘNG TẮT POPUP KHI GAME KẾT THÚC ---
        if game_logic.game_over:
            self.popup_type = None
        # ------------------------------------------------------------

        # Vẽ nền
        pygame.draw.rect(surface, (30, 30, 35), self.rect)
        pygame.draw.line(surface, (100, 100, 100), (self.rect.x, self.rect.y), (self.rect.x, self.rect.bottom), 2)

        # Vẽ Thông tin Lượt / Kết quả
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
            status_text = f"Lượt: {turn_vn}"
            if my_color:
                status_text += " (Bạn)" if current_turn == my_color else ""
                text_color = (100, 255, 100) if current_turn == my_color else (200, 200, 200)

        font_big = pygame.font.SysFont("Arial", 20, bold=True)
        try: txt_surf = self.font.render(status_text, True, text_color)
        except: txt_surf = font_big.render(status_text, True, text_color)
        surface.blit(txt_surf, (self.rect.x + 10, self.rect.y + 20))

        # Vẽ Chat
        pygame.draw.rect(surface, (20, 20, 20), self.history_rect)
        y_offset = self.history_rect.bottom - 25
        for sender, msg in reversed(self.messages):
            if y_offset < self.history_rect.y: break
            color = (100, 200, 255) if sender == "Bạn" else ((200, 200, 200) if sender == "System" else (255, 200, 100))
            line_surf = self.font.render(f"{sender}: {msg}", True, color)
            surface.blit(line_surf, (self.history_rect.x + 5, y_offset))
            y_offset -= 25

        # Vẽ Input
        color_input = (255, 255, 255) if self.input_active else (150, 150, 150)
        pygame.draw.rect(surface, (50, 50, 50), self.input_rect, border_radius=5)
        pygame.draw.rect(surface, color_input, self.input_rect, 2, border_radius=5)
        txt_input = self.font.render(self.input_text, True, WHITE)
        surface.blit(txt_input, (self.input_rect.x + 5, self.input_rect.y + 5))

        # Vẽ Nút Chức Năng
        mouse_pos = pygame.mouse.get_pos()
        
        # Nút Cầu Hòa
        c_draw = (100, 100, 100) if self.btn_draw.collidepoint(mouse_pos) else (70, 70, 70)
        pygame.draw.rect(surface, c_draw, self.btn_draw, border_radius=5)
        t_draw = self.font.render("Cầu Hòa", True, WHITE)
        surface.blit(t_draw, (self.btn_draw.centerx - t_draw.get_width()//2, self.btn_draw.centery - t_draw.get_height()//2))

        # Nút Đầu Hàng
        c_resign = (200, 50, 50) if self.btn_resign.collidepoint(mouse_pos) else (150, 30, 30)
        pygame.draw.rect(surface, c_resign, self.btn_resign, border_radius=5)
        t_resign = self.font.render("Đầu Hàng", True, WHITE)
        surface.blit(t_resign, (self.btn_resign.centerx - t_resign.get_width()//2, self.btn_resign.centery - t_resign.get_height()//2))

        # --- VẼ POPUP (NẾU CÓ) ---
        if self.popup_type:
            # Nền tối
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            surface.blit(overlay, (self.rect.x, self.rect.y))

            # Khung
            pygame.draw.rect(surface, (60, 60, 70), self.popup_rect, border_radius=10)
            pygame.draw.rect(surface, (255, 255, 255), self.popup_rect, 2, border_radius=10)

            # Nội dung Popup
            if self.popup_type == 'RESIGN_CONFIRM':
                msg1 = "Bạn có chắc chắn"
                msg2 = "muốn ĐẦU HÀNG?"
                color_yes = (200, 50, 50) # Nút Yes màu đỏ (Cảnh báo)
            else: # DRAW_RECEIVE
                msg1 = "Đối thủ cầu hòa."
                msg2 = "Bạn đồng ý không?"
                color_yes = (0, 180, 0)   # Nút Yes màu xanh

            # Vẽ text
            t1 = self.font.render(msg1, True, WHITE)
            t2 = self.font.render(msg2, True, WHITE)
            surface.blit(t1, (self.popup_rect.centerx - t1.get_width()//2, self.popup_rect.y + 15))
            surface.blit(t2, (self.popup_rect.centerx - t2.get_width()//2, self.popup_rect.y + 40))

            # Nút Đồng ý
            c_yes = color_yes if not self.btn_p_yes.collidepoint(mouse_pos) else (min(color_yes[0]+50,255), min(color_yes[1]+50,255), min(color_yes[2]+50,255))
            pygame.draw.rect(surface, c_yes, self.btn_p_yes, border_radius=5)
            t_yes = self.font.render("Có", True, WHITE)
            surface.blit(t_yes, (self.btn_p_yes.centerx - t_yes.get_width()//2, self.btn_p_yes.centery - t_yes.get_height()//2))

            # Nút Từ chối
            c_no = (100, 100, 100) if not self.btn_p_no.collidepoint(mouse_pos) else (150, 150, 150)
            pygame.draw.rect(surface, c_no, self.btn_p_no, border_radius=5)
            t_no = self.font.render("Không", True, WHITE)
            surface.blit(t_no, (self.btn_p_no.centerx - t_no.get_width()//2, self.btn_p_no.centery - t_no.get_height()//2))