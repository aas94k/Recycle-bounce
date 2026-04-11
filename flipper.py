"""
flipper.py — Recycle Bounce v2
Flippers cartoon rouge avec ombre et reflet.
"""
import pygame, math
from constants import COLOR_FLIPPER_MAIN, COLOR_FLIPPER_DARK, COLOR_WHITE, PHYS_SCALE, SCREEN_W

FLIPPER_LEN   = max(120, int(0.16 * SCREEN_W))
FLIPPER_W     = max(8, int(7 * PHYS_SCALE))
FLIPPER_SPEED = max(10, int(16 * PHYS_SCALE))
FLIPPER_RESTITUTION = 0.86

REST_LEFT   =  28
ACTIVE_LEFT = -30
REST_RIGHT  = 152
ACTIVE_RIGHT= 210


class Flipper:
    def __init__(self, side, x, y):
        self.side = side; self.px = x; self.py = y
        self.reset()

    def reset(self):
        if self.side == "left":
            self.angle = REST_LEFT; self.rest_angle = REST_LEFT; self.act_angle = ACTIVE_LEFT
        else:
            self.angle = REST_RIGHT; self.rest_angle = REST_RIGHT; self.act_angle = ACTIVE_RIGHT
        self.pressed = False
        self.ang_vel = 0.0

    def update(self, pressed):
        prev = self.angle
        self.pressed = pressed
        target = self.act_angle if pressed else self.rest_angle
        diff = target - self.angle
        while diff >  180: diff -= 360
        while diff < -180: diff += 360
        if abs(diff) < FLIPPER_SPEED: self.angle = target
        else: self.angle += FLIPPER_SPEED * (1 if diff > 0 else -1)
        self.ang_vel = self.angle - prev

    def _tip(self):
        rad = math.radians(self.angle)
        return (self.px + FLIPPER_LEN*math.cos(rad),
                self.py + FLIPPER_LEN*math.sin(rad))

    def check_collision(self, waste):
        tx, ty = self._tip()
        dx = tx - self.px; dy = ty - self.py
        sl = dx*dx + dy*dy
        if sl == 0: return False
        t = max(0.0, min(1.0, ((waste.x-self.px)*dx + (waste.y-self.py)*dy) / sl))
        cx = self.px + t*dx; cy = self.py + t*dy
        dist = math.hypot(waste.x-cx, waste.y-cy)
        if dist < waste.radius + FLIPPER_W:
            seg_len = math.hypot(tx-self.px, ty-self.py)
            if seg_len <= 1e-6:
                return False
            nx = -(ty-self.py) / seg_len
            ny =  (tx-self.px) / seg_len
            if ny > 0: nx, ny = -nx, -ny
            # Reflect incoming velocity for precision, then add swing impulse for "snap".
            dot = waste.vx*nx + waste.vy*ny
            waste.vx = waste.vx - (1.0 + FLIPPER_RESTITUTION) * dot * nx
            waste.vy = waste.vy - (1.0 + FLIPPER_RESTITUTION) * dot * ny

            swing = abs(self.ang_vel)
            base = (420 if self.pressed else 180) * PHYS_SCALE
            impulse = base + swing * (30 * PHYS_SCALE)
            waste.vx += nx * impulse
            waste.vy += ny * impulse
            overlap = waste.radius + FLIPPER_W - dist
            waste.x += nx*overlap; waste.y += ny*overlap
            if hasattr(waste, "stabilize_trajectory"):
                waste.stabilize_trajectory()
            if hasattr(waste, "limit_speed"):
                waste.limit_speed()
            return True
        return False

    def draw(self, surface):
        tx, ty = self._tip()
        px, py = int(self.px), int(self.py)
        dx, dy = tx - self.px, ty - self.py
        seg_len = math.hypot(dx, dy)
        if seg_len <= 1e-6:
            return

        outline_width = FLIPPER_W + 14   # wider outline for strong contrast
        body_width = FLIPPER_W
        highlight_width = max(2, FLIPPER_W // 3)

        # Warm-white outline pill (slightly cream, not pure white — avoids eye-strain)
        OUTLINE_COL = (255, 240, 210)
        pygame.draw.line(surface, OUTLINE_COL, (px, py), (int(tx), int(ty)), outline_width)
        pygame.draw.circle(surface, OUTLINE_COL, (px, py), outline_width // 2)
        pygame.draw.circle(surface, OUTLINE_COL, (int(tx), int(ty)), outline_width // 2)

        # Main red body pill shape
        pygame.draw.line(surface, COLOR_FLIPPER_MAIN, (px, py), (int(tx), int(ty)), body_width)
        pygame.draw.circle(surface, COLOR_FLIPPER_MAIN, (px, py), body_width // 2)
        pygame.draw.circle(surface, COLOR_FLIPPER_MAIN, (int(tx), int(ty)), body_width // 2)

        # Subtle inner highlight for curvature
        highlight_col = tuple(min(255, c + 60) for c in COLOR_FLIPPER_MAIN)
        offset_x = int(-(dy / seg_len) * 2)
        offset_y = int((dx / seg_len) * 2)
        pygame.draw.line(surface, highlight_col,
                         (px + offset_x, py + offset_y),
                         (int(tx) + offset_x, int(ty) + offset_y),
                         highlight_width)

        # Simple pivot circle
        pygame.draw.circle(surface, COLOR_FLIPPER_DARK, (px, py), body_width // 2 + 2)
        pygame.draw.circle(surface, COLOR_FLIPPER_MAIN, (px, py), body_width // 2)
