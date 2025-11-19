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
    Phiên bản BoardUI hỗ trợ P2P Network.
    """
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        # Network
        self.network_manager = network_manager
        self.my_role = my_role # 'host' hoặc 'client'
        
        # Xác định màu quân của mình (Host đi Trắng/Đỏ, Client đi Đen)
        # (Logic này có thể tùy chỉnh, tạm thời quy ước như vậy)
        self.my_color = None
        if self.my_role == 'host':
            self.my_color = 'white' if game_logic.game_type == 'chess' else 'red'
        elif self.my_role == 'client':
            self.my_color = 'black'
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        self.selected_piece_pos = None
        self.possible_moves = []
        
        self.fallback_font = pygame.font.Font(None, 30) 

    def handle_events(self, event: pygame.event.Event):
        """Xử lý click chuột và gửi nước đi qua mạng."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click chuột trái
                # 1. Nếu đang chơi Online mà chưa đến lượt hoặc chọn sai màu -> Chặn (Tùy chọn)
                # Hiện tại mình để mở (Sandbox) để test cho dễ, sau này có thể uncomment dòng dưới:
                # if self.network_manager and self.game_logic.turn != self.my_color: return

                pos = pygame.mouse.get_pos()
                
                # Tính toán tọa độ click
                if self.game_logic.game_type == 'chess':
                    col = pos[0] // (WIDTH // self.cols)
                    row = pos[1] // (HEIGHT // self.rows)
                else:
                    col = round((pos[0] - PADDING_X) / SQUARE_SIZE_W)
                    row = round((pos[1] - PADDING_Y) / SQUARE_SIZE_H)
                
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    clicked_pos = (row, col)

                    if self.selected_piece_pos:
                        # --- ĐÃ CHỌN QUÂN -> THỰC HIỆN NƯỚC ĐI ---
                        from_pos = self.selected_piece_pos
                        to_pos = clicked_pos
                        
                        if to_pos in self.possible_moves:
                            # 1. Di chuyển trên máy mình
                            self.game_logic.move_piece(from_pos, to_pos)
                            
                            # 2. GỬI NƯỚC ĐI QUA MẠNG (QUAN TRỌNG)
                            if self.network_manager:
                                move_data = {
                                    "type": "move",
                                    "from": from_pos,
                                    "to": to_pos,
                                    "game_type": self.game_logic.game_type
                                }
                                self.network_manager.send_to_p2p(move_data)
                                print(f"[P2P] Đã gửi nước đi: {move_data}")

                        else:
                            # Logic chọn lại quân khác
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
                            # Nếu Online: Chỉ cho phép chọn quân của mình
                            if self.network_manager and self.my_color and piece.color != self.my_color:
                                print(f"Bạn chỉ được điều khiển quân màu {self.my_color}")
                                return

                            self.selected_piece_pos = clicked_pos
                            self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)

    def update(self):
        """Cập nhật logic: Lắng nghe nước đi từ đối thủ."""
        if self.network_manager:
            # Kiểm tra xem có tin nhắn nào trong hàng đợi không
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    
                    # Xử lý tin nhắn loại "move"
                    if msg.get("type") == "move":
                        from_pos = tuple(msg["from"]) # JSON trả về list, cần ép kiểu về tuple
                        to_pos = tuple(msg["to"])
                        
                        print(f"[P2P] Nhận nước đi từ đối thủ: {from_pos} -> {to_pos}")
                        # Thực hiện nước đi trên bàn cờ mình
                        self.game_logic.move_piece(from_pos, to_pos)
                        
                except Exception as e:
                    print(f"Lỗi xử lý data mạng: {e}")

    def draw(self):
        """Vẽ giao diện."""
        self.draw_board_squares()
        self.draw_highlights()
        self.draw_pieces()
        
    # --- GIỮ NGUYÊN CÁC HÀM VẼ CŨ CỦA BẠN ---
    def draw_board_squares(self):
        if self.game_logic.game_type == 'chess':
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            for r in range(self.rows):
                for c in range(self.cols):
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    pygame.draw.rect(self.screen, color, (c * square_w, r * square_h, square_w, square_h))
        else: 
            if XIANGQI_BOARD_IMG:
                self.screen.blit(XIANGQI_BOARD_IMG, (0, 0))
            else:
                self.screen.fill(LIGHT_SQUARE_COLOR)

    def draw_pieces(self):
        board_state_symbols = self.game_logic.get_board_state()
        for r in range(self.rows):
            for c in range(self.cols):
                symbol = board_state_symbols[r][c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    if image:
                        if self.game_logic.game_type == 'chess':
                            square_w = WIDTH // self.cols
                            square_h = HEIGHT // self.rows
                            x_pos = c * square_w + (square_w - image.get_width()) // 2
                            y_pos = r * square_h + (square_h - image.get_height()) // 2
                            self.screen.blit(image, (x_pos, y_pos))
                        else:
                            corner_x = PADDING_X + c * SQUARE_SIZE_W
                            corner_y = PADDING_Y + r * SQUARE_SIZE_H
                            self.screen.blit(image, (corner_x - image.get_width() // 2, corner_y - image.get_height() // 2))
                    else:
                        text = self.fallback_font.render(symbol, True, (255,0,0))
                        self.screen.blit(text, (c*50, r*50)) # Fallback đơn giản

    def draw_highlights(self):
        if self.game_logic.game_type == 'chess':
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            if self.possible_moves:
                for r, c in self.possible_moves:
                    s = pygame.Surface((square_w, square_h), pygame.SRCALPHA)
                    pygame.draw.circle(s, (0, 100, 0, 120), (square_w//2, square_h//2), 15)
                    self.screen.blit(s, (c*square_w, r*square_h))
            if self.selected_piece_pos:
                r, c = self.selected_piece_pos
                s = pygame.Surface((square_w, square_h), pygame.SRCALPHA)
                s.fill((*HIGHLIGHT_COLOR, 100))
                self.screen.blit(s, (c*square_w, r*square_h))
        else:
            if self.possible_moves:
                for r, c in self.possible_moves:
                    cx, cy = PADDING_X + c * SQUARE_SIZE_W, PADDING_Y + r * SQUARE_SIZE_H
                    pygame.draw.circle(self.screen, (0, 200, 0), (cx, cy), 10)
            if self.selected_piece_pos:
                r, c = self.selected_piece_pos
                cx, cy = PADDING_X + c * SQUARE_SIZE_W, PADDING_Y + r * SQUARE_SIZE_H
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (cx, cy), 15, 2)