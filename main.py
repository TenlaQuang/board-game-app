# Import thẳng từ package 'ui'
from ui import App  # <--- IMPORT LỚP (CLASS) 'App' TỪ GÓI 'ui'

def main(): # <--- ĐÂY LÀ HÀM (FUNCTION) KHỞI ĐỘNG
    
    # 2. Khởi tạo App
    game_app = App() # <--- DÙNG HÀM 'main' ĐỂ TẠO RA MỘT ĐỐI TƯỢNG (OBJECT) TỪ LỚP 'App'
    
    # 3. Chạy
    game_app.run()

if __name__ == "__main__": # <--- ĐÂY LÀ "ĐIỂM BẮT ĐẦU" KHI BẠN CHẠY FILE
    main() # <--- BẤM VÀO "CÔNG TẮC" (HÀM MAIN)