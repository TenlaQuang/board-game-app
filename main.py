import pygame

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Moving Block")

RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Tạo một hình chữ nhật để di chuyển
player_rect = pygame.Rect(350, 250, 50, 50)
player_speed = 5

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Cập nhật trạng thái game ---
    # Lấy trạng thái của tất cả các phím đang được nhấn
    keys = pygame.key.get_pressed()

    # Di chuyển hình chữ nhật dựa trên phím được nhấn
    if keys[pygame.K_LEFT]:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_rect.x += player_speed
    if keys[pygame.K_UP]:
        player_rect.y -= player_speed
    if keys[pygame.K_DOWN]:
        player_rect.y += player_speed

    # --- Vẽ vời ---
    screen.fill(WHITE)
    pygame.draw.rect(screen, RED, player_rect)

    # --- Cập nhật màn hình ---
    pygame.display.flip()

pygame.quit()