import json
import pygame
import os # Import os để kiểm tra file
from core.board import Board
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR,
    FONTS_DIR 
)
from .assets import XIANGQI_BOARD_IMG
from .chat_box import GameSidebar 

class BoardUI:
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, sidebar_rect=None, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        self.board_rect = board_rect
        self.sidebar_rect = sidebar_rect
        
        self.network_manager = network_manager
        self.my_role = my_role
        
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
        
        # =============================================================================
        # [FIX] LOAD FONT TIẾNG VIỆT CHUẨN
        # =============================================================================
        # 1. Xác định đường dẫn file font
        font_name = "Roboto-Regular.ttf"
        font_path = os.path.join(FONTS_DIR, font_name)
        
        print(f"[FONT] Đang tìm font tại: {font_path}")

        # 2. Hàm helper để load font an toàn
        def load_font(path, size, is_bold=False):
            if os.path.exists(path):
                try:
                    return pygame.font.Font(path, size)
                except Exception as e:
                    print(f"[FONT] Lỗi load file {path}: {e}")
            
            # Fallback: Nếu không thấy file, dùng font hệ thống hỗ trợ tiếng Việt tốt (Segoe UI cho Windows)
            print(f"[FONT] Dùng fallback system font cho size {size}")
            return pygame.font.SysFont("segoeui", size, bold=is_bold)

        # 3. Load các loại font
        self.turn_font     = load_font(font_path, 40, is_bold=True) # Font Lượt đi
        self.fallback_font = load_font(font_path, 30) 
        self.winner_font   = load_font(font_path, 80, is_bold=True) # Font Thắng
        self.info_font     = load_font(font_path, 30)               # Font Hướng dẫn
        self.chat_font     = load_font(font_path, 16)               # Font Chat
        # =============================================================================

        if self.sidebar_rect:
            self.sidebar = GameSidebar(
                self.sidebar_rect.x, self.sidebar_rect.y, 
                self.sidebar_rect.width, self.sidebar_rect.height, 
                self.chat_font 
            )
        else:
            self.sidebar = None

    def _get_board_params(self):
        available_w = self.board_rect.width
        available_h = self.board_rect.height
        cell_size = min(available_w // self.cols, available_h // self.rows)
        board_pixel_w = cell_size * self.cols
        board_pixel_h = cell_size * self.rows
        start_x = self.board_rect.x + (available_w - board_pixel_w) // 2
        start_y = self.board_rect.y + (available_h - board_pixel_h) // 2
        return cell_size, start_x, start_y

    def to_screen_pos(self, logic_r, logic_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - logic_r), (self.cols - 1 - logic_c)
        return logic_r, logic_c

    def from_screen_pos(self, screen_r, screen_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - screen_r), (self.cols - 1 - screen_c)
        return screen_r, screen_c

    def handle_events(self, event: pygame.event.Event):
        if self.sidebar:
            action = self.sidebar.handle_event(event, self.network_manager)
            
            if action == 'RESIGN':
                if self.game_logic.my_color:
                    if self.game_logic.my_color == 'white':
                        self.game_logic.winner = 'black'
                    else:
                        self.game_logic.winner = 'white'
                else:
                    self.game_logic.winner = self.game_logic.opponent_color()
                print(f"Đầu hàng. Người thắng: {self.game_logic.winner}")

            elif action == 'OFFER_DRAW':
                self.sidebar.add_message("System", "Đã gửi lời cầu hòa...")

        if self.game_logic.game_over: return 

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                cell_size, start_x, start_y = self._get_board_params()
                mouse_x, mouse_y = event.pos
                rel_x = mouse_x - start_x
                rel_y = mouse_y - start_y
                
                if 0 <= rel_x < (cell_size * self.cols) and 0 <= rel_y < (cell_size * self.rows):
                    if not self.game_logic.is_my_turn(): 
                        print("Không phải lượt của bạn!")
                        return

                    screen_col = int(rel_x // cell_size)
                    screen_row = int(rel_y // cell_size)
                    logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)

                    if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                        self._process_move_logic((logic_row, logic_col))

    def _process_move_logic(self, clicked_pos):
        if self.selected_piece_pos:
            from_pos = self.selected_piece_pos
            to_pos = clicked_pos
            
            if to_pos in self.possible_moves:
                move_success = self.game_logic.move_piece(from_pos, to_pos)
                if move_success and self.network_manager:
                    move_data = {
                        "type": "move", "from": from_pos, "to": to_pos,
                        "game_type": self.game_logic.game_type
                    }
                    self.network_manager.send_to_p2p(move_data)
                self.selected_piece_pos = None; self.possible_moves = []
            else:
                new_piece = self.game_logic.get_piece(clicked_pos)
                current_piece = self.game_logic.get_piece(from_pos)
                if new_piece and current_piece and new_piece.color == current_piece.color:
                    self.selected_piece_pos = clicked_pos
                    self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic.board, clicked_pos, self.game_logic.current_turn)
                    return 
                self.selected_piece_pos = None; self.possible_moves = []
        else:
            piece = self.game_logic.get_piece(clicked_pos)
            if piece:
                if self.game_logic.my_color and piece.color != self.game_logic.my_color: return
                self.selected_piece_pos = clicked_pos
                self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic.board, clicked_pos, self.game_logic.current_turn)

    def update(self):
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
                            self.sidebar.add_message("System", "Đối thủ đã đầu hàng!")
                            self.game_logic.winner = self.game_logic.my_color 
                        elif cmd == "DRAW_OFFER":
                            self.sidebar.add_message("System", "Đối thủ muốn hòa")
                except Exception as e: print(f"Lỗi update mạng: {e}")

    def draw(self):
        pygame.draw.rect(self.screen, (20, 20, 20), self.board_rect)

        if self.sidebar:
            turn_text_color = (255, 255, 255)
            turn_display_text = ""
            if self.game_logic.my_color:
                if self.game_logic.current_turn == self.game_logic.my_color:
                    turn_display_text = "Lượt đi: CỦA BẠN"
                    turn_text_color = (100, 255, 100)
                else:
                    turn_display_text = "Lượt đi: ĐỐI THỦ"
                    turn_text_color = (255, 100, 100)
            else:
                if self.game_logic.current_turn == 'white':
                    turn_display_text = "Lượt đi: TRẮNG"
                    turn_text_color = (255, 255, 255)
                else:
                    turn_display_text = "Lượt đi: ĐEN"
                    turn_text_color = (150, 150, 150)
            
            # Căn chỉnh lại vị trí text "Lượt đi" cho đẹp
            turn_surface = self.turn_font.render(turn_display_text, True, turn_text_color)
            # Căn giữa theo chiều ngang của Sidebar
            text_x = self.sidebar_rect.x + (self.sidebar_rect.width - turn_surface.get_width()) // 2
            self.screen.blit(turn_surface, (text_x, self.sidebar_rect.y + 30))
            
            self.sidebar.draw(self.screen, self.game_logic)

        cell_size, start_x, start_y = self._get_board_params()

        self.draw_board_squares(cell_size, start_x, start_y)
        self.draw_highlights(cell_size, start_x, start_y)
        self.draw_pieces(cell_size, start_x, start_y)
        
        if self.game_logic.game_over:
            self.draw_game_over_message()

    def draw_board_squares(self, cell_size, start_x, start_y):
        if self.game_logic.game_type == 'chess':
            for r in range(self.rows):
                for c in range(self.cols):
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    pygame.draw.rect(self.screen, color, 
                        (start_x + c * cell_size, start_y + r * cell_size, cell_size, cell_size))
        else: 
            if XIANGQI_BOARD_IMG:
                board_w = cell_size * self.cols
                board_h = cell_size * self.rows
                scaled_bg = pygame.transform.scale(XIANGQI_BOARD_IMG, (board_w, board_h))
                self.screen.blit(scaled_bg, (start_x, start_y))

    def draw_pieces(self, cell_size, start_x, start_y):
        board_state = self.game_logic.get_board_state()
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol = board_state[logic_r][logic_c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                    center_x = start_x + screen_c * cell_size + cell_size // 2
                    center_y = start_y + screen_r * cell_size + cell_size // 2

                    if image:
                        piece_scale = int(cell_size * 0.95)
                        scaled_img = pygame.transform.smoothscale(image, (piece_scale, piece_scale))
                        img_rect = scaled_img.get_rect(center=(center_x, center_y))
                        self.screen.blit(scaled_img, img_rect)
                    else:
                        text = self.fallback_font.render(symbol, True, (255,0,0))
                        self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))

    def draw_highlights(self, cell_size, start_x, start_y):
        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                s.fill((0, 200, 0, 100)) 
                self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))

        if self.selected_piece_pos:
            screen_r, screen_c = self.to_screen_pos(*self.selected_piece_pos)
            rect_x = start_x + screen_c * cell_size
            rect_y = start_y + screen_r * cell_size
            s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            s.fill((*HIGHLIGHT_COLOR, 100)) 
            self.screen.blit(s, (rect_x, rect_y))

    def draw_game_over_message(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        winner = self.game_logic.winner
        if self.game_logic.game_type == 'chess':
            text = "TRẮNG THẮNG!" if winner == 'white' else "ĐEN THẮNG!"
        else:
            text = "ĐỎ THẮNG!" if winner == 'white' else "ĐEN THẮNG!"
            
        color = (255, 50, 50) if winner == 'white' else (100, 100, 255)
        
        text_win_surf = self.winner_font.render(text, True, color)
        text_win_rect = text_win_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(text_win_surf, text_win_rect)
        
        sub_text_surf = self.info_font.render("Nhấn ESC để thoát", True, (200,200,200))
        sub_text_rect = sub_text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        self.screen.blit(sub_text_surf, sub_text_rect)