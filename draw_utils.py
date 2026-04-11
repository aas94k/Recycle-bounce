"""
draw_utils.py — Recycle Bounce v3  (Polished Mobile-Style UI)
"""
import pygame
import math
import random

# ─────────────────────────────────────────────────────────────────────────────
# BASE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def rounded_rect(surf, color, rect, radius=14, alpha=255, border=0, border_color=None):
    """Rounded rect with optional per-pixel alpha and border."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    shape = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shape, (*color[:3], alpha), (0, 0, w, h), border_radius=radius)
    if border and border_color:
        pygame.draw.rect(shape, (*border_color[:3], 255), (0, 0, w, h),
                         width=border, border_radius=radius)
    surf.blit(shape, (x, y))


def draw_outlined_text(surf, text, font, color, cx, y,
                       outline_col=(0, 0, 0), outline_w=2, shadow=True):
    """Text with pixel-perfect outline (8-dir) + drop shadow."""
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        sh.set_alpha(90)
        surf.blit(sh, (cx - sh.get_width() // 2 + 3, y + 4))
    outline_surf = font.render(text, True, outline_col)
    for dx, dy in [(-outline_w, 0), (outline_w, 0), (0, -outline_w), (0, outline_w),
                   (-outline_w, -outline_w), (outline_w, -outline_w),
                   (-outline_w,  outline_w), (outline_w,  outline_w)]:
        surf.blit(outline_surf, (cx - outline_surf.get_width() // 2 + dx, y + dy))
    t = font.render(text, True, color)
    surf.blit(t, (cx - t.get_width() // 2, y))


def draw_text_centered(surf, text, font, color, cx, y, shadow=True):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surf.blit(sh, (cx - sh.get_width() // 2 + 2, y + 2))
    t = font.render(text, True, color)
    surf.blit(t, (cx - t.get_width() // 2, y))


def draw_multiline_centered(surf, text, font, color, cx, y, line_h=24, shadow=True):
    for line in text.split("\n"):
        draw_text_centered(surf, line, font, color, cx, y, shadow=shadow)
        y += line_h
    return y


def draw_polished_button(surf, rect, color, hovered=False, radius=None,
                         label=None, font=None, text_col=(255, 255, 255)):
    """3-D cartoon button: shadow, 3-D base, shine stripe, hover glow."""
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    if radius is None:
        radius = min(h // 2, 32)

    light  = tuple(min(255, c + 55) for c in color)
    darker = tuple(max(0,   c - 65) for c in color)

    # Hover outer glow
    if hovered:
        glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color[:3], 55), (0, 0, w + 20, h + 20),
                         border_radius=radius + 6)
        surf.blit(glow, (x - 10, y - 10))

    # Drop shadow
    sh = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 90), (0, 0, w + 10, h + 10), border_radius=radius + 2)
    surf.blit(sh, (x + 2, y + 7))

    # 3-D base (darker bottom)
    pygame.draw.rect(surf, darker, (x, y + 5, w, h), border_radius=radius)
    # Main face
    face_col = light if hovered else color
    pygame.draw.rect(surf, face_col, (x, y, w, h - 4), border_radius=radius)

    # Shine stripe
    shine_h = max(5, h // 4)
    shine = pygame.Surface((w - 10, shine_h), pygame.SRCALPHA)
    shine_alpha = 65 if hovered else 45
    pygame.draw.rect(shine, (255, 255, 255, shine_alpha), (0, 0, w - 10, shine_h),
                     border_radius=radius)
    surf.blit(shine, (x + 5, y + 4))

    # Label with inner shadow
    if label and font:
        ts = font.render(label, True, darker)
        surf.blit(ts, (rect.centerx - ts.get_width() // 2 + 1,
                       rect.centery - ts.get_height() // 2 + 2))
        t = font.render(label, True, text_col)
        surf.blit(t, (rect.centerx - t.get_width() // 2,
                      rect.centery - t.get_height() // 2))


def draw_glass_panel(surf, rect, fill_col=(20, 60, 20), alpha=190,
                     radius=20, border_col=None, border_w=2):
    """Semi-transparent rounded panel with a thin inner highlight."""
    x, y, w, h = rect
    # Main fill
    rounded_rect(surf, fill_col, rect, radius=radius, alpha=alpha)
    # Inner top highlight (glass sheen)
    shine_h = max(4, h // 8)
    shine = pygame.Surface((w - 8, shine_h), pygame.SRCALPHA)
    pygame.draw.rect(shine, (255, 255, 255, 28), (0, 0, w - 8, shine_h),
                     border_radius=radius)
    surf.blit(shine, (x + 4, y + 3))
    # Border
    if border_col:
        rounded_rect(surf, border_col, rect, radius=radius, alpha=0,
                     border=border_w, border_color=border_col)


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND
# ─────────────────────────────────────────────────────────────────────────────

def draw_nature_background(surf, header_h, screen_w, screen_h):
    """Layered nature background: sky gradient, clouds, rolling hills, river."""
    ux = screen_w / 680.0
    uy = screen_h / 580.0
    play_h = screen_h - header_h - int(40 * uy)

    # Sky gradient: bright teal-green at top → deeper green at bottom
    for row in range(play_h):
        ratio = row / play_h
        r = int(105 + (32  - 105) * ratio)
        g = int(205 + (112 - 205) * ratio)
        b = int( 78 + ( 38 -  78) * ratio)
        pygame.draw.line(surf, (r, g, b),
                         (0, header_h + row), (screen_w, header_h + row))

    # Clouds (static; bg is pre-rendered once)
    _draw_clouds(surf, header_h, screen_w, ux, uy)

    # Far rolling hills
    hill1 = [(0, screen_h)]
    step1 = max(20, int(55 * ux))
    for i in range(0, screen_w + step1, step1):
        hy = header_h + int(play_h * 0.36) + int(math.sin(i * 0.017) * 32 * uy)
        hill1.append((i, hy))
    hill1.append((screen_w, screen_h))
    pygame.draw.polygon(surf, (52, 145, 52), hill1)

    # Mid hills
    hill2 = [(0, screen_h)]
    step2 = max(16, int(38 * ux))
    for i in range(0, screen_w + step2, step2):
        hy = header_h + int(play_h * 0.59) + int(math.sin(i * 0.021 + 1.2) * 22 * uy)
        hill2.append((i, hy))
    hill2.append((screen_w, screen_h))
    pygame.draw.polygon(surf, (36, 105, 36), hill2)

    # River (sinuous, with highlight)
    river_pts = []
    step_r = max(4, int(6 * uy))
    for i in range(header_h + int(22 * uy), screen_h - int(52 * uy), step_r):
        ratio = (i - header_h) / max(1, screen_h - header_h)
        rx = screen_w // 2 + int(math.sin(ratio * 6.4 + 0.5) * 60 * ux)
        river_pts.append((rx, i))
    if len(river_pts) > 1:
        lw = max(10, int(18 * uy))
        pygame.draw.lines(surf, (58, 158, 210), False, river_pts, lw)
        pygame.draw.lines(surf, (195, 232, 255), False, river_pts, max(2, lw // 5))

    # Decorative trees (left and right sides)
    _draw_tree(surf, int(42 * ux),  header_h + int(78 * uy),  int(52 * uy), (22, 108, 22), (52, 172, 52))
    _draw_tree(surf, int(618 * ux), header_h + int(92 * uy),  int(46 * uy), (22, 108, 22), (52, 172, 52))
    _draw_tree(surf, int(88 * ux),  header_h + int(238 * uy), int(38 * uy), (18,  88, 18), (44, 142, 44))
    _draw_tree(surf, int(592 * ux), header_h + int(258 * uy), int(36 * uy), (18,  88, 18), (44, 142, 44))
    _draw_tree(surf, int(162 * ux), header_h + int(132 * uy), int(42 * uy), (20,  98, 20), (48, 155, 48))
    _draw_tree(surf, int(518 * ux), header_h + int(148 * uy), int(40 * uy), (20,  98, 20), (48, 155, 48))

    # Small ground flowers
    small_flowers = [
        (int( 80 * ux), screen_h - int(62 * uy)),
        (int(240 * ux), screen_h - int(58 * uy)),
        (int(520 * ux), screen_h - int(60 * uy)),
    ]
    for fx, fy in small_flowers:
        _draw_small_flower(surf, fx, fy)


def _draw_clouds(surf, header_h, screen_w, ux, uy):
    """Soft, layered cloud shapes."""
    clouds = [
        (int( 80 * ux), header_h + int(28 * uy), int(42 * ux), int(18 * uy)),
        (int(282 * ux), header_h + int(16 * uy), int(58 * ux), int(24 * uy)),
        (int(462 * ux), header_h + int(25 * uy), int(46 * ux), int(17 * uy)),
        (int(618 * ux), header_h + int(20 * uy), int(40 * ux), int(15 * uy)),
    ]
    for cx, cy, cw, ch in clouds:
        # Each cloud is 3 overlapping circles blitted on a temp surface
        tw = cw * 2 + ch
        th = ch * 3
        cs = pygame.Surface((tw, th), pygame.SRCALPHA)
        for ox, oy, rs in [
            (cw // 2, ch + ch // 2, ch),
            (cw,      ch,           int(ch * 0.9)),
            (int(cw * 1.6), ch + ch // 3, int(ch * 0.7)),
        ]:
            pygame.draw.circle(cs, (255, 255, 255, 115), (ox, oy), rs)
        surf.blit(cs, (cx - cw // 2, cy - ch))


def _draw_tree(surf, cx, cy, r, _trunk_col, leaf_col):
    tw = max(4, int(r * 0.18))
    pygame.draw.rect(surf, (88, 50, 14), (cx - tw, cy, tw * 2, r // 2))
    shadow_col = tuple(max(0, c - 32) for c in leaf_col)
    pygame.draw.circle(surf, shadow_col, (cx + 2, cy - r // 2 + 3), int(r * 0.82))
    pygame.draw.circle(surf, leaf_col,   (cx, cy - r), r)
    light_col = tuple(min(255, c + 55) for c in leaf_col)
    pygame.draw.circle(surf, light_col,  (cx - r // 3, cy - r - r // 3), r // 2)


def _draw_small_flower(surf, cx, cy):
    colors = [(255, 200, 50), (200, 232, 255), (255, 158, 182), (195, 255, 160)]
    col = random.choice(colors)
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        px = cx + int(math.cos(rad) * 5)
        py = cy + int(math.sin(rad) * 5)
        pygame.draw.circle(surf, col, (px, py), 3)
    pygame.draw.circle(surf, (255, 242, 78), (cx, cy), 3)


# ─────────────────────────────────────────────────────────────────────────────
# FLOWER BUMPERS
# ─────────────────────────────────────────────────────────────────────────────

def draw_flower_bumper(surf, cx, cy, r, petal_color, frame=0):
    """Animated flower bumper: outer glow ring, petals, shiny centre, face."""
    n_petals = 5
    petal_r  = max(4, r // 3)

    # Outer ambient glow
    glow_r = r + petal_r + 6
    gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(gs, (*petal_color[:3], 38), (glow_r, glow_r), glow_r)
    surf.blit(gs, (cx - glow_r, cy - glow_r))

    # Drop shadow
    sh_r = r + petal_r + 2
    sh = pygame.Surface((sh_r * 2 + 8, sh_r * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(sh, (0, 0, 0, 52), (sh_r + 4, sh_r + 6), sh_r)
    surf.blit(sh, (cx - sh_r, cy - sh_r))

    # Petals (rotate slowly with frame)
    for i in range(n_petals):
        angle = math.radians(i * (360 / n_petals) + frame * 0.35)
        px = cx + int(math.cos(angle) * (r - 2))
        py = cy + int(math.sin(angle) * (r - 2))
        pygame.draw.circle(surf, petal_color, (px, py), petal_r)
        lighter = tuple(min(255, c + 72) for c in petal_color)
        pygame.draw.circle(surf, lighter, (px - 1, py - 1), max(2, petal_r // 3))

    # Yellow centre
    pygame.draw.circle(surf, (255, 222, 38), (cx, cy), r // 2 + 3)
    pygame.draw.circle(surf, (255, 195, 18), (cx, cy), r // 2)
    pygame.draw.circle(surf, (255, 242, 120), (cx - r // 8, cy - r // 8), max(2, r // 6))

    # Cute face
    eye_off = max(3, r // 6)
    eye_r   = max(2, r // 10)
    pygame.draw.circle(surf, (68, 38, 0), (cx - eye_off, cy - eye_off // 2), eye_r)
    pygame.draw.circle(surf, (68, 38, 0), (cx + eye_off, cy - eye_off // 2), eye_r)
    pygame.draw.circle(surf, (255, 255, 255),
                       (cx - eye_off - 1, cy - eye_off // 2 - 1), max(1, eye_r // 2))
    pygame.draw.circle(surf, (255, 255, 255),
                       (cx + eye_off - 1, cy - eye_off // 2 - 1), max(1, eye_r // 2))
    smile_r = max(3, r // 4)
    smile_rect = pygame.Rect(cx - smile_r, cy - smile_r // 2, smile_r * 2, smile_r)
    pygame.draw.arc(surf, (68, 38, 0), smile_rect, math.pi, 2 * math.pi, max(2, eye_r))


# ─────────────────────────────────────────────────────────────────────────────
# BINS
# ─────────────────────────────────────────────────────────────────────────────

def draw_bin(surf, label, color, icon_char, x, y, w, h,
             flashing=False, font=None, font_sm=None):
    """Modern polished recycling bin — tapered body, card label, no face."""
    col   = (255, 240, 80) if flashing else color
    dark  = tuple(max(0,   c - 65) for c in col)
    mid   = tuple(max(0,   c - 28) for c in col)
    light = tuple(min(255, c + 80) for c in col)
    r     = max(10, w // 9)

    # ── Flash glow ────────────────────────────────────────────────────────
    if flashing:
        glow = pygame.Surface((w + 36, h + 36), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 242, 80, 115), (0, 0, w + 36, h + 36),
                         border_radius=r + 14)
        surf.blit(glow, (x - 18, y - 18))

    # ── Soft drop shadow ──────────────────────────────────────────────────
    for off, alpha in ((10, 20), (7, 36), (4, 58)):
        sh = pygame.Surface((w + off * 2, h + off * 2), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, alpha), (0, 0, w + off * 2, h + off * 2),
                         border_radius=r + 5)
        surf.blit(sh, (x - off + 5, y + 4))

    # ── Tapered body (slightly wider at top) via polygon ─────────────────
    taper = max(3, w // 20)
    body = [
        (x,              y),
        (x + w,          y),
        (x + w - taper,  y + h),
        (x + taper,      y + h),
    ]
    # Dark border/3D side face
    pygame.draw.polygon(surf, dark, body)
    # Inner main fill (1px inset)
    inner = [
        (x + 2,              y + 2),
        (x + w - 2,          y + 2),
        (x + w - taper,      y + h - 2),
        (x + taper,          y + h - 2),
    ]
    pygame.draw.polygon(surf, col, inner)

    # ── Gloss highlight (left strip) ──────────────────────────────────────
    gloss_w = max(6, w // 13)
    gloss_h = max(10, h - 10)
    gloss = pygame.Surface((gloss_w, gloss_h), pygame.SRCALPHA)
    pygame.draw.rect(gloss, (*light, 115), (0, 0, gloss_w, gloss_h), border_radius=3)
    surf.blit(gloss, (x + 6, y + 5))

    # ── Bottom rim (3D base edge) ─────────────────────────────────────────
    rim_h = max(4, h // 12)
    rim = [
        (x + taper,          y + h - rim_h),
        (x + w - taper,      y + h - rim_h),
        (x + w - taper,      y + h),
        (x + taper,          y + h),
    ]
    pygame.draw.polygon(surf, dark, rim)

    # ── Lid ───────────────────────────────────────────────────────────────
    lid_h   = max(12, h // 7)
    lid_ext = max(6, w // 14)
    lx, lw  = x - lid_ext, w + lid_ext * 2

    # Lid drop shadow
    ls = pygame.Surface((lw + 6, lid_h + 8), pygame.SRCALPHA)
    pygame.draw.rect(ls, (0, 0, 0, 55), (0, 0, lw + 6, lid_h + 8),
                     border_radius=r // 2 + 3)
    surf.blit(ls, (lx - 3, y - lid_h + 4))

    # Lid body (dark outline + colored fill)
    pygame.draw.rect(surf, dark, (lx - 2, y - lid_h - 2, lw + 4, lid_h + 4),
                     border_radius=r // 2 + 2)
    pygame.draw.rect(surf, mid,  (lx,     y - lid_h,     lw,     lid_h),
                     border_radius=r // 2)
    # Lid top sheen
    pygame.draw.rect(surf, light,
                     (lx + 5, y - lid_h + 3, max(10, lw // 3), max(3, lid_h // 3)),
                     border_radius=2)

    # Handle (rounded tab)
    hnd_w = max(20, w // 5)
    hnd_h = max(7,  lid_h // 2)
    hnd_x = x + w // 2 - hnd_w // 2
    hnd_y = y - lid_h - hnd_h
    pygame.draw.rect(surf, dark, (hnd_x - 2, hnd_y - 2, hnd_w + 4, hnd_h + 2),
                     border_radius=hnd_h // 2 + 2)
    pygame.draw.rect(surf, mid,  (hnd_x,     hnd_y,     hnd_w,     hnd_h),
                     border_radius=hnd_h // 2)

    # ── Label card ────────────────────────────────────────────────────────
    pad    = max(4, w // 18)
    card_x = x + pad + 2
    card_y = y + pad
    card_w = w - pad * 2 - 4
    card_h = h - pad * 2
    card_r = max(5, r // 3)

    # Card shadow
    pygame.draw.rect(surf, dark, (card_x + 2, card_y + 2, card_w, card_h),
                     border_radius=card_r)
    # Card white background
    pygame.draw.rect(surf, (255, 255, 255), (card_x, card_y, card_w, card_h),
                     border_radius=card_r)

    # Colored top strip on card
    strip_h = max(8, card_h // 3)
    pygame.draw.rect(surf, col, (card_x, card_y, card_w, strip_h),
                     border_radius=card_r)
    # Flatten bottom edge of the strip
    if strip_h < card_h:
        pygame.draw.rect(surf, col,
                         (card_x, card_y + card_r, card_w, strip_h - card_r))

    # Card border
    pygame.draw.rect(surf, dark, (card_x, card_y, card_w, card_h), 2,
                     border_radius=card_r)

    # ── Icon in the colored strip ─────────────────────────────────────────
    icon_font = font_sm if font_sm else font
    if icon_font:
        try:
            icon_surf = icon_font.render(icon_char, True, (255, 255, 255))
            ix = card_x + card_w // 2 - icon_surf.get_width() // 2
            iy = card_y + strip_h // 2 - icon_surf.get_height() // 2
            surf.blit(icon_surf, (ix, iy))
        except Exception:
            pass

    # ── Label text ────────────────────────────────────────────────────────
    if font_sm:
        lines = label.split("\n")
        text_top  = card_y + strip_h + 2
        text_area = card_h - strip_h - 4
        lh        = font_sm.get_height()
        total_h   = len(lines) * lh
        start_y   = text_top + max(0, (text_area - total_h) // 2)
        for i, line in enumerate(lines):
            draw_outlined_text(surf, line, font_sm, dark,
                               card_x + card_w // 2, start_y + i * lh,
                               outline_col=(255, 255, 255), outline_w=1, shadow=False)

    # ── Outer polygon border ──────────────────────────────────────────────
    pygame.draw.polygon(surf, dark, body, 2)
