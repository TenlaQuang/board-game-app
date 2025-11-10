import pygame
from utils.constants import WHITE, BLACK

class ChatBox:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.messages = []
        self.input_text = ""
        self.active = False

    def handle_event(self, e, connection=None):
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(e.pos)
        elif e.type == pygame.KEYDOWN and self.active:
            if e.key == pygame.K_RETURN and self.input_text:
                msg = self.input_text
                self.messages.append(("Bạn", msg))
                self.input_text = ""
                if connection:
                    connection.send(f"CHAT:{msg}")
            elif e.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += e.unicode

    def draw(self, surface):
        pygame.draw.rect(surface, (40, 40, 40), self.rect)
        y_offset = self.rect.y + 10
        for name, msg in self.messages[-10:]:
            line = self.font.render(f"{name}: {msg}", True, WHITE)
            surface.blit(line, (self.rect.x + 10, y_offset))
            y_offset += 24

        # Input
        input_rect = pygame.Rect(self.rect.x, self.rect.bottom - 35, self.rect.w, 30)
        pygame.draw.rect(surface, (60, 60, 60), input_rect)
        txt = self.font.render(self.input_text, True, WHITE)
        surface.blit(txt, (input_rect.x + 5, input_rect.y + 5))
