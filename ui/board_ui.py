import json
import threading
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
from pygame_gui.elements import UIWindow, UIButton, UIImage, UIPanel

# --- CẤU HÌNH MÀU SẮC ---
XIANGQI_BG_COLOR = (210, 160, 100) 
CHESS_LIGHT_COLOR = (238, 238, 210) 
CHESS_DARK_COLOR = (118, 150, 86)   

PIECE_BODY_COLOR = (139, 69, 19)
PIECE_FACE_COLOR = (238, 216, 174)

CHESS_HINT_COLOR = (247, 247, 105, 120) 
CHESS_SELECTED_COLOR = (186, 202, 68, 160)
CHECK_GLOW_COLOR = (255, 0, 0, 200)

# --- HELPER ---
def get_piece_info(piece_data):
    if piece_data is None: return None, None
    if hasattr(piece_data, 'symbol'): return piece_data.symbol, piece_data.color
    s = str(piece_data)
    return s, ('white' if s.isupper() else 'black')

# --- CLASS HỘP THOẠI PHONG CẤP ---
class PromotionWindow(UIWindow):
    def __init__(self, rect, manager, piece_assets, player_color):
        target_width = max(rect.width, 500) 
        padding = 20
        btn_size = (target_width - padding * 5) // 4
        target_height = 57 + padding + btn_size + padding
        rect = pygame.Rect(rect.x, rect.y, target_width + 35, target_height)

        super().__init__(rect, manager, window_display_title="Chọn Quân Phong Cấp")
        
        self.background_colour = pygame.Color(40, 40, 40, 220)
        self.rebuild()

        self.btn_map = {}
        options = ['q', 'r', 'b', 'n'] # Hậu, Xe, Tượng, Mã

        panel = UIPanel(
            relative_rect=pygame.Rect(0, 0, target_width, target_height - 30),
            starting_height=1,
            manager=manager,
            container=self
        )

        for i, char in enumerate(options):
            symbol = char.upper() if player_color == 'white' else char.lower()
            x = padding + i * (btn_size + padding)
            y = 10 
            
            btn_rect = pygame.Rect(x, y, btn_size, btn_size)
            btn = UIButton(
                relative_rect=btn_rect,
                text="",
                manager=manager,
                container=panel,
                object_id=f"#promotion_btn"
            )
            self.btn_map[btn] = char

            if symbol in piece_assets:
                img = piece_assets[symbol]
                icon_size = btn_size - 22
                img_scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                img_rect = pygame.Rect(
                    x + (btn_size - icon_size) // 2,
                    y + (btn_size - icon_size) // 2,
                    icon_size,
                    icon_size
                )
                UIImage(
                    relative_rect=img_rect,
                    image_surface=img_scaled,
                    manager=manager,
                    container=panel,
                    object_id="#promotion_icon"
                )

    def check_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.btn_map:
                return self.btn_map[event.ui_element]
        return None


class BoardUI:
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, sidebar_rect=None, network_manager=None, my_role=None, ai_engine=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        self.ai_engine = ai_engine # Lưu lại AI
        self.is_ai_thinking = False
        # Nếu chơi với máy, mình cầm Trắng, Máy cầm Đen
        if self.ai_engine:
            self.game_logic.set_player_color('white')
        
        self.board_rect = board_rect
        self.sidebar_rect = sidebar_rect
        
        self.network_manager = network_manager
        self.my_role = my_role
        
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')
        self.confirmation_dialog = None 
        
        self.promotion_window = None 
        self.pending_promotion_move = None 
        
        self.board_img = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(current_dir, 'assets', 'images', 'xiangqi_board.png')
            if os.path.exists(img_path):
                self.board_img = pygame.image.load(img_path).convert_alpha()
        except Exception: pass

        if self.my_role == 'host':
            self.game_logic.set_player_color('white') 
        elif self.my_role == 'client':
            self.game_logic.set_player_color('black')
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        self.selected_piece_pos = None
        self.possible_moves = []
        
        font_name = "Roboto-Regular.ttf"
        font_path = os.path.join(FONTS_DIR, font_name)
        def load_font(path, size, is_bold=False):
            try: return pygame.font.Font(path, size)
            except: return pygame.font.SysFont("segoeui", size, bold=is_bold)

        self.turn_font = load_font(font_path, 30, is_bold=True)
        self.fallback_font = load_font(font_path, 30) 
        self.winner_font = load_font(font_path, 80, is_bold=True)
        self.info_font = load_font(font_path, 30)
        self.chat_font = load_font(font_path, 16)
        self.coord_font = load_font(font_path, 14, is_bold=True)

        if self.sidebar_rect:
            self.sidebar = GameSidebar(self.sidebar_rect.x, self.sidebar_rect.y, self.sidebar_rect.width, self.sidebar_rect.height, self.chat_font)
        else:
            self.sidebar = None

    def get_color_name(self, color_code):
        if self.game_logic.game_type == 'chess':
            return "TRẮNG" if color_code == 'white' else "ĐEN"
        else:
            return "ĐỎ" if color_code == 'white' else "ĐEN"

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
                print(">>> ĐÃ BẤM ESC! <<<")
                
                # [THÊM ĐOẠN NÀY]
                # Nếu đang chơi Online, gửi lời trăn trối trước khi đi
                if self.network_manager:
                    # 1. Gửi lời trăn trối cho đối thủ
                    try:
                        # [SỬA] Dùng hàm send_to_p2p (send_data không tồn tại)
                        self.network_manager.send_to_p2p({"type": "quit"})
                        
                        import time
                        time.sleep(0.1) # Đợi tin nhắn bay đi
                    except: pass
                
                    # 2. [QUAN TRỌNG NHẤT] Cắt mạng ngay lập tức tại đây
                    # Việc này sẽ làm biến p2p_socket = None. 
                    # Khi quay lại Menu, Menu thấy None sẽ tự động reset về trang chủ.
                    self.network_manager.reset_connection()
                
                return 'QUIT_GAME'
        self.ui_manager.process_events(event)

        if self.promotion_window:
            selected_char = self.promotion_window.check_event(event)
            if selected_char:
                self._execute_promotion_move(selected_char)
                self.promotion_window.kill()
                self.promotion_window = None
                return 

        if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if event.ui_element == self.confirmation_dialog:
                self.game_logic.game_over = True
                self.game_logic.winner = "draw"
                if self.network_manager: self.network_manager.send_command("DRAW_ACCEPT")
                self.confirmation_dialog = None
            # 2. [THÊM ĐOẠN NÀY] Xử lý hộp thoại "Đối phương bỏ chạy"
            # Khi bấm nút "Về Menu" thì thoát game ra ngoài
            elif hasattr(self, 'quit_dialog') and event.ui_element == self.quit_dialog:
                return 'QUIT_GAME'
        
        # [THÊM] Xử lý đóng cửa sổ (nút X) cho quit_dialog
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
             if event.ui_element == self.confirmation_dialog: self.confirmation_dialog = None
             if event.ui_element == self.promotion_window: 
                 self.promotion_window = None
                 self.pending_promotion_move = None 
             # Thêm dòng này:
             if hasattr(self, 'quit_dialog') and event.ui_element == self.quit_dialog:
                 return 'QUIT_GAME' # Bấm X cũng thoát luôn

        if self.sidebar:
            action = self.sidebar.handle_event(event, self.network_manager)
            if action == 'RESIGN':
                opponent_color = 'black' if self.game_logic.my_color == 'white' else 'white'
                self.game_logic.winner = opponent_color; self.game_logic.game_over = True
                if self.confirmation_dialog: self.confirmation_dialog.kill(); self.confirmation_dialog = None
            elif action == 'OFFER_DRAW':
                # self.sidebar.add_message("Hệ thống", "Đã gửi lời cầu hòa...")
                pass

        if self.game_logic.game_over: return 

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.promotion_window: return

                cell_size, start_x, start_y, _ = self._get_board_params()
                mouse_x, mouse_y = event.pos
                rel_x = mouse_x - start_x; rel_y = mouse_y - start_y
                board_pixel_w = cell_size * self.cols; board_pixel_h = cell_size * self.rows
                
                if 0 <= rel_x < board_pixel_w and 0 <= rel_y < board_pixel_h:
                    if not self.game_logic.is_my_turn(): 
                        if self.sidebar: self.sidebar.add_message("Hệ thống", "Chưa đến lượt của bạn!")
                        return
                    
                    screen_col = int(rel_x // cell_size); screen_row = int(rel_y // cell_size)
                    logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)
                    if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                        self._process_move_logic((logic_row, logic_col))
        return None

    def _process_move_logic(self, clicked_pos):
        """
        Xử lý logic khi người chơi click vào bàn cờ.
        """
        if self.selected_piece_pos:
            from_pos = self.selected_piece_pos
            to_pos = clicked_pos
            
            # Validator đã kiểm tra luật Nhập Thành ở đây
            # Nếu ô g1 (nhập thành) bị chặn hoặc nguy hiểm, nó sẽ KHÔNG có trong self.possible_moves
            if to_pos in self.possible_moves:
                piece_data = self.game_logic.get_piece(from_pos)
                symbol, color = get_piece_info(piece_data)

                # --- CHECK PHONG CẤP ---
                is_promotion = False
                if self.game_logic.game_type == 'chess' and symbol:
                    if symbol.lower() == 'p':
                        if (color == 'white' and to_pos[0] == 0) or \
                           (color == 'black' and to_pos[0] == 7):
                            is_promotion = True

                if is_promotion:
                    self.pending_promotion_move = (from_pos, to_pos)
                    self._show_promotion_window(color)
                else:
                    # --- DI CHUYỂN ---
                    # Board.py sẽ tự động xử lý:
                    # 1. Dời Vua
                    # 2. Dời Xe (nếu là nhập thành)
                    # 3. Xóa Tốt (nếu là En Passant)
                    move_success = self.game_logic.move_piece(from_pos, to_pos)
                    
                    if move_success:
                        if self.network_manager:
                            move_data = {
                                "type": "move", "from": from_pos, "to": to_pos, 
                                "game_type": self.game_logic.game_type
                            }
                            self.network_manager.send_to_p2p(move_data)
                
                self.selected_piece_pos = None; self.possible_moves = []
            else:
                new_piece_data = self.game_logic.get_piece(clicked_pos)
                new_symbol, new_color = get_piece_info(new_piece_data)
                if new_symbol:
                    if new_color != self.game_logic.current_turn: return 
                    self.selected_piece_pos = clicked_pos
                    # Lấy nước đi an toàn từ Validator
                    self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic, clicked_pos, self.game_logic.current_turn)
                else: 
                    self.selected_piece_pos = None; self.possible_moves = []
        else:
            piece_data = self.game_logic.get_piece(clicked_pos)
            symbol, color = get_piece_info(piece_data)
            if symbol:
                if self.game_logic.my_color and color != self.game_logic.my_color: return
                if color != self.game_logic.current_turn: return
                self.selected_piece_pos = clicked_pos
                self.possible_moves = self.game_logic.validator.get_valid_moves_for_piece(self.game_logic, clicked_pos, self.game_logic.current_turn)

    def _show_promotion_window(self, player_color):
        rect = pygame.Rect(0, 0, 440, 160) 
        rect.center = (WIDTH//2, HEIGHT//2)
        self.promotion_window = PromotionWindow(rect, self.ui_manager, self.piece_assets, player_color)

    def _execute_promotion_move(self, promotion_char):
        if self.pending_promotion_move:
            from_pos, to_pos = self.pending_promotion_move
            piece_data = self.game_logic.get_piece(from_pos)
            _, pawn_color = get_piece_info(piece_data)
            
            new_symbol = promotion_char.upper() if pawn_color == 'white' else promotion_char.lower()

            success = self.game_logic.move_piece(from_pos, to_pos, promotion=new_symbol)

            if success and self.network_manager:
                move_data = {
                    "type": "move", "from": from_pos, "to": to_pos, 
                    "promotion": new_symbol,
                    "game_type": self.game_logic.game_type
                }
                self.network_manager.send_to_p2p(move_data)
            
            self.pending_promotion_move = None
            return

        if self.game_logic.promotion_pending and self.game_logic.promotion_pos:
            to_pos = self.game_logic.promotion_pos
            pawn_color = self.game_logic.current_turn
            new_symbol = promotion_char.upper() if pawn_color == 'white' else promotion_char.lower()

            self.game_logic.apply_promotion(new_symbol)
            
            if self.network_manager:
                 move_data = {
                    "type": "move", "from": to_pos, "to": to_pos, "promotion": new_symbol,
                    "game_type": self.game_logic.game_type
                }
                 self.network_manager.send_to_p2p(move_data)

    def update(self):
        self.ui_manager.update(0.016)
        
        if self.game_logic.game_type == 'chess' and \
           self.game_logic.promotion_pending and \
           not self.promotion_window and \
           self.game_logic.is_my_turn():
               current_color = self.game_logic.current_turn
               self._show_promotion_window(current_color)
        # --- [THÊM] LOGIC CHO AI ĐI ---
        if self.ai_engine and not self.game_logic.game_over and not self.is_ai_thinking:
            # Nếu đến lượt Đen (máy)
            if self.game_logic.current_turn == 'black':
                self.is_ai_thinking = True
                # Chạy AI trong luồng riêng để không đơ màn hình
                threading.Thread(target=self.run_ai_move, daemon=True).start()
        # ------------------------------
        if self.network_manager:
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    msg_type = msg.get("type")
                    
                    if msg_type == "move":
                        from_pos = tuple(msg["from"]); to_pos = tuple(msg["to"])
                        promo_symbol = msg.get("promotion")
                        self.game_logic.move_piece(from_pos, to_pos, promotion=promo_symbol)
                    # [THÊM ĐOẠN NÀY] Xử lý khi đối thủ thoát
                    elif msg.get('type') == 'quit':
                        self.show_opponent_quit_dialog()
                        # Ngắt kết nối mạng phía mình luôn để dừng game
                        self.network_manager.reset_connection()
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
                                rect = pygame.Rect(0, 0, 300, 200); rect.center = (WIDTH//2, HEIGHT//2)
                                self.confirmation_dialog = UIConfirmationDialog(rect=rect, manager=self.ui_manager, window_title="Cầu Hòa", action_long_desc="Đối thủ muốn cầu hòa.", action_short_name="Đồng ý", blocking=True)
                        elif cmd == "DRAW_ACCEPT":
                            self.sidebar.add_message("Hệ thống", "Hai bên đã hòa!"); self.game_logic.winner = "draw"; self.game_logic.game_over = True
                            if self.confirmation_dialog: self.confirmation_dialog.kill(); self.confirmation_dialog = None
                except Exception as e: print(f"Lỗi update mạng: {e}")
            # 2. [THÊM MỚI - QUAN TRỌNG NHẤT] 
            # Kiểm tra nếu socket bị chết đột ngột (Đối thủ rớt mạng hoặc tắt game nóng)
            # Điều kiện: Game chưa kết thúc VÀ Socket đã bị None (ngắt kết nối)
            if not self.game_logic.game_over and self.network_manager.p2p_socket is None:
                # Kiểm tra xem đã hiện bảng chưa để tránh hiện 100 cái bảng
                if not hasattr(self, 'quit_dialog') or self.quit_dialog is None:
                    print("Phát hiện mất kết nối đột ngột -> Coi như đối thủ bỏ chạy.")
                    self.show_opponent_quit_dialog()
                    # Đánh dấu game over để không check nữa
                    self.game_logic.game_over = True

    def draw(self):
        bg_color = XIANGQI_BG_COLOR if self.game_logic.game_type != 'chess' else (48, 46, 43) 
        pygame.draw.rect(self.screen, bg_color, self.board_rect)

        if self.sidebar:
            turn_display_text = ""
            current_turn_vn = self.get_color_name(self.game_logic.current_turn)
            if self.game_logic.my_color:
                if self.game_logic.current_turn == self.game_logic.my_color:
                    turn_display_text = f"Lượt: {current_turn_vn} (Bạn)"; turn_text_color = (100, 255, 100)
                else:
                    turn_display_text = f"Lượt: {current_turn_vn} (Đối thủ)"; turn_text_color = (255, 100, 100)
            else:
                turn_display_text = f"Lượt: {current_turn_vn}"; turn_text_color = (255, 255, 255)

            turn_surface = self.turn_font.render(turn_display_text, True, turn_text_color)
            text_x = self.sidebar_rect.x + (self.sidebar_rect.width - turn_surface.get_width()) // 2
            self.screen.blit(turn_surface, (text_x, self.sidebar_rect.y + 30))
            self.sidebar.draw(self.screen, self.game_logic)

        cell_size, start_x, start_y, border_size = self._get_board_params()
        self.draw_board_squares(cell_size, start_x, start_y, border_size)
        self.draw_highlight_king_in_check(cell_size, start_x, start_y)
        self.draw_pieces(cell_size, start_x, start_y)
        self.draw_highlights(cell_size, start_x, start_y)
        # [SỬA LẠI ĐOẠN CUỐI NÀY] =================================================
        if self.game_logic.game_over:
            # Chỉ vẽ thông báo thắng/thua to đùng nếu KHÔNG CÓ bảng "Đối phương thoát"
            # Điều này giúp giao diện sạch sẽ, không bị chữ đè lên nhau
            if not hasattr(self, 'quit_dialog') or self.quit_dialog is None:
                self.draw_game_over_message()
        # ==========================================================================
        self.ui_manager.draw_ui(self.screen)

    def draw_game_over_message(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        winner = self.game_logic.winner
        if winner == "draw": text = "HÒA!"; color = (200, 200, 200)
        elif self.game_logic.my_color: 
            if winner == self.game_logic.my_color: text = "BẠN THẮNG!"; color = (100, 255, 100) 
            else: text = "BẠN THUA!"; color = (255, 50, 50) 
        else: 
            winner_vn = self.get_color_name(winner); text = f"{winner_vn} THẮNG!"; color = (255, 215, 0) 
        text_win_surf = self.winner_font.render(text, True, color)
        text_win_rect = text_win_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(text_win_surf, text_win_rect)
        sub_text_surf = self.info_font.render("Nhấn ESC để thoát", True, (200,200,200))
        sub_text_rect = sub_text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        self.screen.blit(sub_text_surf, sub_text_rect)
    
    def draw_board_squares(self, cell_size, start_x, start_y, border_size):
        if self.game_logic.game_type == 'chess':
            if border_size > 0:
                pygame.draw.rect(self.screen, (0, 0, 0), (start_x - border_size, start_y - border_size, cell_size * 8 + border_size*2, cell_size * 8 + border_size*2))
                pygame.draw.rect(self.screen, (100, 100, 100), (start_x - 2, start_y - 2, cell_size * 8 + 4, cell_size * 8 + 4), 2)
                files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']; ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
                if self.game_logic.my_color == 'black': files = files[::-1]; ranks = ranks[::-1]
                for i in range(8):
                    self.screen.blit(self.coord_font.render(ranks[i], True, CHESS_LIGHT_COLOR), (start_x - border_size + 8, start_y + i*cell_size + 8))
                    self.screen.blit(self.coord_font.render(files[i], True, CHESS_LIGHT_COLOR), (start_x + i*cell_size + cell_size - 15, start_y + 8*cell_size + 4))
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
                for r in range(self.rows): pygame.draw.line(self.screen, (0,0,0), (start_x, start_y + r*cell_size + cell_size//2), (start_x + (self.cols-1)*cell_size, start_y + r*cell_size + cell_size//2), 2)
                for c in range(self.cols): pygame.draw.line(self.screen, (0,0,0), (start_x + c*cell_size + cell_size//2, start_y), (start_x + c*cell_size + cell_size//2, start_y + (self.rows-1)*cell_size), 2)

    def draw_highlight_king_in_check(self, cell_size, start_x, start_y):
        is_check = False
        if hasattr(self.game_logic, 'is_check'): is_check = self.game_logic.is_check
        elif hasattr(self.game_logic, 'validator') and hasattr(self.game_logic.validator, 'is_in_check'):
             is_check = self.game_logic.validator.is_in_check(self.game_logic, self.game_logic.current_turn)
        if is_check:
            king_symbol = 'K' if self.game_logic.current_turn == 'white' else 'k'
            board_state = self.game_logic.get_board_state()
            for r in range(self.rows):
                for c in range(self.cols):
                    p_symbol, _ = get_piece_info(board_state[r][c])
                    if p_symbol == king_symbol:
                        screen_r, screen_c = self.to_screen_pos(r, c)
                        s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                        if self.game_logic.game_type == 'chess': s.fill((255, 0, 0, 150)) 
                        else: pygame.draw.circle(s, (255, 0, 0, 100), (cell_size//2, cell_size//2), cell_size//2); pygame.draw.circle(s, (255, 0, 0, 180), (cell_size//2, cell_size//2), cell_size//2.5)
                        self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))
                        return

    def draw_pieces(self, cell_size, start_x, start_y):
        board_state = self.game_logic.get_board_state()
        piece_radius = int(cell_size // 2 * 0.85); piece_thickness = 6 
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol, _ = get_piece_info(board_state[logic_r][logic_c])
                
                if symbol:
                    screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                    center_x = start_x + screen_c * cell_size + cell_size // 2
                    center_y = start_y + screen_r * cell_size + cell_size // 2
                    if self.game_logic.game_type == 'chess':
                        image = self.piece_assets.get(symbol)
                        if image:
                            main_size = int(cell_size * 0.75); outline_size = main_size + 6 
                            outline_img = pygame.transform.smoothscale(image, (outline_size, outline_size)); outline_img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
                            main_img = pygame.transform.smoothscale(image, (main_size, main_size))
                            self.screen.blit(outline_img, outline_img.get_rect(center=(center_x, center_y)))
                            self.screen.blit(main_img, main_img.get_rect(center=(center_x, center_y)))
                    else:
                        pygame.draw.circle(self.screen, (0, 0, 0, 60), (center_x + 2, center_y + piece_thickness + 3), piece_radius)
                        for i in range(piece_thickness): pygame.draw.circle(self.screen, PIECE_BODY_COLOR, (center_x, center_y + piece_thickness - i), piece_radius)
                        pygame.draw.circle(self.screen, PIECE_FACE_COLOR, (center_x, center_y), piece_radius)
                        image = self.piece_assets.get(symbol)
                        if image:
                            piece_scale = int(cell_size * 0.85); scaled_img = pygame.transform.smoothscale(image, (piece_scale, piece_scale))
                            self.screen.blit(scaled_img, scaled_img.get_rect(center=(center_x, center_y)))
                        else: self.screen.blit(self.fallback_font.render(symbol, True, (255,0,0)), (center_x - 10, center_y - 15))

    def draw_highlights(self, cell_size, start_x, start_y):
        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                if self.game_logic.game_type == 'chess': s.fill(CHESS_HINT_COLOR) 
                else:
                      center_x = cell_size//2; center_y = cell_size//2; radius = int(cell_size//2 * 0.9) + 2
                      has_piece, _ = get_piece_info(self.game_logic.get_board_state()[logic_r][logic_c])
                      if has_piece: pygame.draw.circle(s, (0, 255, 0, 200), (center_x, center_y), radius, 4)
                      else: pygame.draw.circle(s, (0, 200, 0, 180), (center_x, center_y), cell_size // 6)
                self.screen.blit(s, (start_x + screen_c * cell_size, start_y + screen_r * cell_size))
        if self.selected_piece_pos:
            screen_r, screen_c = self.to_screen_pos(*self.selected_piece_pos)
            rect_x = start_x + screen_c * cell_size; rect_y = start_y + screen_r * cell_size
            s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            if self.game_logic.game_type == 'chess': s.fill(CHESS_SELECTED_COLOR); self.screen.blit(s, (rect_x, rect_y))
            else: pygame.draw.circle(s, (255, 215, 0, 200), (cell_size//2, cell_size//2), int(cell_size//2 * 0.9) + 2, 4); self.screen.blit(s, (rect_x, rect_y))
        # --- [HIGHLIGHT LAST MOVE] ---
        if hasattr(self.game_logic, 'last_move') and self.game_logic.last_move:
            lm = self.game_logic.last_move
            start_pos = lm['start']
            end_pos = lm['end']
            
            # [SỬA 1] Màu vàng nhạt hơn: (255, 255, 0, 60)
            # Số cuối cùng (60) là độ đậm nhạt. Càng nhỏ càng mờ.
            highlight_color = (255, 255, 0, 60) 

            for pos in [start_pos, end_pos]:
                screen_r, screen_c = self.to_screen_pos(pos[0], pos[1])
                
                rect_x = start_x + screen_c * cell_size
                rect_y = start_y + screen_r * cell_size
                
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                
                if self.game_logic.game_type == 'chess':
                    # Cờ vua: Tô full ô vuông
                    s.fill(highlight_color)
                else:
                    # [SỬA 2] Cờ tướng: Vẽ hình tròn
                    # center: tâm hình tròn (giữa ô)
                    # radius: bán kính (nhỏ hơn ô một chút cho đẹp)
                    center = (cell_size // 2, cell_size // 2)
                    radius = int(cell_size // 2 * 0.8) 
                    
                    # Vẽ hình tròn đặc (màu nhạt)
                    pygame.draw.circle(s, highlight_color, center, radius)

                self.screen.blit(s, (rect_x, rect_y))
        # -----------------------------
    # --- [THÊM] HÀM CHẠY AI ---
    def run_ai_move(self):
        try:
            # Kiểm tra xem đây là Bot Tự Train hay là Engine (Stockfish/Pikafish)
            # Bot tự train có hàm 'predict' hoặc thuộc tính 'device'
            is_custom_bot = hasattr(self.ai_engine, 'predict') or hasattr(self.ai_engine, 'device')
            
            if is_custom_bot:
                # =================================================
                # TRƯỜNG HỢP 1: BOT TỰ TRAIN (CỜ TƯỚNG)
                # =================================================
                # Bot này cần nhận toàn bộ logic bàn cờ để tự tính toán
                best_move = self.ai_engine.get_best_move(self.game_logic)
                
                if best_move:
                    start, end = best_move
                    print(f"🤖 Bot đi: {start} -> {end}")
                    
                    # Đi trực tiếp (vì đã có tọa độ rồi)
                    self.game_logic.move_piece(start, end)
            
            else:
                # =================================================
                # TRƯỜNG HỢP 2: ENGINE (STOCKFISH / PIKAFISH)
                # =================================================
                # 1. Lấy FEN từ bàn cờ
                fen = self.game_logic.to_fen()
                
                # 2. Hỏi Stockfish/Pikafish
                best_move_str = self.ai_engine.get_best_move(fen)
                
                if best_move_str:
                    print(f"🤖 Engine đi: {best_move_str}")
                    
                    # 3. Đổi tọa độ uci (e7e5) sang tọa độ số ((1,4)->(3,4))
                    start, end, promo = self.game_logic.uci_to_coords(best_move_str)
                    
                    if start and end:
                        # 4. Đi quân
                        self.game_logic.move_piece(start, end, promotion=promo)

        except Exception as e:
            print(f"❌ Lỗi AI: {e}")
            import traceback
            traceback.print_exc() # In chi tiết lỗi để dễ sửa
        
        # Tắt cờ hiệu để cho phép người chơi click chuột lại
        self.is_ai_thinking = False
    # Thêm vào class BoardUI
    def show_opponent_quit_dialog(self):
        from pygame_gui.windows import UIConfirmationDialog
        from pygame_gui.core import ObjectID
        if self.game_logic.my_color:
            self.game_logic.winner = self.game_logic.my_color
        
        # Đánh dấu game kết thúc luôn để chặn click chuột
        self.game_logic.game_over = True
        # Tạo hộp thoại thông báo
        self.quit_dialog = UIConfirmationDialog(
            rect=pygame.Rect(0, 0, 400, 200),
            manager=self.ui_manager,
            window_title="Thông Báo",
            action_long_desc="Đối phương đã bỏ chạy!",
            action_short_name="Về Menu",
            blocking=True,
            object_id=ObjectID(object_id="#confirmation_dialog") # Để nó nhận font tiếng Việt
        )
        # Căn giữa màn hình
        self.quit_dialog.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.quit_dialog.rebuild()