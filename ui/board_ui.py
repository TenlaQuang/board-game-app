# ui/board_ui.py
import pygame
from core.board import Board # Import lớp Board của bạn
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR
)

class BoardUI:
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict):
        """
        Khởi tạo màn hình chơi game.
        :param screen: Surface để vẽ lên.
        :param game_logic: Đối tượng Board (chứa trạng thái cờ vua hoặc cờ tướng).
        :param piece_assets: Dict chứa ảnh của các quân cờ (CHESS_PIECES hoặc XIANGQI_PIECES).
        """
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        # Tính toán kích thước ô cờ
        self.square_size_width = WIDTH // self.cols
        # Cờ Tướng thường có chiều cao lớn hơn chiều rộng 1 chút
        self.square_size_height = HEIGHT // self.rows 
        
        self.selected_piece_pos = None # Vị trí (row, col) của quân đang được chọn
        self.possible_moves = []       # Các nước đi hợp lệ cho quân đang chọn

    def handle_events(self, event: pygame.event.Event):
        """Xử lý click chuột để chọn/di chuyển quân."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click chuột trái
                pos = pygame.mouse.get_pos()
                col = pos[0] // self.square_size_width
                row = pos[1] // self.square_size_height
                
                clicked_pos = (row, col)

                if self.selected_piece_pos:
                    # Đã có quân được chọn, đây là nước đi
                    from_pos = self.selected_piece_pos
                    to_pos = clicked_pos
                    
                    # TODO: Thực sự kiểm tra nước đi có hợp lệ không
                    # (Logic valid_moves nằm trong Piece class)
                    # if to_pos in self.possible_moves:
                    if self.game_logic.move_piece(from_pos, to_pos):
                        print(f"Di chuyển thành công từ {from_pos} đến {to_pos}")
                    else:
                        print("Nước đi không hợp lệ (hoặc không phải nước đi)")
                    
                    self.selected_piece_pos = None
                    self.possible_moves = []
                else:
                    # Lần click đầu tiên, chọn quân
                    piece = self.game_logic.get_piece(clicked_pos)
                    if piece: # và piece.color == lượt_hiện_tại
                        self.selected_piece_pos = clicked_pos
                        print(f"Đã chọn quân: {piece} tại {clicked_pos}")
                        
                        # TODO: Tính toán các nước đi hợp lệ của quân này
                        # self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)
                        # print("Nước đi hợp lệ:", self.possible_moves)

    def update(self):
        """Cập nhật logic game (nếu có animation hoặc tính toán gì đó)."""
        pass

    def draw(self):
        """Vẽ bàn cờ và các quân cờ lên màn hình."""
        self.draw_board_squares()
        self.draw_highlights() # Vẽ highlight trước quân cờ
        self.draw_pieces()
        
    def draw_board_squares(self):
        """Vẽ các ô sáng/tối của bàn cờ."""
        for r in range(self.rows):
            for c in range(self.cols):
                # Màu ô cờ xen kẽ
                if self.game_logic.game_type == 'chess':
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                else: # Cờ Tướng không có ô đen trắng xen kẽ
                    color = LIGHT_SQUARE_COLOR # Có thể dùng 1 màu nền hoặc ảnh nền
                
                pygame.draw.rect(
                    self.screen, 
                    color, 
                    (c * self.square_size_width, r * self.square_size_height, self.square_size_width, self.square_size_height)
                )

    def draw_pieces(self):
        """Vẽ tất cả quân cờ lên bàn cờ."""
        board_state_symbols = self.game_logic.get_board_state() # Lấy trạng thái bàn cờ dạng symbols
        
        for r in range(self.rows):
            for c in range(self.cols):
                symbol = board_state_symbols[r][c] # 'K', 'p', 'G', 'c' ...
                if symbol:
                    # Lấy ảnh tương ứng từ dict assets đã truyền vào
                    image = self.piece_assets.get(symbol) 
                    if image:
                        x_pos = c * self.square_size_width
                        y_pos = r * self.square_size_height
                        self.screen.blit(image, (x_pos, y_pos))
                    else:
                        print(f"Cảnh báo: Không tìm thấy ảnh cho quân cờ: {symbol}")
                        # Có thể vẽ placeholder hoặc text nếu không có ảnh
                        font = pygame.font.Font(None, 30)
                        text_surface = font.render(symbol, True, (0,0,0))
                        self.screen.blit(text_surface, (x_pos + self.square_size_width//4, y_pos + self.square_size_height//4))

    def draw_highlights(self):
        """Vẽ highlight cho ô đang chọn và các nước đi hợp lệ."""
        if self.selected_piece_pos:
            r, c = self.selected_piece_pos
            x = c * self.square_size_width
            y = r * self.square_size_height
            
            # Highlight ô đang chọn (màu vàng)
            highlight_surf = pygame.Surface((self.square_size_width, self.square_size_height))
            highlight_surf.set_alpha(100) # Độ trong suốt
            highlight_surf.fill(HIGHLIGHT_COLOR) 
            self.screen.blit(highlight_surf, (x, y))
            
            # TODO: Highlight các nước đi hợp lệ
            # for move_r, move_c in self.possible_moves:
            #     move_x = move_c * self.square_size_width
            #     move_y = move_r * self.square_size_height
            #     pygame.draw.circle(self.screen, (0, 255, 0, 100), 
            #                        (move_x + self.square_size_width // 2, move_y + self.square_size_height // 2), 
            #                        self.square_size_width // 4)