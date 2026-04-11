"""
obstacles.py — Recycle Bounce v2
Static obstacles to make the table more skill-based (side guards/bumpers).
"""

from __future__ import annotations

import math
import pygame


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def _reflect(vx: float, vy: float, nx: float, ny: float, restitution: float) -> tuple[float, float]:
    # Reflect velocity across the collision normal.
    dot = vx * nx + vy * ny
    rvx = vx - (1.0 + restitution) * dot * nx
    rvy = vy - (1.0 + restitution) * dot * ny
    return rvx, rvy


class SegmentObstacle:
    """
    Thick line segment that behaves like an angled wall/guard.
    Collision is circle vs segment with a constant normal response.
    """

    def __init__(
        self,
        ax: float,
        ay: float,
        bx: float,
        by: float,
        thickness: int = 10,
        color: tuple[int, int, int] = (235, 240, 255),
        border: tuple[int, int, int] = (60, 120, 190),
        restitution: float = 0.88,
        tangential_damping: float = 0.985,
        kick: float = 0.0,
    ):
        self.ax = float(ax)
        self.ay = float(ay)
        self.bx = float(bx)
        self.by = float(by)
        self.thickness = int(thickness)
        self.color = color
        self.border = border
        self.restitution = float(restitution)
        self.tangential_damping = float(tangential_damping)
        self.kick = float(kick)

    def collide(self, waste) -> bool:
        dx = self.bx - self.ax
        dy = self.by - self.ay
        sl = dx * dx + dy * dy
        if sl <= 1e-8:
            return False

        t = ((waste.x - self.ax) * dx + (waste.y - self.ay) * dy) / sl
        t = _clamp(t, 0.0, 1.0)
        cx = self.ax + t * dx
        cy = self.ay + t * dy

        rx = waste.x - cx
        ry = waste.y - cy
        dist = math.hypot(rx, ry)
        radius = waste.radius + self.thickness
        if dist >= radius:
            return False

        if dist < 1e-6:
            # Fallback normal from segment direction
            nlen = math.hypot(-dy, dx)
            nx = (-dy / nlen) if nlen else 1.0
            ny = (dx / nlen) if nlen else 0.0
        else:
            nx = rx / dist
            ny = ry / dist

        # Separate
        overlap = radius - dist
        waste.x += nx * overlap
        waste.y += ny * overlap

        # Bounce with small tangential damping (reduces "chaos")
        rvx, rvy = _reflect(waste.vx, waste.vy, nx, ny, self.restitution)
        # Damp the component along the segment direction a bit
        tx, ty = (dx, dy)
        tlen = math.hypot(tx, ty)
        if tlen > 1e-6:
            tx /= tlen
            ty /= tlen
            tang = rvx * tx + rvy * ty
            rvx -= tang * (1.0 - self.tangential_damping) * tx
            rvy -= tang * (1.0 - self.tangential_damping) * ty

        if self.kick:
            rvx += nx * self.kick
            rvy += ny * self.kick

        waste.vx, waste.vy = rvx, rvy
        return True

    def draw(self, surf: pygame.Surface, ox: int = 0, oy: int = 0):
        a = (int(self.ax + ox), int(self.ay + oy))
        b = (int(self.bx + ox), int(self.by + oy))
        pygame.draw.line(surf, (0, 0, 0), (a[0] + 3, a[1] + 4), (b[0] + 3, b[1] + 4), self.thickness * 2 + 6)
        pygame.draw.line(surf, self.border, a, b, self.thickness * 2 + 4)
        pygame.draw.line(surf, self.color, a, b, self.thickness * 2)


class CircleBumper:
    """Static circular bumper with stable restitution (no speed runaway)."""

    def __init__(
        self,
        x: float,
        y: float,
        r: int = 18,
        color: tuple[int, int, int] = (255, 230, 120),
        border: tuple[int, int, int] = (190, 120, 40),
        restitution: float = 0.92,
        kick: float = 40.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.r = int(r)
        self.color = color
        self.border = border
        self.restitution = float(restitution)
        self.kick = float(kick)

    def collide(self, waste) -> bool:
        dx = waste.x - self.x
        dy = waste.y - self.y
        dist = math.hypot(dx, dy)
        rr = self.r + waste.radius
        if dist >= rr:
            return False

        if dist < 1e-6:
            nx, ny = 1.0, 0.0
        else:
            nx, ny = dx / dist, dy / dist

        overlap = rr - dist
        waste.x += nx * overlap
        waste.y += ny * overlap

        rvx, rvy = _reflect(waste.vx, waste.vy, nx, ny, self.restitution)
        rvx += nx * self.kick
        rvy += ny * self.kick
        waste.vx, waste.vy = rvx, rvy
        return True

    def draw(self, surf: pygame.Surface, ox: int = 0, oy: int = 0):
        cx = int(self.x + ox)
        cy = int(self.y + oy)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 3, cy + 4), self.r + 6)
        pygame.draw.circle(surf, self.border, (cx, cy), self.r + 2)
        pygame.draw.circle(surf, self.color, (cx, cy), self.r)
        pygame.draw.circle(surf, (255, 255, 255), (cx - self.r // 3, cy - self.r // 3), max(3, self.r // 4))


def build_side_obstacles(screen_w: int, header_h: int, screen_h: int):
    """
    Strategic mid-table side guards + bumpers to stop straight falls.
    Layout scales from the original 680×580 reference table.
    """
    sx = screen_w / 680.0
    sy = screen_h / 580.0
    mid_y = header_h + int(235 * sy)
    left_x = int(34 * sx)
    right_x = screen_w - left_x
    th = max(6, int(8 * (sx + sy) / 2))
    kick = 8.0 * (sx + sy) / 2

    # Increase spacing between the side obstacle pairs so the ball has more room.
    guards = [
        SegmentObstacle(left_x, mid_y - int(85 * sy), left_x + int(60 * sx), mid_y - int(10 * sy),
                        thickness=th, restitution=0.9, tangential_damping=0.985, kick=kick),
        SegmentObstacle(left_x + int(20 * sx), mid_y + int(35 * sy), left_x + int(85 * sx), mid_y + int(110 * sy),
                        thickness=th, restitution=0.9, tangential_damping=0.985, kick=kick),
        SegmentObstacle(right_x, mid_y - int(85 * sy), right_x - int(60 * sx), mid_y - int(10 * sy),
                        thickness=th, restitution=0.9, tangential_damping=0.985, kick=kick),
        SegmentObstacle(right_x - int(20 * sx), mid_y + int(35 * sy), right_x - int(85 * sx), mid_y + int(110 * sy),
                        thickness=th, restitution=0.9, tangential_damping=0.985, kick=kick),
    ]

    rb = max(12, int(16 * (sx + sy) / 2))
    bk = 35.0 * (sx + sy) / 2
    bumpers = [
        CircleBumper(left_x + int(40 * sx), mid_y + int(10 * sy), r=rb, restitution=0.92, kick=bk),
        CircleBumper(right_x - int(40 * sx), mid_y + int(10 * sy), r=rb, restitution=0.92, kick=bk),
    ]
    return guards, bumpers

