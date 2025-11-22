import numpy as np
import torch

# Map quân cờ (Viết hoa: Đỏ/Trắng, Viết thường: Đen)
# Pikafish dùng: R, N, B, A, K, C, P
PIECE_MAP = {
    'R': 0, 'N': 1, 'B': 2, 'A': 3, 'K': 4, 'C': 5, 'P': 6, 
    'r': 7, 'n': 8, 'b': 9, 'a': 10, 'k': 11, 'c': 12, 'p': 13
}

def fen_to_tensor(fen):
    # Tensor: 14 lớp x 10 hàng x 9 cột
    board = np.zeros((14, 10, 9), dtype=np.float32)
    position = fen.split(' ')[0]
    rows = position.split('/')
    
    for r, row_str in enumerate(rows):
        c = 0
        for char in row_str:
            if char.isdigit():
                c += int(char)
            else:
                if char in PIECE_MAP:
                    layer = PIECE_MAP[char]
                    if r < 10 and c < 9: # Check an toàn
                        board[layer][r][c] = 1.0
                c += 1
    return torch.from_numpy(board)