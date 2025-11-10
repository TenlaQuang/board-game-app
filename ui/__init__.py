# ui/__init__.py

# Dòng này có nghĩa là: 
# "Bất cứ ai import từ package 'ui', hãy cho họ thấy class 'App' từ file 'window' (cùng thư mục)"
from .window import GameApp

# Tương tự, "quảng bá" class MainMenu từ file menu.py
from .menu import MenuScreen

# "Quảng bá" hàm load_assets từ file assets.py
# from .assets import load_assets

# (Bạn có thể thêm cả BoardUI, v.v...)
# from .board_ui import BoardUI
# ui/__init__.py

# Quảng bá class chính


# Quảng bá các class "Cảnh"
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu
from .xiangqi_menu import XiangqiMenu

# Quảng bá các hàm và tài nguyên
from .assets import load_assets, CHESS_PIECES, XIANGQI_PIECES
