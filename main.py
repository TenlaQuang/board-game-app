# main.py

# Import class 'App' từ gói 'ui'
# (ui/__init__.py sẽ lo việc tìm 'App' từ ui/window.py)
from ui import App

def main():
    # 2. Khởi tạo App
    game_app = App()
    
    # 3. Chạy
    game_app.run()

if __name__ == "__main__":
    main()