# Trong file: ui/board_ui.py
import pygame
from core.board import Board # Import "bộ não" Board của bạn
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR,
    # Import các hằng số Cờ Tướng (quan trọng!)
    XIANGQI_ROWS, XIANGQI_COLS, PADDING_X, PADDING_Y, 
    SQUARE_SIZE_W, SQUARE_SIZE_H
)
# Import ảnh nền bàn cờ tướng
from .assets import XIANGQI_BOARD_IMG

class BoardUI:
    """
    Lớp này chịu trách nhiệm vẽ bàn cờ, quân cờ,
    và xử lý input của người chơi (click chuột) trên bàn cờ.
    """
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        # --- (Xóa code tính square_size cũ) ---
        
        self.selected_piece_pos = None # Vị trí (row, col) của quân đang được chọn
        self.possible_moves = []       # Các nước đi hợp lệ cho quân đang chọn
        
        # Thêm font dự phòng (cho trường hợp không tải được ảnh)
        self.fallback_font = pygame.font.Font(None, 30) 

    def handle_events(self, event: pygame.event.Event):
        """Xử lý click chuột để chọn/di chuyển quân."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click chuột trái
                pos = pygame.mouse.get_pos()
                
                # --- SỬA LOGIC CLICK CHUỘT ---
                if self.game_logic.game_type == 'chess':
                    # Logic Cờ Vua (tính theo ô)
                    col = pos[0] // (WIDTH // self.cols)
                    row = pos[1] // (HEIGHT // self.rows)
                else:
                    # Logic Cờ Tướng (tính giao điểm gần nhất)
                    # (Đây là phép toán tìm giao điểm gần nhất với cú click)
                    col = round((pos[0] - PADDING_X) / SQUARE_SIZE_W)
                    row = round((pos[1] - PADDING_Y) / SQUARE_SIZE_H)
                # -----------------------------
                
                # Đảm bảo click nằm trong bàn cờ
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    clicked_pos = (row, col)

                    if self.selected_piece_pos:
                        # --- Đã có quân được chọn -> Đây là nước đi ---
                        from_pos = self.selected_piece_pos
                        to_pos = clicked_pos
                        
                        if to_pos in self.possible_moves:
                            print(f"Di chuyển hợp lệ từ {from_pos} đến {to_pos}")
                            self.game_logic.move_piece(from_pos, to_pos)
                        else:
                            new_piece = self.game_logic.get_piece(clicked_pos)
                            # (Đã sửa: dùng .get_piece() cho cả 2)
                            if new_piece and new_piece.color == self.game_logic.get_piece(from_pos).color:
                                # Chọn quân khác cùng màu
                                self.selected_piece_pos = clicked_pos
                                print(f"Đổi chọn quân: {new_piece} tại {clicked_pos}")
                                self.possible_moves = new_piece.valid_moves(self.game_logic.board, clicked_pos)
                                print("Nước đi hợp lệ:", self.possible_moves)
                                return 
                            else:
                                print(f"Nước đi không hợp lệ: {from_pos} -> {to_pos}")
                        
                        # Bỏ chọn
                        self.selected_piece_pos = None
                        self.possible_moves = []
                        
                    else:
                        # --- Đây là lần click đầu tiên -> Chọn quân ---
                        piece = self.game_logic.get_piece(clicked_pos)
                        if piece: # và piece.color == lượt_hiện_tại (sẽ thêm sau)
                            self.selected_piece_pos = clicked_pos
                            print(f"Đã chọn quân: {piece} tại {clicked_pos}")
                            self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)
                            print("Nước đi hợp lệ:", self.possible_moves)
                        else:
                            print(f"Click vào ô trống: {clicked_pos}")

    def update(self):
        """Cập nhật logic game (nếu có animation hoặc tính toán gì đó)."""
        pass # (Chúng ta sẽ thêm animation di chuyển quân cờ vào đây sau)

    def draw(self):
        """Vẽ mọi thứ của màn hình game: nền, quân cờ, highlight."""
        self.draw_board_squares()
        self.draw_highlights() # Vẽ highlight trước quân cờ
        self.draw_pieces()
        
    def draw_board_squares(self):
        """Vẽ các ô sáng/tối (Cờ Vua) hoặc nền (Cờ Tướng)."""
        
        # --- SỬA LOGIC VẼ NỀN ---
        if self.game_logic.game_type == 'chess':
            # Vẽ ô Cờ Vua
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            for r in range(self.rows):
                for c in range(self.cols):
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    pygame.draw.rect(
                        self.screen, color, 
                        (c * square_w, r * square_h, square_w, square_h)
                    )
        else: 
            # Vẽ nền Cờ Tướng
            if XIANGQI_BOARD_IMG:
                # 1. Vẽ ảnh nền bàn cờ
                self.screen.blit(XIANGQI_BOARD_IMG, (0, 0))
            else:
                # 2. Dự phòng: Tô màu be nếu không có ảnh
                self.screen.fill(LIGHT_SQUARE_COLOR)
                # (Thiếu code vẽ đường kẻ, nên dùng ảnh nền là tốt nhất)

    def draw_pieces(self):
        """Vẽ tất cả quân cờ lên bàn cờ."""
        board_state_symbols = self.game_logic.get_board_state()
        
        for r in range(self.rows):
            for c in range(self.cols):
                symbol = board_state_symbols[r][c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    
                    # --- SỬA LOGIC VẼ QUÂN CỜ ---
                    if image:
                        if self.game_logic.game_type == 'chess':
                            # Logic Cờ Vua (căn giữa ô)
                            square_w = WIDTH // self.cols
                            square_h = HEIGHT // self.rows
                            x_pos = c * square_w
                            y_pos = r * square_h
                            x_offset = (square_w - image.get_width()) // 2
                            y_offset = (square_h - image.get_height()) // 2
                            self.screen.blit(image, (x_pos + x_offset, y_pos + y_offset))
                        
                        else: # game_type == 'xiangqi'
                            # Logic Cờ Tướng (căn giữa GIAO ĐIỂM)
                            corner_x = PADDING_X + c * SQUARE_SIZE_W
                            corner_y = PADDING_Y + r * SQUARE_SIZE_H
                            
                            blit_x = corner_x - image.get_width() // 2
                            blit_y = corner_y - image.get_height() // 2
                            
                            self.screen.blit(image, (blit_x, blit_y))
                            
                    else:
                        # Vẽ chữ dự phòng (nếu không tìm thấy ảnh)
                        text_surface = self.fallback_font.render(symbol, True, (255, 0, 0))
                        if self.game_logic.game_type == 'chess':
                            x_pos = c * (WIDTH // self.cols) + 10
                            y_pos = r * (HEIGHT // self.rows) + 10
                            self.screen.blit(text_surface, (x_pos, y_pos))
                        else:
                            corner_x = PADDING_X + c * SQUARE_SIZE_W
                            corner_y = PADDING_Y + r * SQUARE_SIZE_H
                            self.screen.blit(text_surface, (corner_x - 10, corner_y - 10))

    def draw_highlights(self):
        """Vẽ highlight cho ô đang chọn và các nước đi hợp lệ."""
        
        # --- SỬA LOGIC VẼ HIGHLIGHT ---
        if self.game_logic.game_type == 'chess':
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            
            # Vẽ các nước đi hợp lệ (vòng tròn)
            if self.possible_moves:
                for move in self.possible_moves:
                    r, c = move
                    move_surf = pygame.Surface((square_w, square_h), pygame.SRCALPHA)
                    move_surf.set_alpha(120) 
                    pygame.draw.circle(move_surf, (0, 100, 0), (square_w // 2, square_h // 2), 20)
                    self.screen.blit(move_surf, (c * square_w, r * square_h))
            
            # Vẽ ô đang được chọn
            if self.selected_piece_pos:
                r, c = self.selected_piece_pos
                highlight_surf = pygame.Surface((square_w, square_h))
                highlight_surf.set_alpha(100)
                highlight_surf.fill(HIGHLIGHT_COLOR) 
                self.screen.blit(highlight_surf, (c * square_w, r * square_h))
                
        else: # game_type == 'xiangqi'
            
            # Vẽ các nước đi hợp lệ (vòng tròn trên giao điểm)
            if self.possible_moves:
                for move in self.possible_moves:
                    r, c = move
                    corner_x = PADDING_X + c * SQUARE_SIZE_W
                    corner_y = PADDING_Y + r * SQUARE_SIZE_H
                    
                    move_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    move_surf.set_alpha(120) 
                    pygame.draw.circle(move_surf, (0, 100, 0), (corner_x, corner_y), 20)
                    self.screen.blit(move_surf, (0, 0))

            # Vẽ ô đang được chọn (hình vuông trên giao điểm)
            if self.selected_piece_pos:
                r, c = self.selected_piece_pos
                corner_x = PADDING_X + c * SQUARE_SIZE_W
                corner_y = PADDING_Y + r * SQUARE_SIZE_H
                
                highlight_surf = pygame.Surface((SQUARE_SIZE_W, SQUARE_SIZE_H), pygame.SRCALPHA)
                highlight_surf.set_alpha(100)
                highlight_surf.fill(HIGHLIGHT_COLOR) 
                # Căn giữa highlight trên giao điểm
                self.screen.blit(highlight_surf, (corner_x - SQUARE_SIZE_W / 2, corner_y - SQUARE_SIZE_H / 2))