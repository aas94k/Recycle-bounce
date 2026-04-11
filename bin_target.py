"""
bin_target.py — Recycle Bounce v2
Poubelles de tri avec UI cartoon améliorée.
"""
import pygame
from constants import BIN_W, BIN_H
from draw_utils import draw_bin


def _circle_rect_collide(cx: float, cy: float, radius: float, rect: pygame.Rect) -> bool:
    nearest_x = max(rect.left, min(cx, rect.right))
    nearest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy <= radius * radius


class BinTarget:
    def __init__(self, label: str, color: tuple, icon: str, category: str, x: int, y: int):
        self.label    = label
        self.color    = color
        self.icon     = icon
        self.category = category
        self.x        = x
        self.y        = y
        self.rect     = pygame.Rect(x, y, BIN_W, BIN_H)
        self.flash    = 0

    def check_collision(self, waste) -> bool:
        """Circle-vs-rect collision using the visible waste sprite radius."""
        if _circle_rect_collide(waste.x, waste.y, waste.radius, self.rect):
            self.flash = 25
            return True
        return False

    def update(self):
        if self.flash > 0:
            self.flash -= 1

    def draw(self, surface, font_icon, font_sm):
        self.update()
        draw_bin(surface, self.label, self.color, self.icon,
                 self.x, self.y, BIN_W, BIN_H,
                 flashing=(self.flash > 0),
                 font=font_icon, font_sm=font_sm)
