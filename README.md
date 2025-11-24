# Board Game P2P lai♟️

Dự án game cờ vua và cờ tướng peer-to-peer viết bằng Python + Pygame theo hướng OOP.

## Cấu trúc thư mục

- `ai/`: Chứa mô hình AI cho 2 game
- `core/`: Logic game (bàn cờ, quân cờ, luật di chuyển)
- `network/`: Xử lý kết nối mạng (host/client)
- `ui/`: Giao diện pygame
- `games/`: Các loại game (cờ vua, cờ tướng)
- `utils/`: Các hàm tiện ích và hằng số
- `tests/`: Unit test

## Cách chạy app chơi cờ sử dụng P2P lai 

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Tham khảo code server giúp client trao đổi ip tại: [Repository này](https://github.com/TenlaQuang/board-game-app-sv)
### Tham khảo bot chinese chess (xiangqi) tại: [Repository này](https://github.com/TenlaQuang/chinese-chess-model)

### Đây là địa chỉ web render https://board-game-app-sv.onrender.com

server sẽ chạy dựa trên repository board-game-app-sv và luôn hoạt động để hỗ trợ app.
