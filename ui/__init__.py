# ui/__init__.py

# Quảng bá class chính (từ window.py)
from .window import App

# Quảng bá các class "Cảnh" (Scenes)
from .menu import MainMenu
from .board_ui import BoardUI
from .chess_menu import ChessMenu
from .xiangqi_menu import XiangqiMenu
from .animated_background import AnimatedBackground

# Quảng bá các hàm và tài nguyên (từ assets.py)
from .assets import load_assets, CHESS_PIECES, XIANGQI_PIECES