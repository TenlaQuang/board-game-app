import pygame
from utils.constants import (
    LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, 
    XIANGQI_LIGHT_BACKGROUND_COLOR, XIANGQI_DARK_BACKGROUND_COLOR
)

class AnimatedBackground:
    """
    Một lớp đa năng để vẽ và cuộn nền dạng ô vuông một cách vô hạn.
    Có thể tùy chỉnh màu sắc và kích thước ô.
    """
    def __init__(self, screen_width, screen_height, square_size=100, scroll_speed=10, 
                 light_color=LIGHT_SQUARE_COLOR, dark_color=DARK_SQUARE_COLOR):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.square_size = square_size
        self.scroll_speed = scroll_speed
        self.light_color = light_color
        self.dark_color = dark_color

        # Kích thước surface cần lớn hơn màn hình để cuộn mượt
        self.loop_size = self.square_size * 2
        
        # Kích thước surface lớn hơn màn hình + kích thước lặp
        self.surface_width = self.screen_width + self.loop_size
        self.surface_height = self.screen_height + self.loop_size
        
        # Tạo surface (bảng vẽ) một lần duy nhất
        self.surface = pygame.Surface((self.surface_width, self.surface_height))
        self._draw_pattern() # Vẽ họa tiết lên surface

        self.scroll_x = 0.0
        self.scroll_y = 0.0

    def _draw_pattern(self):
        """Vẽ họa tiết ô vuông (lớn) lên surface nội bộ."""
        # Tính toán số hàng/cột cần vẽ để lấp đầy surface
        rows = self.surface_height // self.square_size + 1 # +1 để đảm bảo bao phủ
        cols = self.surface_width // self.square_size + 1 # +1 để đảm bảo bao phủ
        
        for r in range(rows):
            for c in range(cols):
                # Chọn màu xen kẽ
                color = self.light_color if (r + c) % 2 == 0 else self.dark_color
                pygame.draw.rect(
                    self.surface, 
                    color, 
                    (c * self.square_size, r * self.square_size, self.square_size, self.square_size)
                )

    def update(self, time_delta):
        """Cập nhật vị trí cuộn (scroll) dựa trên thời gian."""
        self.scroll_x += self.scroll_speed * time_delta
        self.scroll_y += self.scroll_speed * time_delta
        
        # Reset vị trí cuộn khi nó vượt quá kích thước lặp (self.loop_size)
        # để tạo hiệu ứng cuộn vô hạn
        self.scroll_x %= self.loop_size
        self.scroll_y %= self.loop_size

    def draw(self, screen: pygame.Surface):
        """Vẽ nền đang cuộn lên màn hình chính."""
        
        # Vị trí vẽ luôn là số âm, di chuyển từ 0 đến -self.loop_size
        x_offset = -self.scroll_x
        y_offset = -self.scroll_y
        
        # Vẽ surface lớn của chúng ta lên màn hình tại vị trí đã cuộn
        screen.blit(self.surface, (x_offset, y_offset))

