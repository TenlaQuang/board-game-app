# ui/board_ui.py
import pygame
from core.board import Board
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR,
    XIANGQI_ROWS, XIANGQI_COLS, PADDING_X, PADDING_Y, 
    SQUARE_SIZE_W, SQUARE_SIZE_H
)
from .assets import XIANGQI_BOARD_IMG

class BoardUI:
    """
    Phiên bản BoardUI hỗ trợ P2P Network và Board Flipping.
    """
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        self.board_rect = board_rect # Hình chữ nhật chứa bàn cờ
        
        # Network & Role
        self.network_manager = network_manager
        self.my_role = my_role # 'host' hoặc 'client'
        
        # Thiết lập màu cho người chơi Local
        # Host = White/Red (đi trước), Client = Black (đi sau)
        # Cờ tướng: 'white' trong logic mapping là Đỏ
        if self.my_role == 'host':
            self.game_logic.set_player_color('white') 
        elif self.my_role == 'client':
            self.game_logic.set_player_color('black')
        else:
            # Chơi offline 1 máy -> không set màu cố định (ai đi cũng được)
            self.game_logic.set_player_color(None) 
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        self.selected_piece_pos = None
        self.possible_moves = []
        
        self.fallback_font = pygame.font.Font(None, 30) 

    # =======================================================================
    # HÀM HỖ TRỢ ĐẢO NGƯỢC BÀN CỜ (BOARD FLIPPING)
    # =======================================================================
    def to_screen_pos(self, logic_r, logic_c):
        """Chuyển tọa độ Logic -> Tọa độ Màn hình (để vẽ)."""
        # Nếu mình là quân Đen (Client), lật ngược bàn cờ để quân mình nằm dưới
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - logic_r), (self.cols - 1 - logic_c)
        return logic_r, logic_c

    def from_screen_pos(self, screen_r, screen_c):
        """Chuyển tọa độ Màn hình -> Tọa độ Logic (để xử lý click)."""
        # Nếu mình là quân Đen, tính ngược lại
        if self.game_logic.my_color == 'black':
            return (self.rows - 1 - screen_r), (self.cols - 1 - screen_c)
        return screen_r, screen_c
    # =======================================================================

    def handle_events(self, event: pygame.event.Event):
        """Xử lý click chuột và gửi nước đi qua mạng."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click chuột trái
                
                # 1. KIỂM TRA LƯỢT CHƠI (Chặn click nếu chưa tới lượt)
                # Hàm is_my_turn() đã được thêm vào GameState/Board ở bước trước
                if not self.game_logic.is_my_turn():
                    print("Chưa tới lượt bạn!")
                    return

                pos = pygame.mouse.get_pos()
                
                # 2. TÍNH TOẠ ĐỘ MÀN HÌNH (Screen Row/Col)
                if self.game_logic.game_type == 'chess':
                    screen_col = pos[0] // (WIDTH // self.cols)
                    screen_row = pos[1] // (HEIGHT // self.rows)
                else: # Xiangqi
                    screen_col = round((pos[0] - PADDING_X) / SQUARE_SIZE_W)
                    screen_row = round((pos[1] - PADDING_Y) / SQUARE_SIZE_H)
                
                # 3. CHUYỂN ĐỔI SANG TOẠ ĐỘ LOGIC (Có xử lý đảo ngược)
                logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)

                # Kiểm tra click hợp lệ trong bàn cờ
                if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                    clicked_pos = (logic_row, logic_col)

                    if self.selected_piece_pos:
                        # --- ĐÃ CHỌN QUÂN -> THỰC HIỆN NƯỚC ĐI ---
                        from_pos = self.selected_piece_pos
                        to_pos = clicked_pos
                        
                        if to_pos in self.possible_moves:
                            # 1. Di chuyển trên máy mình
                            self.game_logic.move_piece(from_pos, to_pos) # Hàm này sẽ tự switch_turn
                            
                            # 2. GỬI NƯỚC ĐI QUA MẠNG
                            if self.network_manager:
                                move_data = {
                                    "type": "move",
                                    "from": from_pos,
                                    "to": to_pos,
                                    "game_type": self.game_logic.game_type
                                }
                                self.network_manager.send_to_p2p(move_data)
                                print(f"[P2P] Đã gửi nước đi: {move_data}")
                            
                            # Reset chọn
                            self.selected_piece_pos = None
                            self.possible_moves = []

                        else:
                            # Logic chọn lại quân khác cùng phe
                            new_piece = self.game_logic.get_piece(clicked_pos)
                            current_piece = self.game_logic.get_piece(from_pos)
                            if new_piece and current_piece and new_piece.color == current_piece.color:
                                self.selected_piece_pos = clicked_pos
                                self.possible_moves = new_piece.valid_moves(self.game_logic.board, clicked_pos)
                                return 
                            
                            self.selected_piece_pos = None
                            self.possible_moves = []
                        
                    else:
                        # --- CHƯA CHỌN -> CHỌN QUÂN ---
                        piece = self.game_logic.get_piece(clicked_pos)
                        if piece:
                            # Chỉ cho phép chọn quân đúng màu của mình
                            if self.game_logic.my_color and piece.color != self.game_logic.my_color:
                                print(f"Bạn chỉ được điều khiển quân màu {self.game_logic.my_color}")
                                return

                            self.selected_piece_pos = clicked_pos
                            self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)

    def update(self):
        """Cập nhật logic: Lắng nghe nước đi từ đối thủ."""
        if self.network_manager:
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    if msg.get("type") == "move":
                        from_pos = tuple(msg["from"])
                        to_pos = tuple(msg["to"])
                        
                        print(f"[P2P] Nhận nước đi từ đối thủ: {from_pos} -> {to_pos}")
                        # Thực hiện nước đi (logic game sẽ tự đổi lượt về lại cho mình)
                        self.game_logic.move_piece(from_pos, to_pos)
                        
                except Exception as e:
                    print(f"Lỗi xử lý data mạng: {e}")

    def draw(self):
        """Vẽ giao diện."""
        self.draw_board_squares()
        self.draw_highlights()
        self.draw_pieces()
        
    def draw_board_squares(self):
        # Vẽ nền (Không cần đảo ngược vì nền đối xứng hoặc ảnh tĩnh)
        if self.game_logic.game_type == 'chess':
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            for r in range(self.rows):
                for c in range(self.cols):
                    # Lưu ý: Màu ô cờ vua cần vẽ theo tọa độ màn hình để giữ tính xen kẽ đúng
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    pygame.draw.rect(self.screen, color, (c * square_w, r * square_h, square_w, square_h))
        else: 
            if XIANGQI_BOARD_IMG:
                self.screen.blit(XIANGQI_BOARD_IMG, (0, 0))
            else:
                self.screen.fill(LIGHT_SQUARE_COLOR)

    def draw_pieces(self):
        board_state_symbols = self.game_logic.get_board_state()
        
        # Duyệt qua TOÀN BỘ tọa độ logic
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol = board_state_symbols[logic_r][logic_c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    if image:
                        # --- CHUYỂN ĐỔI LOGIC -> SCREEN ĐỂ VẼ ---
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)

                        if self.game_logic.game_type == 'chess':
                            square_w = WIDTH // self.cols
                            square_h = HEIGHT // self.rows
                            x_pos = screen_c * square_w + (square_w - image.get_width()) // 2
                            y_pos = screen_r * square_h + (square_h - image.get_height()) // 2
                            self.screen.blit(image, (x_pos, y_pos))
                        else:
                            corner_x = PADDING_X + screen_c * SQUARE_SIZE_W
                            corner_y = PADDING_Y + screen_r * SQUARE_SIZE_H
                            self.screen.blit(image, (corner_x - image.get_width() // 2, corner_y - image.get_height() // 2))
                    else:
                        # Fallback text
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                        text = self.fallback_font.render(symbol, True, (255,0,0))
                        if self.game_logic.game_type == 'chess':
                             self.screen.blit(text, (screen_c * 60 + 10, screen_r * 60 + 10))
                        else:
                             cx = PADDING_X + screen_c * SQUARE_SIZE_W
                             cy = PADDING_Y + screen_r * SQUARE_SIZE_H
                             self.screen.blit(text, (cx - 10, cy - 10))

    def draw_highlights(self):
        # 1. Highlight nước đi hợp lệ
        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                # Chuyển đổi tọa độ logic -> màn hình
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                
                if self.game_logic.game_type == 'chess':
                    square_w = WIDTH // self.cols
                    square_h = HEIGHT // self.rows
                    s = pygame.Surface((square_w, square_h), pygame.SRCALPHA)
                    pygame.draw.circle(s, (0, 100, 0, 120), (square_w//2, square_h//2), 15)
                    self.screen.blit(s, (screen_c*square_w, screen_r*square_h))
                else:
                    cx = PADDING_X + screen_c * SQUARE_SIZE_W
                    cy = PADDING_Y + screen_r * SQUARE_SIZE_H
                    pygame.draw.circle(self.screen, (0, 200, 0), (cx, cy), 10)

        # 2. Highlight quân đang chọn
        if self.selected_piece_pos:
            logic_r, logic_c = self.selected_piece_pos
            screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
            
            if self.game_logic.game_type == 'chess':
                square_w = WIDTH // self.cols
                square_h = HEIGHT // self.rows
                s = pygame.Surface((square_w, square_h), pygame.SRCALPHA)
                s.fill((*HIGHLIGHT_COLOR, 100))
                self.screen.blit(s, (screen_c*square_w, screen_r*square_h))
            else:
                cx = PADDING_X + screen_c * SQUARE_SIZE_W
                cy = PADDING_Y + screen_r * SQUARE_SIZE_H
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (cx, cy), 15, 2)