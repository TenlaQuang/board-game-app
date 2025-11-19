import json
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
    def __init__(self, screen: pygame.Surface, game_logic: Board, piece_assets: dict, board_rect, network_manager=None, my_role=None):
        self.screen = screen
        self.game_logic = game_logic
        self.piece_assets = piece_assets
        self.board_rect = board_rect
        
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
        
        with open("theme.json", "r", encoding="utf-8") as f:
            theme = json.load(f)

        font_path = theme["defaults"]["font"]["regular_path"]

        self.fallback_font = pygame.font.Font(font_path, 30)
        self.winner_font   = pygame.font.Font(font_path, 80)
        self.info_font     = pygame.font.Font(font_path, 40)

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
        # --- CHẶN CLICK NẾU GAME OVER ---
        if self.game_logic.game_over: return 

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.game_logic.is_my_turn(): return

                pos = pygame.mouse.get_pos()
                
                if self.game_logic.game_type == 'chess':
                    screen_col = pos[0] // (WIDTH // self.cols)
                    screen_row = pos[1] // (HEIGHT // self.rows)
                else:
                    screen_col = round((pos[0] - PADDING_X) / SQUARE_SIZE_W)
                    screen_row = round((pos[1] - PADDING_Y) / SQUARE_SIZE_H)
                
                logic_row, logic_col = self.from_screen_pos(screen_row, screen_col)

                if 0 <= logic_row < self.rows and 0 <= logic_col < self.cols:
                    clicked_pos = (logic_row, logic_col)

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
                            
                            self.selected_piece_pos = None
                            self.possible_moves = []
                        else:
                            new_piece = self.game_logic.get_piece(clicked_pos)
                            current_piece = self.game_logic.get_piece(from_pos)
                            if new_piece and current_piece and new_piece.color == current_piece.color:
                                self.selected_piece_pos = clicked_pos
                                self.possible_moves = new_piece.valid_moves(self.game_logic.board, clicked_pos)
                                return 
                            
                            self.selected_piece_pos = None
                            self.possible_moves = []
                    else:
                        piece = self.game_logic.get_piece(clicked_pos)
                        if piece:
                            if self.game_logic.my_color and piece.color != self.game_logic.my_color:
                                return
                            self.selected_piece_pos = clicked_pos
                            self.possible_moves = piece.valid_moves(self.game_logic.board, clicked_pos)

    def update(self):
        if self.network_manager:
            while not self.network_manager.p2p_queue.empty():
                try:
                    msg = self.network_manager.p2p_queue.get_nowait()
                    if msg.get("type") == "move":
                        self.game_logic.move_piece(tuple(msg["from"]), tuple(msg["to"]))
                except Exception as e:
                    print(f"Lỗi update: {e}")

    def draw(self):
        self.draw_board_squares()
        self.draw_highlights()
        self.draw_pieces()
        
        # --- [SỬA] VẼ MÀN HÌNH CHIẾN THẮNG ---
        if self.game_logic.game_over:
            self.draw_game_over_message()
        # -------------------------------------
        
    def draw_board_squares(self):
        if self.game_logic.game_type == 'chess':
            square_w = WIDTH // self.cols
            square_h = HEIGHT // self.rows
            for r in range(self.rows):
                for c in range(self.cols):
                    color = LIGHT_SQUARE_COLOR if (r + c) % 2 == 0 else DARK_SQUARE_COLOR
                    pygame.draw.rect(self.screen, color, (c * square_w, r * square_h, square_w, square_h))
        else: 
            if XIANGQI_BOARD_IMG: self.screen.blit(XIANGQI_BOARD_IMG, (0, 0))
            else: self.screen.fill(LIGHT_SQUARE_COLOR)

    def draw_pieces(self):
        board_state = self.game_logic.get_board_state()
        for logic_r in range(self.rows):
            for logic_c in range(self.cols):
                symbol = board_state[logic_r][logic_c]
                if symbol:
                    image = self.piece_assets.get(symbol)
                    if image:
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                        if self.game_logic.game_type == 'chess':
                            sw = WIDTH // self.cols
                            sh = HEIGHT // self.rows
                            self.screen.blit(image, (screen_c*sw + (sw-image.get_width())//2, screen_r*sh + (sh-image.get_height())//2))
                        else:
                            cx = PADDING_X + screen_c * SQUARE_SIZE_W
                            cy = PADDING_Y + screen_r * SQUARE_SIZE_H
                            self.screen.blit(image, (cx - image.get_width()//2, cy - image.get_height()//2))
                    else:
                        screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                        text = self.fallback_font.render(symbol, True, (255,0,0))
                        self.screen.blit(text, (screen_c*50, screen_r*50))

    def draw_highlights(self):
        if self.possible_moves:
            for logic_r, logic_c in self.possible_moves:
                screen_r, screen_c = self.to_screen_pos(logic_r, logic_c)
                if self.game_logic.game_type == 'chess':
                    sw, sh = WIDTH // self.cols, HEIGHT // self.rows
                    s = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    pygame.draw.circle(s, (0, 100, 0, 120), (sw//2, sh//2), 15)
                    self.screen.blit(s, (screen_c*sw, screen_r*sh))
                else:
                    cx, cy = PADDING_X + screen_c*SQUARE_SIZE_W, PADDING_Y + screen_r*SQUARE_SIZE_H
                    pygame.draw.circle(self.screen, (0, 200, 0), (cx, cy), 10)

        if self.selected_piece_pos:
            screen_r, screen_c = self.to_screen_pos(*self.selected_piece_pos)
            if self.game_logic.game_type == 'chess':
                sw, sh = WIDTH // self.cols, HEIGHT // self.rows
                s = pygame.Surface((sw, sh), pygame.SRCALPHA)
                s.fill((*HIGHLIGHT_COLOR, 100))
                self.screen.blit(s, (screen_c*sw, screen_r*sh))
            else:
                cx, cy = PADDING_X + screen_c*SQUARE_SIZE_W, PADDING_Y + screen_r*SQUARE_SIZE_H
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (cx, cy), 15, 2)

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
        
        txt_surf = self.winner_font.render(text, True, color)
        self.screen.blit(txt_surf, txt_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))
        
        sub_txt = self.info_font.render("Nhấn ESC để thoát", True, (200,200,200))
        self.screen.blit(sub_txt, sub_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))