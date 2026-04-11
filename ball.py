"""
ball.py — Recycle Bounce v2
Waste sprite (PNG) with gravity, velocity, rotation, and pygame.Rect collision.
"""
from __future__ import annotations

import os
import pygame
import math
import random
from constants import HEADER_H, REF_H, SCREEN_H, SCALE_Y, PHYS_SCALE

GRAVITY = int(480 * SCALE_Y)
WALL_RESTITUTION = 0.82
MAX_SPEED = int(850 * PHYS_SCALE)
MIN_SPEED = int(100 * PHYS_SCALE)
DEFAULT_LAUNCH_SPEED = int(360 * PHYS_SCALE)
# Longest side of the waste PNG (scales with display height).
WASTE_MAX_SPRITE_DIM = max(380, int(380 * SCREEN_H / REF_H))

# PNG assets (transparency preserved via convert_alpha)
ASSETS = {
    "plastic": "plastic_bottle.png",
    "glass": "glass_bottle.png",
    "paper": "paper.png",
    "bio": "food.png",
}


def _asset_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "assets", filename)


class Waste:
    """
    One waste item on the table. Physics use center (x, y); collision uses
    the axis-aligned rect of the rotated sprite.
    """

    def __init__(self, x: float, y: float, waste_type: str, max_dim: int = WASTE_MAX_SPRITE_DIM):
        self.start_x = float(x)
        self.start_y = float(y)
        self.type = waste_type
        self.max_dim = int(max_dim)

        self._base_image = self._load_image(waste_type, self.max_dim)
        self.size = max(self._base_image.get_width(), self._base_image.get_height())
        self._mask_radius = self._compute_mask_radius(self._base_image)
        self._image = self._base_image
        self.angle = random.uniform(0, 360)
        self.ang_vel = random.uniform(-220, 220) * PHYS_SCALE

        self.reset(x, y, waste_type=waste_type)

    def _placeholder_surface(self, waste_type: str, dim: int) -> pygame.Surface:
        s = pygame.Surface((dim, dim), pygame.SRCALPHA)
        center = dim // 2
        
        if waste_type == "plastic":
            # Draw a plastic bottle
            bottle_color = (255, 200, 60, 255)
            cap_color = (100, 100, 100, 255)
            pygame.draw.rect(s, bottle_color, (center - 8, center - 12, 16, 20), border_radius=3)
            pygame.draw.rect(s, bottle_color, (center - 4, center - 16, 8, 8))
            pygame.draw.rect(s, cap_color, (center - 5, center - 18, 10, 4), border_radius=2)
            pygame.draw.rect(s, (200, 150, 50, 255), (center - 6, center - 8, 12, 6))
        elif waste_type == "glass":
            glass_color = (120, 200, 140, 200)
            cap_color = (80, 80, 80, 255)
            pygame.draw.rect(s, glass_color, (center - 6, center - 15, 12, 24), border_radius=2)
            pygame.draw.rect(s, glass_color, (center - 3, center - 18, 6, 6))
            pygame.draw.rect(s, cap_color, (center - 4, center - 20, 8, 3), border_radius=1)
            pygame.draw.line(s, (255, 255, 255, 100), (center - 4, center - 12), (center - 4, center - 2), 2)
        elif waste_type == "paper":
            paper_color = (240, 240, 240, 255)
            pygame.draw.rect(s, paper_color, (center - 10, center - 12, 18, 22), border_radius=1)
            pygame.draw.polygon(s, paper_color, [(center + 6, center - 12), (center + 8, center - 10), (center + 8, center - 12)])
            pygame.draw.line(s, (150, 150, 150, 255), (center - 8, center - 8), (center + 6, center - 8), 1)
            pygame.draw.line(s, (150, 150, 150, 255), (center - 8, center - 4), (center + 6, center - 4), 1)
            pygame.draw.line(s, (150, 150, 150, 255), (center - 8, center), (center + 6, center), 1)
        elif waste_type == "bio":
            banana_color = (255, 225, 50, 255)
            stem_color = (100, 150, 50, 255)
            pygame.draw.ellipse(s, banana_color, (center - 12, center - 8, 20, 12))
            pygame.draw.rect(s, stem_color, (center - 2, center - 10, 3, 4))
            pygame.draw.circle(s, (200, 180, 30, 255), (center - 6, center - 4), 1)
            pygame.draw.circle(s, (200, 180, 30, 255), (center, center - 2), 1)
        else:
            c = (200, 200, 200, 255)
            pygame.draw.circle(s, c, (center, center), dim // 2 - 2)
            pygame.draw.circle(s, (40, 40, 40, 200), (center, center), dim // 2 - 2, 2)
        return self._trim_transparent(s)

    def _trim_transparent(self, surf: pygame.Surface) -> pygame.Surface:
        rect = surf.get_bounding_rect()
        if rect.width == 0 or rect.height == 0:
            return surf
        return surf.subsurface(rect).copy()

    def _compute_mask_radius(self, surf: pygame.Surface) -> float:
        mask = pygame.mask.from_surface(surf)
        outline = mask.outline()
        if not outline:
            return max(surf.get_width(), surf.get_height()) * 0.4
        cx = surf.get_width() / 2.0
        cy = surf.get_height() / 2.0
        return max(math.hypot(x - cx, y - cy) for x, y in outline)

    def _load_image(self, waste_type: str, max_dim: int) -> pygame.Surface:
        filename = ASSETS.get(waste_type, ASSETS["plastic"])
        path = _asset_path(filename)
        try:
            img = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError, OSError):
            return self._placeholder_surface(waste_type, max_dim)

        w, h = img.get_width(), img.get_height()
        if w < 1 or h < 1:
            return self._placeholder_surface(waste_type, max_dim)

        scale = max_dim / max(w, h)
        nw = max(1, int(round(w * scale)))
        nh = max(1, int(round(h * scale)))
        return self._trim_transparent(pygame.transform.smoothscale(img, (nw, nh)))

    @property
    def radius(self) -> float:
        """Circular collider radius based on the visible waste sprite."""
        return self._mask_radius

    def sync_rect(self) -> None:
        self._image = pygame.transform.rotate(self._base_image, -self.angle)
        self.rect = self._image.get_rect(center=(int(self.x), int(self.y)))

    def reset(self, x: float, y: float, waste_type: str | None = None):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        if waste_type is not None and waste_type != self.type:
            self.type = waste_type
            self._base_image = self._load_image(self.type, self.max_dim)
            self.size = max(self._base_image.get_width(), self._base_image.get_height())
            self._mask_radius = self._compute_mask_radius(self._base_image)
        self._image = self._base_image
        self.angle = random.uniform(0, 360)
        self.ang_vel = random.uniform(-220, 220) * PHYS_SCALE
        self.sync_rect()

    def launch(self, speed: float | None = None):
        if speed is None:
            speed = float(DEFAULT_LAUNCH_SPEED)
        angle = math.radians(random.uniform(-8, 8))
        self.vx = speed * math.sin(angle)
        self.vy = -speed * math.cos(angle)

    def limit_speed(self):
        sp = math.hypot(self.vx, self.vy)
        if sp > MAX_SPEED:
            self.vx = self.vx / sp * MAX_SPEED
            self.vy = self.vy / sp * MAX_SPEED
        elif sp < MIN_SPEED and sp > 1e-6:
            self.vx = self.vx / sp * MIN_SPEED
            self.vy = self.vy / sp * MIN_SPEED

    def stabilize_trajectory(self):
        vy_t = 160 * SCALE_Y
        vx_t = 55 * PHYS_SCALE
        if self.vy > vy_t and abs(self.vx) < vx_t:
            self.vx = vx_t if self.vx >= 0 else -vx_t

    def update(self, dt, screen_w, screen_h):
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.ang_vel * dt) % 360
        self.stabilize_trajectory()
        self.limit_speed()

        half = self.size * 0.5
        if self.x - half < 0:
            self.x = half
            self.vx = abs(self.vx) * WALL_RESTITUTION
        elif self.x + half > screen_w:
            self.x = screen_w - half
            self.vx = -abs(self.vx) * WALL_RESTITUTION
        if self.y - half < HEADER_H:
            self.y = HEADER_H + half
            self.vy = abs(self.vy) * WALL_RESTITUTION

        self.sync_rect()

    def add_impulse(self, ix: float, iy: float):
        self.vx += ix
        self.vy += iy
        self.limit_speed()

    def draw(self, surface: pygame.Surface):
        # Soft ambient glow so the waste is always visible against the background
        gr = max(8, int(self.radius * 1.55))
        glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 255, 30), (gr, gr), gr)
        pygame.draw.circle(glow, (200, 230, 255, 18), (gr, gr), int(gr * 0.70))
        surface.blit(glow, (int(self.x) - gr, int(self.y) - gr))
        surface.blit(self._image, self.rect.topleft)
