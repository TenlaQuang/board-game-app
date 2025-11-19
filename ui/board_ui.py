import json
import pygame
from core.board import Board
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR,
    PADDING_X, PADDING_Y, SQUARE_SIZE_W, SQUARE_SIZE_H
)
from .assets import XIANGQI_BOARD_IMG
# Đảm bảo bạn đã cập nhật file chat_box.py thành GameSidebar như bước trước
from .chat_box import GameSidebar 

class BoardUI:
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, sidebar_rect=None, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        # Hình chữ nhật giới hạn khu vực bàn cờ
        self.board_rect = board_rect
        # Hình chữ nhật giới hạn khu vực Sidebar (Chat)
        self.sidebar_rect = sidebar_rect
        
        # Network & Role
        self.network_manager = network_manager
        self.my_role = my_role
        
        # Thiết lập màu cho người chơi Local
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
        
        # --- LOAD THEME & FONTS (Code của bạn) ---
        try:
            with open("theme.json", "r", encoding="utf-8") as f:
                theme = json.load(f)
            font_path = theme["defaults"]["font"]["regular_path"]
        except Exception as e:
            print(f"Không đọc được theme.json, dùng font mặc định: {e}")
            font_path = None # Pygame sẽ dùng default font

        self.fallback_font = pygame.font.Font(font_path, 30)
        self.winner_font   = pygame.font.Font(font_path, 80)
        self.info_font     = pygame.font.Font(font_path, 40)
        
        # Font nhỏ hơn cho Chat
        self.chat_font     = pygame.font.Font(font_path, 18)

        # --- KHỞI TẠO SIDEBAR ---
        if self.sidebar_rect:
            self.sidebar = GameSidebar(
                self.sidebar_rect.x, self.sidebar_rect.y, 
                self.sidebar_rect.width, self.sidebar_rect.height, 
                self.chat_font 
            )
        else:
            self.sidebar = None

    # --- HÀM ĐẢO NGƯỢC BÀN CỜ ---
    def to_screen_pos(self, logic_r, logic_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - logic_r), (self.cols - 1 - logic_c)
        return logic_r, logic_c

    def from_screen_pos(self, screen_r, screen_c):
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - screen_r), (self.cols - 1 - screen_c)
        return screen_r, screen_c

    def handle_events(self, event: pygame.event.Event):
       # 1. Ưu tiên xử lý sự kiện ở Sidebar (Chat, nút bấm)
        if self.sidebar:
            action = self.sidebar.handle_event(event, self.network_manager)
            
            if action == 'RESIGN':
                # --- [FIX LOGIC ĐẦU HÀNG] ---
                # Nếu đang chơi Online (có phân biệt màu quân)
                if self.game_logic.my_color:
                    # Mình bấm đầu hàng -> Đối thủ thắng
                    if self.game_logic.my_color == 'white':
                        self.game_logic.winner = 'black'
                    else: # my_color là black
                        self.game_logic.winner = 'white'
                else:
                    # Nếu chơi Offline (2 người 1 máy), ai bấm lúc nào thì coi như người đang đi đầu hàng
                    self.game_logic.winner = self.game_logic.opponent_color()
                # ----------------------------

            elif action == 'OFFER_DRAW':
                self.sidebar.add_message("System", "Đã gửi lời cầu hòa...")

        # 2. Nếu Game Over thì chặn click bàn cờ
        if self.game_logic.game_over: return

        # 3. Xử lý Click trên bàn cờ
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Chỉ xử lý khi click chuột NẰM TRONG vùng bàn cờ
                if self.board_rect.collidepoint(event.pos):
                    if not self.game_logic.is_my_turn(): return

                    # Tính toạ độ chuột TƯƠNG ĐỐI so với góc trên trái của bàn cờ
                    rel_x = event.pos[0] - self.board_rect.x
                    rel_y = event.pos[1] - self.board_rect.y

                    # Tính kích thước 1 ô dựa trên kích thước hiện tại của bàn cờ
                    current_cell_w = self.board_rect.width // self.cols
                    current_cell_h = self.board_rect.height // self.rows

                    if self.game_logic.game_type == 'chess':
                        screen_col = rel_x // current_cell_w
                        screen_row = rel_y // current_cell_h
                    else:
                        # Xiangqi: Cần tính lại tỉ lệ co giãn nếu bàn cờ bị thu nhỏ
                        # Tạm thời dùng logic chia lưới đơn giản để đảm bảo hoạt động
                        screen_col = round((rel_x - PADDING_X) / SQUARE_SIZE_W)
                        screen_row = round((rel_y - PADDING_Y) / SQUARE_SIZE_H)
                    
                    logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)

                    if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                        clicked_pos = (logic_row, logic_col)
                        self._process_move_logic(clicked_pos)

    def _process_move_logic(self, clicked_pos):
        """Tách logic di chuyển ra hàm riêng cho gọn"""
        if self.selected_piece_pos:
            from_pos = self.selected_piece_pos
            to_pos = clicked_pos
            
            if to_pos in self.possible_moves:
                self.game_logic.move_piece(from_pos, to_pos)
                
                if self.network_manager:
                    move_data = {
                        "type": "move", "from": from_pos, "to": to_pos,
                        "game_type": self.game_logic.game_type
                    }
                    self.network_manager.send_to_p2p(move_data)
                
                self.selected_piece_pos = None; self.possible_moves = []
            else:
                # Logic chọn lại quân khác
                new_piece = self.game_logic.get_piece(clicked_pos)
                current_piece = self.game_logic.get_piece(from_pos)
                if new_piece and current_piece and new_piece.color == current_piece.color:
                    self.selected_piece_pos = clicked_pos
                    self.possible_moves = new_piece.valid_moves(self.game_logic.board, clicked_pos)
                    return 
                self.selected_piece_pos = None; self.possible_moves = []
        else:
            piece = self.game_logic.get_piece(clicked_pos)
            if piece:
                if self.game_logic.my_color and piece.color != self.game_logic.my_color: return
                self.selected_piece_pos = clicked_pos
                self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)

    def update(self):
        if self.network_manager:
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    msg_type = msg.get("type")

                    if msg_type == "move":
                        self.game_logic.move_piece(tuple(msg["from"]), tuple(msg["to"]))
                    
                    elif msg_type == "chat":
                        if self.sidebar:
                            self.sidebar.add_message("Đối thủ", msg["content"])
                    
                    elif msg_type == "command":
                        cmd = msg["content"]
                        if cmd == "RESIGN":
                            self.sidebar.add_message("System", "Đối thủ đã đầu hàng!")
                            self.game_logic.winner = self.game_logic.my_color 
                        elif cmd == "DRAW_OFFER":
                            self.sidebar.add_message("System", "Đối thủ muốn hòa")

                except Exception as e:
                    print(f"Lỗi update mạng: {e}")

    def draw(self):
        # 1. Vẽ Sidebar (Khung chat)
        if self.sidebar:
            self.sidebar.draw(self.screen, self.game_logic)

        # 2. Vẽ Bàn cờ
        # Dùng clip để đảm bảo không vẽ lan sang vùng sidebar
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.board_rect)
        
        self.draw_board_squares()
        self.draw_highlights()
        self.draw_pieces()
        
        self.screen.set_clip(old_clip) # Trả lại vùng vẽ toàn màn hình

        # 3. Vẽ màn hình chiến thắng (Game Over) - Đè lên tất cả
        if self.game_logic.game_over:
            self.draw_game_over_message()

    def draw_board_squares(self):
        # Tính lại kích thước ô dựa trên board_rect (không dùng WIDTH/HEIGHT global)
        cell_w = self.board_rect.width // self.cols
        cell_h = self.board_rect.height // self.rows

        if self.game_logic.game_type == 'chess':
            for r in range(self.rows):
                for c in range(self.cols):
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    # Vẽ ô cờ có cộng thêm offset board_rect.x/y
                    rect = (self.board_rect.x + c * cell_w, self.board_rect.y + r * cell_h, cell_w, cell_h)
                    pygame.draw.rect(self.screen, color, rect)
        else: 
            if XIANGQI_BOARD_IMG:
                # Co giãn ảnh bàn cờ tướng cho vừa khung
                scaled_bg = pygame.transform.scale(XIANGQI_BOARD_IMG, (self.board_rect.width, self.board_rect.height))
                self.screen.blit(scaled_bg, (self.board_rect.x, self.board_rect.y))
            else:
                self.screen.fill(LIGHT_SQUARE_COLOR, self.board_rect)

    def draw_pieces(self):
        cell_w = self.board_rect.width // self.cols
        cell_h = self.board_rect.height // self.rows
        
        board_state = self.game_logic.get_board_state()
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol = board_state[logic_r][logic_c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    if image:
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                        
                        # Tính toạ độ vẽ (Căn giữa ô) + Offset của bàn cờ
                        x = self.board_rect.x + screen_c * cell_w + (cell_w - image.get_width()) // 2
                        y = self.board_rect.y + screen_r * cell_h + (cell_h - image.get_height()) // 2
                        self.screen.blit(image, (x, y))
                    else:
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                        text = self.fallback_font.render(symbol, True, (255,0,0))
                        x = self.board_rect.x + screen_c * cell_w + 10
                        y = self.board_rect.y + screen_r * cell_h + 10
                        self.screen.blit(text, (x, y))

    def draw_highlights(self):
        cell_w = self.board_rect.width // self.cols
        cell_h = self.board_rect.height // self.rows

        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                
                # Tâm ô cờ
                center_x = self.board_rect.x + screen_c * cell_w + cell_w // 2
                center_y = self.board_rect.y + screen_r * cell_h + cell_h // 2
                
                if self.game_logic.game_type == 'chess':
                    s = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                    pygame.draw.circle(s, (0, 100, 0, 120), (cell_w//2, cell_h//2), 15)
                    self.screen.blit(s, (self.board_rect.x + screen_c*cell_w, self.board_rect.y + screen_r*cell_h))
                else:
                    pygame.draw.circle(self.screen, (0, 200, 0), (center_x, center_y), 10)

        if self.selected_piece_pos:
            screen_r, screen_c = self.to_screen_pos(*self.selected_piece_pos)
            x = self.board_rect.x + screen_c * cell_w
            y = self.board_rect.y + screen_r * cell_h
            
            if self.game_logic.game_type == 'chess':
                s = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                s.fill((*HIGHLIGHT_COLOR, 100))
                self.screen.blit(s, (x, y))
            else:
                center_x = x + cell_w // 2
                center_y = y + cell_h // 2
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (center_x, center_y), 15, 2)

    def draw_game_over_message(self):
        # Vẽ overlay toàn màn hình (cả sidebar cũng bị tối đi)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        winner = self.game_logic.winner
        if self.game_logic.game_type == 'chess':
            text = "TRẮNG THẮNG!" if winner == 'white' else "ĐEN THẮNG!"
        else:
            text = "ĐỎ THẮNG!" if winner == 'white' else "ĐEN THẮNG!"
            
        color = (255, 50, 50) if winner == 'white' else (100, 100, 255)
        
        # Căn giữa toàn bộ cửa sổ
        txt_surf = self.winner_font.render(text, True, color)
        self.screen.blit(txt_surf, txt_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
        sub_txt = self.info_font.render("Nhấn ESC để thoát", True, (200,200,200))
        self.screen.blit(sub_txt, sub_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))