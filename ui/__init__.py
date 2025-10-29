# ui/__init__.py

# Dòng này có nghĩa là: 
# "Bất cứ ai import từ package 'ui', hãy cho họ thấy class 'App' từ file 'window' (cùng thư mục)"
from .window import App

# Tương tự, "quảng bá" class MainMenu từ file menu.py
from .menu import MainMenu

# "Quảng bá" hàm load_assets từ file assets.py
from .assets import load_assets

# (Bạn có thể thêm cả BoardUI, v.v...)
# from .board_ui import BoardUI