# ui/board_ui.py
import pygame
from core.board import Board # Import "bộ não" Board của bạn
from utils.constants import (
    WIDTH, HEIGHT,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, HIGHLIGHT_COLOR
)

class BoardUI:
    """
    Lớp này chịu trách nhiệm vẽ bàn cờ, quân cờ,
    và xử lý input của người chơi (click chuột) trên bàn cờ.
    """
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
        
        # Tự động lấy kích thước từ logic
        self.rows = self.game_logic.rows
        self.cols = self.game_logic.cols
        
        # Tính toán kích thước ô cờ (cho cả 2 loại cờ)
        self.square_size_width = WIDTH // self.cols
        self.square_size_height = HEIGHT // self.rows 
        
        self.selected_piece_pos = None # Vị trí (row, col) của quân đang được chọn
        self.possible_moves = []       # Các nước đi hợp lệ cho quân đang chọn

    def handle_events(self, event: pygame.event.Event):
        """Xử lý click chuột để chọn/di chuyển quân."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click chuột trái
                pos = pygame.mouse.get_pos()
                
                # Tính (row, col) từ vị trí click
                col = pos[0] // self.square_size_width
                row = pos[1] // self.square_size_height
                
                # Đảm bảo click nằm trong bàn cờ
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    clicked_pos = (row, col)

                    if self.selected_piece_pos:
                        # --- Đã có quân được chọn -> Đây là nước đi ---
                        from_pos = self.selected_piece_pos
                        to_pos = clicked_pos
                        
                        # Kiểm tra xem nước đi có hợp lệ không
                        if to_pos in self.possible_moves:
                            print(f"Di chuyển hợp lệ từ {from_pos} đến {to_pos}")
                            self.game_logic.move_piece(from_pos, to_pos)
                        else:
                            # Nếu click vào ô không hợp lệ (hoặc ô cũ),
                            # hãy kiểm tra xem có phải đang chọn quân khác không
                            new_piece = self.game_logic.get_piece(clicked_pos)
                            if new_piece and new_piece.color == self.game_logic.get_piece(from_pos).color:
                                # Chọn quân khác cùng màu
                                self.selected_piece_pos = clicked_pos
                                print(f"Đổi chọn quân: {new_piece} tại {clicked_pos}")
                                self.possible_moves = new_piece.valid_moves(self.game_logic.board, clicked_pos)
                                print("Nước đi hợp lệ:", self.possible_moves)
                                return # Dừng lại, không bỏ chọn
                            else:
                                print(f"Nước đi không hợp lệ: {from_pos} -> {to_pos}")
                        
                        # Bỏ chọn sau khi đi (hoặc click ra ngoài)
                        self.selected_piece_pos = None
                        self.possible_moves = []
                        
                    else:
                        # --- Đây là lần click đầu tiên -> Chọn quân ---
                        piece = self.game_logic.get_piece(clicked_pos)
                        if piece: # và piece.color == lượt_hiện_tại (sẽ thêm sau)
                            self.selected_piece_pos = clicked_pos
                            print(f"Đã chọn quân: {piece} tại {clicked_pos}")
                            
                            # Tính toán các nước đi hợp lệ
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
        for r in range(self.rows):
            for c in range(self.cols):
                # Màu ô cờ xen kẽ cho Cờ Vua
                if self.game_logic.game_type == 'chess':
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                else: 
                    # Cờ Tướng dùng 1 màu nền (hoặc ảnh nền, nhưng giờ dùng màu)
                    color = LIGHT_SQUARE_COLOR 
                
                pygame.draw.rect(
                    self.screen, 
                    color, 
                    (c * self.square_size_width, r * self.square_size_height, self.square_size_width, self.square_size_height)
                )
        # TODO: Vẽ sông, cung điện cho Cờ Tướng

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
                        # Căn giữa ảnh vào ô (nếu ảnh nhỏ hơn ô)
                        x_offset = (self.square_size_width - image.get_width()) // 2
                        y_offset = (self.square_size_height - image.get_height()) // 2
                        
                        self.screen.blit(image, (x_pos + x_offset, y_pos + y_offset))
                    else:
                        # Vẽ chữ nếu không tìm thấy ảnh
                        x_pos = c * self.square_size_width
                        y_pos = r * self.square_size_height
                        font = pygame.font.Font(None, 30)
                        text_surface = font.render(symbol, True, (255, 0, 0)) # Màu đỏ cho dễ thấy
                        self.screen.blit(text_surface, (x_pos + 10, y_pos + 10))

    def draw_highlights(self):
        """Vẽ highlight cho ô đang chọn và các nước đi hợp lệ."""
        
        # Vẽ các nước đi hợp lệ (vòng tròn)
        if self.possible_moves:
            for move in self.possible_moves:
                r, c = move
                center_x = int(c * self.square_size_width + self.square_size_width / 2)
                center_y = int(r * self.square_size_height + self.square_size_height / 2)
                
                # Tạo 1 surface nhỏ cho vòng tròn trong suốt
                move_surf = pygame.Surface((self.square_size_width, self.square_size_height), pygame.SRCALPHA)
                move_surf.set_alpha(120) # Độ trong suốt 
                pygame.draw.circle(move_surf, (0, 100, 0), (self.square_size_width // 2, self.square_size_height // 2), 20) # Vẽ vòng tròn xanh đậm
                self.screen.blit(move_surf, (c * self.square_size_width, r * self.square_size_height))

        # Vẽ ô đang được chọn (hình vuông, đè lên trên)
        if self.selected_piece_pos:
            r, c = self.selected_piece_pos
            x = c * self.square_size_width
            y = r * self.square_size_height
            
            # Vẽ 1 hình chữ nhật màu vàng, hơi trong suốt
            highlight_surf = pygame.Surface((self.square_size_width, self.square_size_height))
            highlight_surf.set_alpha(100) # Độ trong suốt
            highlight_surf.fill(HIGHLIGHT_COLOR) 
            self.screen.blit(highlight_surf, (x, y))