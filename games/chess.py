# games/chess.py
import pygame
import threading # Dùng để AI suy nghĩ không làm đơ màn hình
from games.base_game import BaseGame
from core.board import Board  # Import class Board của bạn
from utils.constants import WHITE, BLUE, RED
from ai.engines.stockfish_adapter import StockfishAdapter

class ChessGame(BaseGame):
    def __init__(self, app, connection=None, player_name="Player", difficulty=None):
        # Gọi init của cha (BaseGame)
        super().__init__(app, connection, player_name)
        
        self.title = pygame.font.Font(None, 36).render("CỜ VUA", True, WHITE)
        
        # --- KHỞI TẠO BÀN CỜ ---
        self.board = Board('chess') # Tạo bàn cờ logic
        
        # --- LOGIC CHỌN QUÂN (HUMAN) ---
        self.selected_pos = None  # Tọa độ đang chọn (row, col)
        self.valid_moves = []     # Gợi ý nước đi

        # --- CẤU HÌNH AI (PvE) ---
        self.is_pve = difficulty is not None
        self.ai_engine = None
        self.ai_thinking = False # Cờ hiệu để biết máy đang tính
        
        if self.is_pve:
            print(f"[Chess] Chế độ đấu máy - Mức: {difficulty}")
            try:
                self.ai_engine = StockfishAdapter(difficulty)
                self.ai_color = 'black' # Máy luôn cầm quân đen
                self.board.set_player_color('white') # Người cầm trắng
            except Exception as e:
                print(f"Lỗi khởi tạo AI: {e}")
                self.is_pve = False # Tắt chế độ AI nếu lỗi

    def update(self, events):
        # 1. Xử lý sự kiện (Click chuột, Thoát)
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                # Chỉ cho người click khi không phải lượt máy (hoặc game over)
                if not self.game_over and not self.ai_thinking:
                    if self.is_pve and self.board.current_turn == self.ai_color:
                        pass # Lượt máy thì ko làm gì
                    else:
                        self.handle_click(e.pos)
            else:
                self.handle_event(e)

        # 2. Kiểm tra Logic Game Over từ Board
        if self.board.game_over and not self.game_over:
            self.game_over = True
            # Có thể thêm popup thông báo thắng thua ở đây

        # 3. Logic AI (Máy đi)
        # Nếu là PvE, chưa hết game, đúng lượt máy và máy chưa đang tính
        if self.is_pve and not self.game_over and \
           self.board.current_turn == self.ai_color and not self.ai_thinking:
            
            self.ai_thinking = True
            # Chạy AI trong luồng riêng để không đơ giao diện
            threading.Thread(target=self.run_ai_logic, daemon=True).start()

        # 4. Cập nhật mạng (nếu có)
        self.update_network()

    def run_ai_logic(self):
        """Hàm chạy ngầm để AI tính toán"""
        try:
            # Lấy FEN hiện tại
            fen = self.board.to_fen()
            # Hỏi Stockfish
            best_move_uci = self.ai_engine.get_best_move(fen)
            
            if best_move_uci:
                print(f"--> AI ({self.ai_color}) đi: {best_move_uci}")
                # Convert UCI (e7e5) -> Tọa độ ((1,4), (3,4))
                start, end, promo = self.board.uci_to_coords(best_move_uci)
                
                if start and end:
                    # Thực hiện nước đi trên bàn cờ logic
                    self.board.move_piece(start, end, promotion=promo)
            else:
                print("--> AI không tìm được nước đi!")
        except Exception as e:
            print(f"Lỗi trong luồng AI: {e}")
        
        # Tính xong thì tắt cờ hiệu
        self.ai_thinking = False

    def handle_click(self, pos_screen):
        """Xử lý logic chọn và đi quân của người chơi"""
        x, y = pos_screen
        
        # Kiểm tra click có nằm trong bàn cờ không (board_rect từ BaseGame)
        if not self.board_rect.collidepoint(x, y):
            return 

        # Tính tọa độ ô cờ (row, col)
        cell_size = self.board_rect.width // 8
        col = (x - self.board_rect.x) // cell_size
        row = (y - self.board_rect.y) // cell_size
        clicked_pos = (row, col)

        piece = self.board.get_piece(clicked_pos)

        # A. Chọn quân của mình
        if piece and piece.color == self.board.current_turn:
            self.selected_pos = clicked_pos
            # Nếu có validator thì lấy gợi ý
            if self.board.validator:
                self.valid_moves = self.board.validator.get_valid_moves(self.board, clicked_pos)
            print(f"Chọn: {piece.symbol} tại {clicked_pos}")

        # B. Di chuyển quân (Nếu đã chọn trước đó)
        elif self.selected_pos:
            # Thử di chuyển
            success = self.board.move_piece(self.selected_pos, clicked_pos)
            if success:
                # Đi thành công thì bỏ chọn
                self.selected_pos = None
                self.valid_moves = []
                
                # Nếu đang chơi Online, cần gửi nước đi qua mạng (Code sau)
                if self.conn:
                    move_str = f"MOVE:{self.selected_pos}->{clicked_pos}" 
                    self.conn.send(move_str) # Giả định hàm send
            else:
                print("Nước đi không hợp lệ!")

    def draw(self, screen):
        # 1. Vẽ nền và tiêu đề
        screen.fill((30, 30, 30))
        screen.blit(self.title, (self.board_rect.centerx - 50, 10))
        
        # 2. Vẽ khung chat (BaseGame lo)
        self.draw_base(screen)

        # 3. Vẽ bàn cờ
        cell_size = self.board_rect.width // 8
        
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(
                    self.board_rect.x + col * cell_size,
                    self.board_rect.y + row * cell_size,
                    cell_size,
                    cell_size
                )
                
                # Màu ô cờ
                color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                
                # Highlight nước vừa đi (Last Move)
                if self.board.last_move:
                    l_start = self.board.last_move['start']
                    l_end = self.board.last_move['end']
                    if (row, col) == l_start or (row, col) == l_end:
                        color = (205, 210, 106) # Màu vàng chanh

                pygame.draw.rect(screen, color, rect)

                # Highlight ô đang chọn (Selected)
                if self.selected_pos == (row, col):
                    s = pygame.Surface((cell_size, cell_size))
                    s.set_alpha(100) # Trong suốt
                    s.fill(BLUE)
                    screen.blit(s, rect)

                # 4. Vẽ Quân Cờ
                piece = self.board.board[row][col]
                if piece:
                    # Nếu Piece có thuộc tính image đã load xong
                    if hasattr(piece, 'image') and piece.image:
                        # Resize ảnh cho vừa ô
                        img = pygame.transform.scale(piece.image, (cell_size - 10, cell_size - 10))
                        img_rect = img.get_rect(center=rect.center)
                        screen.blit(img, img_rect)
                    else:
                        # Vẽ chữ thay thế nếu chưa có ảnh
                        font = pygame.font.SysFont("Arial", 40, bold=True)
                        txt_color = (0, 0, 0) if piece.color == 'white' else (255, 255, 255)
                        # Viền chữ để dễ đọc
                        txt = font.render(piece.symbol, True, txt_color)
                        screen.blit(txt, (rect.centerx - 10, rect.centery - 20))

        # 5. Vẽ chấm gợi ý nước đi
        for move in self.valid_moves:
            r, c = move
            cx = self.board_rect.x + c * cell_size + cell_size // 2
            cy = self.board_rect.y + r * cell_size + cell_size // 2
            pygame.draw.circle(screen, (100, 100, 100), (cx, cy), 8)
            
        # 6. Hiển thị trạng thái (AI thinking)
        if self.ai_thinking:
            waiting_text = self.font.render("Máy đang nghĩ...", True, (255, 0, 0))
            screen.blit(waiting_text, (self.board_rect.x, self.board_rect.bottom + 10))