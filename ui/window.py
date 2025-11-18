# ui/window.py (Phiên bản hoàn chỉnh, hỗ trợ PLAY_ONLINE không block UI)
import threading
import pygame
import pygame_gui
from utils.constants import (
    WIDTH, HEIGHT, FPS,
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR,
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)
from core import Board

# Import TẤT CẢ các "cảnh" (scenes) của bạn
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu      # Cảnh menu cờ vua
from .xiangqi_menu import XiangqiMenu # Cảnh menu cờ tướng
from .animated_background import AnimatedBackground # <-- LỚP NỀN CHUYỂN ĐỘNG

# Import TẤT CẢ các tài nguyên
from ui.assets import (
    load_assets,
    CHESS_PIECES, XIANGQI_PIECES,
    MAIN_MENU_BACKGROUND  # Chỉ cần nền của menu chính
)


class App:
    def __init__(self, network_manager, server_ip, server_port):
        # Network
        self.network_manager = network_manager
        self.server_ip = server_ip
        self.server_port = server_port

        # Thread / state flags for online flow
        self._online_thread = None
        self._online_result = None      # (ip, port) on success
        self._online_error = None       # error message
        self._online_connected = False  # True when P2P connected

        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Board Game P2P")
        self.clock = pygame.time.Clock()
        self.running = True

        # 1. Tải tất cả tài nguyên (ảnh nút, ảnh quân cờ, nền menu chính)
        load_assets()

        # 2. Khởi tạo UI Manager
        self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT), 'theme.json')

        # 3. Tạo TẤT CẢ các "màn hình" của game
        # Các màn hình này sẽ được ẩn/hiện khi cần
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.chess_menu = ChessMenu(self.screen, self.ui_manager)
        self.xiangqi_menu = XiangqiMenu(self.screen, self.ui_manager)

        self.game_screen = None  # Màn hình game chỉ được tạo khi vào trận

        # label hiển thị khi đang tìm online
        self.searching_label = None

        # --- 4. TẠO CÁC NỀN CHUYỂN ĐỘNG ---
        self.chess_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80,
            scroll_speed=120,
            light_color=LIGHT_SQUARE_COLOR,
            dark_color=DARK_SQUARE_COLOR
        )

        self.xiangqi_menu_background_animated = AnimatedBackground(
            WIDTH, HEIGHT,
            square_size=80,
            scroll_speed=150,
            light_color=XIANGQI_LIGHT_BACKGROUND_COLOR,
            dark_color=XIANGQI_DARK_BACKGROUND_COLOR
        )
        # ------------------------------------

        # 5. Đặt trạng thái game ban đầu
        self.state = 'MAIN_MENU'
        self.main_menu.show()  # Chỉ hiện menu chính lúc đầu

    # -------------------------
    # Main loop
    # -------------------------
    def run(self):
        """Vòng lặp game chính (State Machine)."""
        while self.running:
            # 1. Lấy time_delta (quan trọng cho FPS cao)
            time_delta = self.clock.tick(FPS) / 1000.0

            # --- 2. XỬ LÝ SỰ KIỆN ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                # Đưa sự kiện cho UI Manager
                self.ui_manager.process_events(event)

                # Đưa sự kiện cho "cảnh" (state) hiện tại
                if self.state == 'MAIN_MENU':
                    next_state = self.main_menu.handle_events(event)
                    if next_state == 'QUIT':
                        self.running = False
                    elif next_state == 'PLAY_CHESS':
                        self.main_menu.hide()
                        self.chess_menu.show()
                        self.state = 'CHESS_MENU'
                    elif next_state == 'PLAY_XIANGQI':
                        self.main_menu.hide()
                        self.xiangqi_menu.show()
                        self.state = 'XIANGQI_MENU'
                    elif next_state == 'PLAY_ONLINE':
                        # Bấm nút Chơi Online -> bắt đầu flow
                        print("[App] PLAY_ONLINE được kích hoạt!")
                        self.main_menu.hide()
                        self._begin_online_search()
                elif self.state == 'CHESS_MENU':
                    next_state = self.chess_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.chess_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_CHESS_QUICK':
                        self.chess_menu.hide()
                        game_logic = Board(game_type='chess')
                        board_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
                        self.game_screen = BoardUI(self.screen, game_logic, CHESS_PIECES, board_rect)
                        self.state = 'GAME_SCREEN'
                elif self.state == 'XIANGQI_MENU':
                    next_state = self.xiangqi_menu.handle_events(event)
                    if next_state == 'BACK_TO_MAIN_MENU':
                        self.xiangqi_menu.hide()
                        self.main_menu.show()
                        self.state = 'MAIN_MENU'
                    elif next_state == 'PLAY_XIANGQI_QUICK':
                        self.xiangqi_menu.hide()
                        game_logic = Board(game_type='chinese_chess')
                        board_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
                        self.game_screen = BoardUI(self.screen, game_logic, XIANGQI_PIECES, board_rect)
                        self.state = 'GAME_SCREEN'
                elif self.state == 'GAME_SCREEN':
                    if self.game_screen:
                        self.game_screen.handle_events(event)
                    # TODO: Thêm logic quay lại menu
                elif self.state == 'SEARCHING':
                    # Có thể muốn cho nút "Hủy" về menu, tạm không có
                    pass

            # --- 3. CẬP NHẬT LOGIC ---
            self.ui_manager.update(time_delta)

            # Poll background online thread result (không block GUI)
            self._poll_online_thread()

            # Cập nhật nền chuyển động (nếu đang ở state đó)
            if self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.update()
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.update(time_delta)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.update(time_delta)

            # --- 4. VẼ LÊN MÀN HÌNH ---
            # 4a. Vẽ nền (background) tùy theo state
            if self.state == 'MAIN_MENU':
                if MAIN_MENU_BACKGROUND:
                    self.screen.blit(MAIN_MENU_BACKGROUND, (0, 0))
                else:
                    self.screen.fill((20, 20, 20))
            elif self.state == 'CHESS_MENU':
                self.chess_menu_background_animated.draw(self.screen)
            elif self.state == 'XIANGQI_MENU':
                self.xiangqi_menu_background_animated.draw(self.screen)
            elif self.state == 'GAME_SCREEN' and self.game_screen:
                self.game_screen.draw()
            elif self.state == 'SEARCHING':
                # Nếu bạn muốn, vẽ 1 background tối giản khi đang tìm
                self.screen.fill((10, 10, 30))

            # 4b. Vẽ các nút UI (luôn ở trên cùng)
            self.ui_manager.draw_ui(self.screen)

            # 4c. Cập nhật màn hình
            pygame.display.flip()

        # End loop
        pygame.quit()

    # -------------------------
    # Online flow helpers
    # -------------------------
    def _begin_online_search(self):
        """Chuẩn bị UI và start thread tìm đối thủ online (LAN -> Web)."""
        # Hiện label "Đang tìm đối thủ..."
        if self.searching_label is None:
            self.searching_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((WIDTH // 2 - 150, HEIGHT // 2 - 20), (300, 40)),
                text="Đang tìm đối thủ... Vui lòng chờ",
                manager=self.ui_manager
            )
        else:
            self.searching_label.show()

        self.state = 'SEARCHING'
        self._online_result = None
        self._online_error = None
        self._online_connected = False

        # Start background thread (không block UI)
        self._online_thread = threading.Thread(target=self._online_search_and_connect, daemon=True)
        self._online_thread.start()

    def _online_search_and_connect(self):
        """
        Chạy trong thread nền:
         1) gọi network_manager.find_opponent(username)
         2) nếu tìm được -> gọi network_manager.connect_to_peer(ip, port)
         3) set flags tương ứng để main loop xử lý chuyển trạng thái
        """
        # username tạm (bạn có thể lấy từ UI)
        username = "Player1"

        # 1) find opponent (LAN ưu tiên, rồi web)
        try:
            print("[OnlineThread] Gọi find_opponent...")
            # Prefer NetworkManager.find_opponent if exists
            find_fn = getattr(self.network_manager, "find_opponent", None)
            if callable(find_fn):
                res = find_fn(username)
            else:
                # fallback: import từ network package
                try:
                    from network import find_opponent as net_find  # network/__init__.py
                    res = net_find(username)
                except Exception as e:
                    res = None
                    print("[OnlineThread] Không có hàm find_opponent:", e)

            if not res:
                self._online_error = "Không tìm thấy đối thủ (LAN/Web)."
                print("[OnlineThread]", self._online_error)
                return
            ip, port = res
            if port is None:
                # dùng port mặc định nếu đối phương không gửi port
                # lấy từ server_port đã truyền vào App (main.py)
                port = self.server_port or 12345
            self._online_result = (ip, port)
            print("[OnlineThread] Tìm thấy đối thủ:", self._online_result)

            # 2) Thực hiện kết nối P2P (NetworkManager chịu trách nhiệm)
            connect_fn = getattr(self.network_manager, "connect_to_peer", None)
            if callable(connect_fn):
                ok = connect_fn(ip, port)
            else:
                # fallback: nếu NetworkManager có _initiate_p2p_connection (your earlier code)
                init_fn = getattr(self.network_manager, "_initiate_p2p_connection", None)
                if callable(init_fn):
                    # note: signature might be (role, ip, port, opponent_username) in your class
                    # we try to call as client by default
                    try:
                        # attempt to act as client
                        init_fn(role='client', opponent_ip=ip, port=port, opponent_username="Opponent")
                        ok = True
                    except Exception as e:
                        print("[OnlineThread] fallback connect error:", e)
                        ok = False
                else:
                    ok = False

            if ok:
                self._online_connected = True
                print("[OnlineThread] Kết nối P2P thành công")
            else:
                self._online_error = "Kết nối P2P thất bại."
                print("[OnlineThread] Kết nối P2P thất bại")

        except Exception as e:
            self._online_error = f"Lỗi khi tìm/kết nối: {e}"
            print("[OnlineThread] Exception:", e)

    def _poll_online_thread(self):
        """Kiểm tra kết quả từ thread nền và cập nhật UI / state nếu cần."""
        # Nếu thread không tồn tại hoặc vẫn đang chạy -> nothing
        if self._online_thread and self._online_thread.is_alive():
            return

        # Nếu có lỗi xảy ra
        if self._online_error:
            # Ẩn label searching
            if self.searching_label:
                self.searching_label.hide()
            # Hiện thông báo lỗi (popup)
            pygame_gui.windows.UIMessageWindow(
                rect=pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 80, 400, 160),
                html_message=self._online_error,
                manager=self.ui_manager,
                window_title="Lỗi kết nối"
            )
            # Quay về menu chính
            self._online_thread = None
            self._online_result = None
            self._online_error = None
            self.state = 'MAIN_MENU'
            self.main_menu.show()
            return

        # Nếu đã kết nối thành công
        if self._online_connected and self._online_result:
            # Ẩn label searching
            if self.searching_label:
                self.searching_label.hide()

            ip, port = self._online_result
            # Tạo BoardUI (ở đây mặc định chess, bạn có thể điều chỉnh)
            try:
                game_logic = Board(game_type='chess')
                board_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
                self.game_screen = BoardUI(self.screen, game_logic, CHESS_PIECES, board_rect)
            except Exception as e:
                print("[App] Lỗi tạo BoardUI:", e)

            # chuyển state vào game
            self.state = 'GAME_SCREEN'

            # reset flags
            self._online_thread = None
            self._online_result = None
            self._online_error = None
            self._online_connected = False
            return

        # Nếu thread đã kết thúc nhưng không có kết quả -> quay lại menu
        if self._online_thread and not self._online_thread.is_alive() and not (self._online_connected or self._online_error):
            # Hơi hiếm, nhưng reset state
            if self.searching_label:
                self.searching_label.hide()
            self._online_thread = None
            self.state = 'MAIN_MENU'
            self.main_menu.show()

