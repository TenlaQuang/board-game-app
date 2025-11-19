# ui/board_ui.py (Bản Final 5: Fix triệt để lỗi hiển thị tên màu & Giữ nguyên đồ họa đẹp)
import json
import pygame
import os
from core.board import Board
from utils.constants import (
    WIDTH, HEIGHT,
    HIGHLIGHT_COLOR,
    FONTS_DIR 
)
from .chat_box import GameSidebar 
import pygame_gui
from pygame_gui.windows import UIConfirmationDialog

# --- CẤU HÌNH MÀU SẮC ---

# 1. Màu nền Cờ Tướng (Gỗ sáng)
XIANGQI_BG_COLOR = (210, 160, 100) 

# 2. Màu nền Cờ Vua (Green Theme)
CHESS_LIGHT_COLOR = (238, 238, 210) # Màu kem
CHESS_DARK_COLOR = (118, 150, 86)   # Màu xanh lá đậm

# Màu Cờ Tướng 3D
PIECE_BODY_COLOR = (139, 69, 19)
PIECE_FACE_COLOR = (238, 216, 174)

# Màu Highlight Cờ Vua
CHESS_HINT_COLOR = (247, 247, 105, 120) # Vàng chanh trong suốt
CHESS_SELECTED_COLOR = (186, 202, 68, 160) # Xanh vàng khi chọn

CHECK_GLOW_COLOR = (255, 0, 0, 200)    # Đỏ rực (Chiếu tướng)

class BoardUI:
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, sidebar_rect=None, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        self.board_rect = board_rect
        self.sidebar_rect = sidebar_rect
        
        self.network_manager = network_manager
        self.my_role = my_role
        
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')
        self.confirmation_dialog = None 
        
        # --- LOAD ẢNH BÀN CỜ TƯỚNG ---
        self.board_img = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(current_dir, 'assets', 'images', 'xiangqi_board.png')
            if os.path.exists(img_path):
                self.board_img = pygame.image.load(img_path).convert()
            else:
                print(f"CẢNH BÁO: Không tìm thấy ảnh tại {img_path}")
        except Exception as e:
            print(f"LỖI LOAD ẢNH: {e}")

        if self.my_role == 'host':
            self.game_logic.set_player_color('white') 
        elif self.my_role == 'client':
            self.game_logic.set_player_color('black')
        else:
            self.game_logic.set_player_color(None) 
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        self.selected_piece_pos = None
        self.possible_moves = []
        
        # Load fonts
        font_name = "Roboto-Regular.ttf"
        font_path = os.path.join(FONTS_DIR, font_name)
        
        def load_font(path, size, is_bold=False):
            if os.path.exists(path):
                try: return pygame.font.Font(path, size)
                except: pass
            return pygame.font.SysFont("segoeui", size, bold=is_bold)

        self.turn_font = load_font(font_path, 30, is_bold=True)
        self.fallback_font = load_font(font_path, 30) 
        self.winner_font = load_font(font_path, 80, is_bold=True)
        self.info_font = load_font(font_path, 30)
        self.chat_font = load_font(font_path, 16)
        self.coord_font = load_font(font_path, 14, is_bold=True)

        if self.sidebar_rect:
            self.sidebar = GameSidebar(
                self.sidebar_rect.x, self.sidebar_rect.y, 
                self.sidebar_rect.width, self.sidebar_rect.height, 
                self.chat_font 
            )
        else:
            self.sidebar = None

    # --- HÀM QUAN TRỌNG: LẤY TÊN MÀU CHUẨN ---
    def get_color_name(self, color_code):
        """
        Chuyển đổi mã màu (white/black) sang tên tiếng Việt chuẩn xác theo loại game.
        """
        if self.game_logic.game_type == 'chess':
            # Cờ Vua: White = Trắng, Black = Đen
            return "TRẮNG" if color_code == 'white' else "ĐEN"
        else:
            # Cờ Tướng: White (đi trước) = Đỏ, Black = Đen
            return "ĐỎ" if color_code == 'white' else "ĐEN"
    # -------------------------------------------

    def _get_board_params(self):
        available_w = self.board_rect.width
        available_h = self.board_rect.height
        
        border_size = 30 if self.game_logic.game_type == 'chess' else 0
        
        safe_w = available_w - border_size * 2
        safe_h = available_h - border_size * 2
        
        cell_size = min(safe_w // self.cols, safe_h // self.rows)
        
        board_pixel_w = cell_size * self.cols
        board_pixel_h = cell_size * self.rows
        
        start_x = self.board_rect.x + (available_w - board_pixel_w) // 2
        start_y = self.board_rect.y + (available_h - board_pixel_h) // 2
        
        return cell_size, start_x, start_y, border_size

    def to_screen_pos(self, logic_r, logic_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - logic_r), (self.cols - 1 - logic_c)
        return logic_r, logic_c

    def from_screen_pos(self, screen_r, screen_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - screen_r), (self.cols - 1 - screen_c)
        return screen_r, screen_c

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'QUIT_GAME'

        self.ui_manager.process_events(event)

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.confirmation_dialog:
                self.game_logic.game_over = True
                self.game_logic.winner = "draw"
                if self.network_manager:
                    self.network_manager.send_command("DRAW_ACCEPT")
                self.confirmation_dialog = None
        
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
             if event.ui_element == self.confirmation_dialog:
                 self.confirmation_dialog = None

        if self.sidebar:
            action = self.sidebar.handle_event(event, self.network_manager)
            if action == 'RESIGN':
                opponent_color = 'black' if self.game_logic.my_color == 'white' else 'white'
                self.game_logic.winner = opponent_color
                self.game_logic.game_over = True
                if self.confirmation_dialog: 
                    self.confirmation_dialog.kill(); self.confirmation_dialog = None
            elif action == 'OFFER_DRAW':
                self.sidebar.add_message("Hệ thống", "Đã gửi lời cầu hòa...")

        if self.game_logic.game_over: return 

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                cell_size, start_x, start_y, _ = self._get_board_params()
                mouse_x, mouse_y = event.pos
                rel_x = mouse_x - start_x
                rel_y = mouse_y - start_y
                
                board_pixel_w = cell_size * self.cols
                board_pixel_h = cell_size * self.rows
                
                if 0 <= rel_x < board_pixel_w and 0 <= rel_y < board_pixel_h:
                    if not self.game_logic.is_my_turn(): return
                    screen_col = int(rel_x // cell_size)
                    screen_row = int(rel_y // cell_size)
                    logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)
                    if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                        self._process_move_logic((logic_row, logic_col))
        return None

    def _process_move_logic(self, clicked_pos):
        if self.selected_piece_pos:
            from_pos = self.selected_piece_pos
            to_pos = clicked_pos
            if to_pos in self.possible_moves:
                move_success = self.game_logic.move_piece(from_pos, to_pos)
                if move_success and self.network_manager:
                    move_data = {"type": "move", "from": from_pos, "to": to_pos, "game_type": self.game_logic.game_type}
                    self.network_manager.send_to_p2p(move_data)
                self.selected_piece_pos = None; self.possible_moves = []
            else:
                new_piece = self.game_logic.get_piece(clicked_pos)
                current_piece = self.game_logic.get_piece(from_pos)
                if new_piece and current_piece and new_piece.color == current_piece.color:
                    self.selected_piece_pos = clicked_pos
                    self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic, clicked_pos, self.game_logic.current_turn)
                    return 
                self.selected_piece_pos = None; self.possible_moves = []
        else:
            piece = self.game_logic.get_piece(clicked_pos)
            if piece:
                if self.game_logic.my_color and piece.color != self.game_logic.my_color: return
                self.selected_piece_pos = clicked_pos
                self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic, clicked_pos, self.game_logic.current_turn)

    def update(self):
        self.ui_manager.update(0.016)
        if self.network_manager:
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    msg_type = msg.get("type")
                    if msg_type == "move":
                        from_pos = tuple(msg["from"])
                        to_pos = tuple(msg["to"])
                        self.game_logic.move_piece(from_pos, to_pos)
                    elif msg_type == "chat":
                        if self.sidebar: self.sidebar.add_message("Đối thủ", msg["content"])
                    elif msg_type == "command":
                        cmd = msg["content"]
                        if cmd == "RESIGN":
                            self.sidebar.add_message("Hệ thống", "Đối thủ đã đầu hàng!")
                            self.game_logic.winner = self.game_logic.my_color; self.game_logic.game_over = True
                            if self.confirmation_dialog: self.confirmation_dialog.kill(); self.confirmation_dialog = None
                        elif cmd == "DRAW_OFFER":
                            self.sidebar.add_message("Hệ thống", "Đối thủ muốn hòa...")
                            if self.confirmation_dialog is None and not self.game_logic.game_over:
                                rect = pygame.Rect(0, 0, 300, 200)
                                rect.center = (WIDTH//2, HEIGHT//2)
                                self.confirmation_dialog = UIConfirmationDialog(rect=rect, manager=self.ui_manager, window_title="Cầu Hòa", action_long_desc="Đối thủ muốn cầu hòa. Bạn đồng ý không?", action_short_name="Đồng ý", blocking=True)
                        elif cmd == "DRAW_ACCEPT":
                            self.sidebar.add_message("Hệ thống", "Hai bên đã hòa!")
                            self.game_logic.winner = "draw"; self.game_logic.game_over = True
                            if self.confirmation_dialog: self.confirmation_dialog.kill(); self.confirmation_dialog = None
                except Exception as e: print(f"Lỗi update mạng: {e}")

    def draw(self):
        bg_color = XIANGQI_BG_COLOR if self.game_logic.game_type != 'chess' else (48, 46, 43) 
        
        pygame.draw.rect(self.screen, bg_color, self.board_rect)

        if self.sidebar:
            # --- FIX LỖI HIỂN THỊ TEXT ---
            turn_display_text = ""
            # Lấy tên màu chuẩn xác
            current_turn_vn = self.get_color_name(self.game_logic.current_turn)
            
            if self.game_logic.my_color:
                if self.game_logic.current_turn == self.game_logic.my_color:
                    turn_display_text = f"Lượt: {current_turn_vn} (Bạn)"
                    turn_text_color = (100, 255, 100)
                else:
                    turn_display_text = f"Lượt: {current_turn_vn} (Đối thủ)"
                    turn_text_color = (255, 100, 100)
            else:
                turn_display_text = f"Lượt: {current_turn_vn}"
                turn_text_color = (255, 255, 255)

            turn_surface = self.turn_font.render(turn_display_text, True, turn_text_color)
            text_x = self.sidebar_rect.x + (self.sidebar_rect.width - turn_surface.get_width()) // 2
            self.screen.blit(turn_surface, (text_x, self.sidebar_rect.y + 30))
            self.sidebar.draw(self.screen, self.game_logic)

        cell_size, start_x, start_y, border_size = self._get_board_params()
        
        self.draw_board_squares(cell_size, start_x, start_y, border_size)
        self.draw_highlight_king_in_check(cell_size, start_x, start_y)
        self.draw_pieces(cell_size, start_x, start_y)
        self.draw_highlights(cell_size, start_x, start_y)
        
        if self.game_logic.game_over:
            self.draw_game_over_message()
            
        self.ui_manager.draw_ui(self.screen)

    def draw_game_over_message(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        winner = self.game_logic.winner
        if winner == "draw":
            text = "HÒA!"
            color = (200, 200, 200)
        elif self.game_logic.my_color: 
            if winner == self.game_logic.my_color:
                text = "BẠN THẮNG!"
                color = (100, 255, 100) 
            else:
                text = "BẠN THUA!"
                color = (255, 50, 50) 
        else: 
            # Fix cả tên màu khi hiển thị người thắng cuộc
            winner_vn = self.get_color_name(winner)
            text = f"{winner_vn} THẮNG!"
            color = (255, 215, 0) 

        text_win_surf = self.winner_font.render(text, True, color)
        text_win_rect = text_win_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(text_win_surf, text_win_rect)
        
        sub_text_surf = self.info_font.render("Nhấn ESC để thoát", True, (200,200,200))
        sub_text_rect = sub_text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        self.screen.blit(sub_text_surf, sub_text_rect)
    
    def draw_board_squares(self, cell_size, start_x, start_y, border_size):
        if self.game_logic.game_type == 'chess':
            if border_size > 0:
                border_color = (0, 0, 0) 
                pygame.draw.rect(self.screen, border_color, 
                                 (start_x - border_size, start_y - border_size, 
                                  cell_size * 8 + border_size*2, cell_size * 8 + border_size*2))
                
                pygame.draw.rect(self.screen, (100, 100, 100), 
                                (start_x - 2, start_y - 2, 
                                 cell_size * 8 + 4, cell_size * 8 + 4), 2)

                files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
                
                if self.game_logic.my_color == 'black':
                    files = files[::-1]
                    ranks = ranks[::-1]

                for i in range(8):
                    text = self.coord_font.render(ranks[i], True, CHESS_LIGHT_COLOR)
                    self.screen.blit(text, (start_x - border_size + 8, start_y + i*cell_size + 8))
                    
                    text = self.coord_font.render(files[i], True, CHESS_LIGHT_COLOR)
                    self.screen.blit(text, (start_x + i*cell_size + cell_size - 15, start_y + 8*cell_size + 4))

            for r in range(self.rows):
                for c in range(self.cols):
                    color = CHESS_LIGHT_COLOR if (r + c) % 2 == 0 else CHESS_DARK_COLOR
                    pygame.draw.rect(self.screen, color, (start_x + c * cell_size, start_y + r * cell_size, cell_size, cell_size))
        else: 
            if self.board_img:
                board_w = cell_size * self.cols; board_h = cell_size * self.rows
                scaled_bg = pygame.transform.smoothscale(self.board_img, (board_w, board_h))
                self.screen.blit(scaled_bg, (start_x, start_y), special_flags=pygame.BLEND_MULT)
            else:
                for r in range(self.rows):
                    pygame.draw.line(self.screen, (0,0,0), (start_x, start_y + r*cell_size + cell_size//2), (start_x + (self.cols-1)*cell_size, start_y + r*cell_size + cell_size//2), 2)
                for c in range(self.cols):
                    pygame.draw.line(self.screen, (0,0,0), (start_x + c*cell_size + cell_size//2, start_y), (start_x + c*cell_size + cell_size//2, start_y + (self.rows-1)*cell_size), 2)

    def draw_highlight_king_in_check(self, cell_size, start_x, start_y):
        is_check = False
        if hasattr(self.game_logic, 'is_check'):
             is_check = self.game_logic.is_check
        elif hasattr(self.game_logic, 'validator') and hasattr(self.game_logic.validator, 'is_in_check'):
             is_check = self.game_logic.validator.is_in_check(self.game_logic, self.game_logic.current_turn)

        if is_check:
            king_symbol = 'K' if self.game_logic.current_turn == 'white' else 'k'
            board_state = self.game_logic.get_board_state()
            
            for r in range(self.rows):
                for c in range(self.cols):
                    if board_state[r][c] == king_symbol:
                        screen_r, screen_c = self.to_screen_pos(r, c)
                        s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                        
                        if self.game_logic.game_type == 'chess':
                             s.fill((255, 0, 0, 150)) 
                        else:
                            pygame.draw.circle(s, (255, 0, 0, 100), (cell_size//2, cell_size//2), cell_size//2)
                            pygame.draw.circle(s, (255, 0, 0, 180), (cell_size//2, cell_size//2), cell_size//2.5)
                            
                        self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))
                        return

    def draw_pieces(self, cell_size, start_x, start_y):
        board_state = self.game_logic.get_board_state()
        
        piece_radius = int(cell_size // 2 * 0.85) 
        piece_thickness = 6 
        
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol = board_state[logic_r][logic_c]
                if symbol:
                    screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                    center_x = start_x + screen_c * cell_size + cell_size // 2
                    center_y = start_y + screen_r * cell_size + cell_size // 2
                    
                    if self.game_logic.game_type == 'chess':
                        image = self.piece_assets.get(symbol)
                        if image:
                            main_size = int(cell_size * 0.75)
                            outline_size = main_size + 6 

                            outline_img = pygame.transform.smoothscale(image, (outline_size, outline_size))
                            outline_img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
                            
                            main_img = pygame.transform.smoothscale(image, (main_size, main_size))

                            outline_rect = outline_img.get_rect(center=(center_x, center_y))
                            self.screen.blit(outline_img, outline_rect)

                            img_rect = main_img.get_rect(center=(center_x, center_y))
                            self.screen.blit(main_img, img_rect)
                    else:
                        shadow_offset_y = piece_thickness + 3
                        pygame.draw.circle(self.screen, (0, 0, 0, 60), (center_x + 2, center_y + shadow_offset_y), piece_radius)
                        for i in range(piece_thickness):
                            draw_y = center_y + piece_thickness - i
                            pygame.draw.circle(self.screen, PIECE_BODY_COLOR, (center_x, draw_y), piece_radius)
                        pygame.draw.circle(self.screen, PIECE_FACE_COLOR, (center_x, center_y), piece_radius)
                        
                        image = self.piece_assets.get(symbol)
                        if image:
                            piece_scale = int(cell_size * 0.85)
                            scaled_img = pygame.transform.smoothscale(image, (piece_scale, piece_scale))
                            img_rect = scaled_img.get_rect(center=(center_x, center_y))
                            self.screen.blit(scaled_img, img_rect)
                        else:
                            text = self.fallback_font.render(symbol, True, (255,0,0))
                            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))

    def draw_highlights(self, cell_size, start_x, start_y):
        board_state = self.game_logic.get_board_state()

        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                
                if self.game_logic.game_type == 'chess':
                    s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                    s.fill(CHESS_HINT_COLOR) 
                    self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))
                else:
                    center_x = start_x + screen_c * cell_size + cell_size // 2
                    center_y = start_y + screen_r * cell_size + cell_size // 2
                    has_piece = board_state[logic_r][logic_c] is not None
                    s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                    if has_piece:
                        radius = int(cell_size // 2 * 0.9) + 2
                        pygame.draw.circle(s, (0, 255, 0, 200), (cell_size//2, cell_size//2), radius, 4)
                    else:
                        pygame.draw.circle(s, (0, 200, 0, 180), (cell_size//2, cell_size//2), cell_size // 6)
                    self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))

        if self.selected_piece_pos:
            screen_r, screen_c = self.to_screen_pos(*self.selected_piece_pos)
            rect_x = start_x + screen_c * cell_size
            rect_y = start_y + screen_r * cell_size
            
            if self.game_logic.game_type == 'chess':
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                s.fill(CHESS_SELECTED_COLOR)
                self.screen.blit(s, (rect_x, rect_y))
            else:
                center_x = cell_size // 2
                center_y = cell_size // 2
                radius = int(cell_size // 2 * 0.9) + 2
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 215, 0, 200), (center_x, center_y), radius, 4)
                self.screen.blit(s, (rect_x, rect_y))