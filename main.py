from codecarbon import EmissionsTracker
import pygame, sys, math, random, warnings
from constants import *
from ball       import Waste
from flipper    import Flipper
from bin_target import BinTarget
from obstacles  import build_side_obstacles
from draw_utils import (rounded_rect, draw_outlined_text,
                        draw_multiline_centered, wrap_text, draw_polished_button,
                        draw_glass_panel, draw_nature_background, draw_flower_bumper)

warnings.filterwarnings("ignore", message=".*system font.*couldn't be found.*")

# ── Init ──────────────────────────────────────────────────────────────────────

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("🌍 Recycle Bounce – Le Flipper du Tri")
clock = pygame.time.Clock()

UI       = SCREEN_H / REF_H
LAUNCH_PAD_Y     = SCREEN_H - int(0.20 * SCREEN_H)
FLIP_OFF_X       = int(0.17 * SCREEN_W)
FLIP_PAD_Y       = SCREEN_H - int(0.18 * SCREEN_H)
HEADER_PLAY_CROP = int(22 * SCALE_X)

# ── Fonts ─────────────────────────────────────────────────────────────────────
def try_font(names, size, bold=False):
    for n in names:
        try:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)

FONT_TITLE  = try_font(["Fredoka One", "Arial Rounded MT Bold", "Comic Sans MS"],
                        int(54 * UI), bold=True)
FONT_BIG    = try_font(["Fredoka One", "Arial Rounded MT Bold", "Comic Sans MS"],
                        int(34 * UI), bold=True)
FONT_MED    = try_font(["Arial Rounded MT Bold", "Comic Sans MS", "Arial"],
                        int(22 * UI), bold=False)
FONT_SMALL  = try_font(["Arial", "Helvetica"],                  int(17 * UI))
FONT_ICON   = try_font(["Segoe UI Emoji", "Apple Color Emoji",
                         "Noto Color Emoji", "Arial"],           int(28 * UI))
FONT_ICON_SM = try_font(["Segoe UI Emoji", "Apple Color Emoji",
                          "Noto Color Emoji", "Arial"],          int(16 * UI))

# ── Bins ──────────────────────────────────────────────────────────────────────
BIN_SPACING = (SCREEN_W - 20) // 4
BINS = [
    BinTarget("Plastique\n& Métal", COLOR_BIN_YELLOW, "♻",  "plastic",
              BIN_SPACING * 0 + 10, HEADER_H - 2),
    BinTarget("Papier\n& Carton",   COLOR_BIN_BLUE,   "📄", "paper",
              BIN_SPACING * 1 + 10, HEADER_H - 2),
    BinTarget("Verre",              COLOR_BIN_GREEN,  "🍾", "glass",
              BIN_SPACING * 2 + 10, HEADER_H - 2),
    BinTarget("Bio-\nDéchets",      COLOR_BIN_BROWN,  "🍌", "bio",
              BIN_SPACING * 3 + 10, HEADER_H - 2),
]

waste_idx      = 0
next_waste_idx = random.randrange(len(WASTE_LIST))
MAX_ROUNDS     = 10

# ── Game objects ──────────────────────────────────────────────────────────────
waste          = Waste(SCREEN_W // 2, LAUNCH_PAD_Y, WASTE_LIST[waste_idx][1])
_preview_waste = Waste(0, 0, WASTE_LIST[next_waste_idx][1], max_dim=int(64 * UI))
left_flipper  = Flipper("left",  SCREEN_W // 2 - FLIP_OFF_X, FLIP_PAD_Y)
right_flipper = Flipper("right", SCREEN_W // 2 + FLIP_OFF_X, FLIP_PAD_Y)
side_guards, side_bumpers = build_side_obstacles(SCREEN_W, HEADER_H, SCREEN_H)

# ── State ─────────────────────────────────────────────────────────────────────
state          = "menu"
score          = 0
score_display  = 0.0    # smooth-animated score for display
score_flash    = 0      # frames to flash the score badge
combo          = 0
combo_timer    = 0
waste_launched = False
message        = ""
msg_timer      = 0
msg_good       = True
tip_idx        = 0
tip_counter    = 0
round_num      = 1
game_completed = False  # True if completed all 10 rounds
frame          = 0
particles      = []
nudge_cd       = 0
shake_frames   = 0
shake_strength = 0.0
paused         = False
menu_btn_rect  = None
pause_btn_rect = None
launch_btn_rect    = None
screen_flash_col   = (0, 220, 100)   # colour for next flash overlay
screen_flash_timer = 0               # frames remaining

# ── Pre-rendered surfaces ──────────────────────────────────────────────────────
bg_surf     = pygame.Surface((SCREEN_W, SCREEN_H))
header_surf = pygame.Surface((SCREEN_W, HEADER_H - HEADER_PLAY_CROP))
grass_surf  = pygame.Surface((SCREEN_W, int(44 * UI)))
tip_surf    = pygame.Surface((SCREEN_W, int(38 * UI)))

def build_bg():
    draw_nature_background(bg_surf, HEADER_H, SCREEN_W, SCREEN_H)

def build_header_surf():
    """Pre-render the header gradient so we only compute it once."""
    h = header_surf.get_height()
    for row in range(h):
        ratio = row / max(1, h)
        r = int(18 + (40 - 18) * ratio)
        g = int(62 + (105 - 62) * ratio)
        b = int(18 + (40 - 18) * ratio)
        pygame.draw.line(header_surf, (r, g, b), (0, row), (SCREEN_W, row))
    pygame.draw.line(header_surf, (58, 148, 58), (0, h - 1), (SCREEN_W, h - 1),
                     max(2, int(2 * UI)))

def build_grass_surf():
    """Pre-render the ground grass gradient strip."""
    h = grass_surf.get_height()
    for row in range(h):
        ratio = row / max(1, h)
        r = int(26 + (44 - 26) * ratio)
        g = int(88 + (115 - 88) * ratio)
        b = int(26 + (44 - 26) * ratio)
        pygame.draw.line(grass_surf, (r, g, b), (0, row), (SCREEN_W, row))
    pygame.draw.line(grass_surf, (55, 172, 55), (0, 0), (SCREEN_W, 0),
                     max(2, int(3 * UI)))

def build_tip_surf():
    """Pre-render the eco-tip bar gradient (call again when tip_idx changes)."""
    h = tip_surf.get_height()
    for row in range(h):
        ratio = row / max(1, h)
        r = int(14 + (28 - 14) * ratio)
        g = int(62 + (88 - 62) * ratio)
        b = int(14 + (28 - 14) * ratio)
        pygame.draw.line(tip_surf, (r, g, b), (0, row), (SCREEN_W, row))
    pygame.draw.line(tip_surf, (55, 155, 55), (0, 0), (SCREEN_W, 0),
                     max(2, int(2 * UI)))
    # Blit text onto tip_surf
    tip = ECO_TIPS[tip_idx]
    t = FONT_SMALL.render(tip, True, (175, 255, 175))
    tip_surf.blit(t, (SCREEN_W // 2 - t.get_width() // 2, int(9 * SCALE_Y)))

build_bg()
build_header_surf()
build_grass_surf()
build_tip_surf()

# ── Particles ─────────────────────────────────────────────────────────────────
def spawn_particles(x, y, color, n=18):
    for _ in range(n):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(70, 230)
        particles.append([
            x, y,
            math.cos(angle) * speed, math.sin(angle) * speed,
            random.randint(32, 65),
            color,
        ])

def update_particles(dt):
    for p in particles:
        p[0] += p[2] * dt
        p[1] += p[3] * dt
        p[3] += 200 * dt
        p[4] -= 1
    particles[:] = [p for p in particles if p[4] > 0]

def draw_particles(surf):
    for p in particles:
        alpha = min(255, p[4] * 4)
        r = max(2, p[4] // 8)
        ps = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*p[5][:3], alpha), (r, r), r)
        surf.blit(ps, (int(p[0]) - r, int(p[1]) - r))

def draw_particles_offset(surf, ox=0, oy=0):
    for p in particles:
        alpha = min(255, p[4] * 4)
        r = max(2, p[4] // 8)
        ps = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*p[5][:3], alpha), (r, r), r)
        surf.blit(ps, (int(p[0] + ox) - r, int(p[1] + oy) - r))

# ── Screen-shake ──────────────────────────────────────────────────────────────
def trigger_shake(strength=3.0, frames=10):
    global shake_frames, shake_strength
    shake_frames   = max(shake_frames,   int(frames))
    shake_strength = max(shake_strength, float(strength))

def get_shake_offset():
    global shake_frames, shake_strength
    if shake_frames <= 0:
        shake_strength = 0.0
        return 0, 0
    shake_frames -= 1
    mag = shake_strength * (shake_frames / max(1, shake_frames + 3))
    return int(random.uniform(-mag, mag)), int(random.uniform(-mag, mag))

# ── Reset ─────────────────────────────────────────────────────────────────────
def reset_game():
    global score, score_display, score_flash, combo, combo_timer
    global waste_launched, waste_idx, next_waste_idx, message, msg_timer, tip_idx, tip_counter, round_num, game_completed
    global screen_flash_timer
    waste_idx = random.randrange(len(WASTE_LIST))
    waste.reset(SCREEN_W // 2, LAUNCH_PAD_Y, waste_type=WASTE_LIST[waste_idx][1])
    next_waste_idx = random.randrange(len(WASTE_LIST))
    _preview_waste.reset(0, 0, waste_type=WASTE_LIST[next_waste_idx][1])
    left_flipper.reset()
    right_flipper.reset()
    score = 0; score_display = 0.0; score_flash = 0
    waste_launched = False
    combo = 0; combo_timer = 0
    message = ""; msg_timer = 0; tip_idx = 0; tip_counter = 0
    round_num = 1
    game_completed = False
    paused = False
    particles.clear()
    screen_flash_timer = 0


# ══════════════════════════════════════════════════════════════════════════════
# DRAW HELPERS — GAME HUD
# ══════════════════════════════════════════════════════════════════════════════

def draw_header():
    """Gradient header: title left, animated score badge right."""
    # Pre-rendered gradient
    screen.blit(header_surf, (0, 0))

    # Title
    draw_outlined_text(screen, "🌍 Recycle Bounce", FONT_BIG,
                       (255, 242, 80), int(12 * SCALE_X) + FONT_BIG.size("🌍 Recycle Bounce")[0] // 2,
                       int(8 * SCALE_Y), outline_col=(22, 72, 22), outline_w=2, shadow=False)

    # Round display
    round_txt = FONT_MED.render(f"Round {round_num}/{MAX_ROUNDS}", True, (200, 255, 200))
    screen.blit(round_txt, (int(12 * SCALE_X), int(38 * SCALE_Y)))

    # Score badge (pulses+scales when score_flash > 0)
    pulsing  = score_flash > 0
    bw_base  = int(148 * SCALE_X)
    bh_base  = int(44  * SCALE_Y)
    if pulsing:
        t     = score_flash / 45.0          # 1.0 = just scored, 0.0 = faded
        scale = 1.0 + 0.18 * t
        bw    = int(bw_base * scale)
        bh    = int(bh_base * scale)
    else:
        bw, bh = bw_base, bh_base
    bx = SCREEN_W - bw - int(8 * SCALE_X)  # pin to right edge, grow leftward
    by = int(8 * SCALE_Y) - (bh - bh_base) // 2
    badge_col = (255, 220, 20) if pulsing else (255, 185, 0)

    # Badge shadow
    sh = pygame.Surface((bw + 6, bh + 6), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 80), (0, 0, bw + 6, bh + 6), border_radius=int(22 * UI))
    screen.blit(sh, (bx + 2, by + 5))

    # Badge fill (3-D style)
    darker = tuple(max(0, c - 55) for c in badge_col)
    pygame.draw.rect(screen, darker, (bx, by + 3, bw, bh), border_radius=int(22 * UI))
    pygame.draw.rect(screen, badge_col, (bx, by, bw, bh - 3), border_radius=int(22 * UI))
    # Shine stripe
    shine_s = pygame.Surface((bw - 10, max(4, bh // 4)), pygame.SRCALPHA)
    pygame.draw.rect(shine_s, (255, 255, 255, 50), (0, 0, bw - 10, shine_s.get_height()),
                     border_radius=int(14 * UI))
    screen.blit(shine_s, (bx + 5, by + 3))

    # Score text
    disp = round(score_display)
    sc_txt = FONT_BIG.render(f"⭐ {disp}", True, (60, 30, 0))
    screen.blit(sc_txt, (bx + bw // 2 - sc_txt.get_width() // 2,
                         by + bh // 2 - sc_txt.get_height() // 2))


def draw_top_controls():
    """Top-right action buttons for menu and pause."""
    global menu_btn_rect, pause_btn_rect
    btn_w = int(48 * SCALE_X)
    btn_h = int(36 * SCALE_Y)
    pad   = int(10 * SCALE_X)
    y = int(10 * SCALE_Y)

    pause_btn_rect = pygame.Rect(SCREEN_W - btn_w - pad, y, btn_w, btn_h)
    menu_btn_rect  = pygame.Rect(SCREEN_W - btn_w * 2 - pad * 2, y, btn_w, btn_h)

    draw_polished_button(screen, menu_btn_rect, COLOR_BTN_BLUE,
                         hovered=menu_btn_rect.collidepoint(pygame.mouse.get_pos()),
                         radius=int(14 * UI), label="☰",
                         font=FONT_SMALL, text_col=COLOR_WHITE)
    draw_polished_button(screen, pause_btn_rect, COLOR_BTN_GREEN,
                         hovered=pause_btn_rect.collidepoint(pygame.mouse.get_pos()),
                         radius=int(14 * UI), label="⏸",
                         font=FONT_SMALL, text_col=COLOR_WHITE)
    return menu_btn_rect, pause_btn_rect


def draw_launch_button():
    """Bottom launch button anchored to the lower 10% of the screen."""
    global launch_btn_rect
    btn_w = int(170 * SCALE_X)
    btn_h = int(44 * SCALE_Y)
    x = SCREEN_W // 2 - btn_w // 2
    y = SCREEN_H - int(0.10 * SCREEN_H) - btn_h // 2
    launch_btn_rect = pygame.Rect(x, y, btn_w, btn_h)
    label = "▶ Lancer" if not waste_launched else "⏳ Envolé"
    draw_polished_button(screen, launch_btn_rect, COLOR_BTN_GREEN if not waste_launched else COLOR_BTN_GREEN_D,
                         hovered=launch_btn_rect.collidepoint(pygame.mouse.get_pos()) and not waste_launched,
                         radius=int(18 * UI), label=label,
                         font=FONT_MED, text_col=COLOR_WHITE)
    return launch_btn_rect


def draw_pause_overlay():
    panel = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 150))
    screen.blit(panel, (0, 0))
    draw_outlined_text(screen, "PAUSE", FONT_TITLE, COLOR_WHITE,
                       SCREEN_W // 2, SCREEN_H // 2 - int(26 * SCALE_Y),
                       outline_col=(0, 0, 0), outline_w=4, shadow=False)
    hint = FONT_SMALL.render("Appuyez sur P pour reprendre", True, COLOR_WHITE)
    screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                       SCREEN_H // 2 + int(16 * SCALE_Y)))


def draw_waste_card():
    """Bottom-left card: shows the waste item to be sorted."""
    cw = int(172 * SCALE_X)
    ch = int(104 * SCALE_Y)
    cx = int(8 * SCALE_X)
    cy = SCREEN_H - tip_surf.get_height() - ch - int(6 * SCALE_Y)
    card_r = int(16 * UI)

    # Outer glow
    glow = pygame.Surface((cw + 16, ch + 16), pygame.SRCALPHA)
    pygame.draw.rect(glow, (80, 220, 80, 42), (0, 0, cw + 16, ch + 16),
                     border_radius=card_r + 4)
    screen.blit(glow, (cx - 8, cy - 8))

    # Card shadow
    sh = pygame.Surface((cw + 8, ch + 8), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 70), (0, 0, cw + 8, ch + 8), border_radius=card_r)
    screen.blit(sh, (cx + 3, cy + 5))

    # Card body
    draw_glass_panel(screen, (cx, cy, cw, ch),
                     fill_col=(245, 252, 245), alpha=238,
                     radius=card_r, border_col=(50, 168, 50), border_w=max(2, int(2 * UI)))

    name, _, col = WASTE_LIST[waste_idx]

    # Colour badge at top
    bh_badge = int(26 * UI)
    rounded_rect(screen, col,
                 (cx + int(6 * SCALE_X), cy + int(6 * SCALE_Y),
                  cw - int(12 * SCALE_X), bh_badge),
                 radius=int(11 * UI))
    cat_txt = FONT_SMALL.render("À TRIER :", True, (255, 255, 255))
    screen.blit(cat_txt, (cx + cw // 2 - cat_txt.get_width() // 2,
                           cy + int(9 * SCALE_Y)))

    # Waste name
    line_gap = int(22 * UI)
    y0 = cy + int(38 * SCALE_Y)
    for i, line in enumerate(name.split("\n")):
        t = FONT_MED.render(line, True, COLOR_DARK_TEXT)
        screen.blit(t, (cx + cw // 2 - t.get_width() // 2, y0 + i * line_gap))


def draw_next_waste_panel():
    """Bottom-right panel: next waste preview + round progress bar.

    Visual layout (top-down cursor, progress section pinned to bottom):
      ┌─────────────────────┐
      │  [ SUIVANT  ▶ ]     │  ← coloured badge header
      │        🖼            │  ← sprite, scaled to fit its zone
      │    Nom du déchet    │  ← waste name, auto-wrapped to card width
      │  · · · · · · · · ·  │  ← thin separator
      │    Manche X / Y     │  ← progress label   (bottom-pinned)
      │  [======--------]   │  ← progress bar     (bottom-pinned)
      └─────────────────────┘
    """
    PAD_H = int(10 * SCALE_X)   # left/right inner margin
    PAD_V = int(5  * SCALE_Y)   # vertical gap between sections

    cw    = int(160 * SCALE_X)
    ch    = int(135 * SCALE_Y)  # taller card → enough room for all sections
    cx    = SCREEN_W - cw - int(8 * SCALE_X)
    cy    = SCREEN_H - tip_surf.get_height() - ch - int(6 * SCALE_Y)
    card_r = int(16 * UI)

    next_name, _, next_col = WASTE_LIST[next_waste_idx]
    dark_col  = tuple(max(0, c - 60) for c in next_col)
    sep_col   = tuple(min(255, c + 50) for c in dark_col)  # muted line colour

    # ── Outer category-colour glow ────────────────────────────────────────
    glow = pygame.Surface((cw + 16, ch + 16), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*next_col, 48), (0, 0, cw + 16, ch + 16),
                     border_radius=card_r + 4)
    screen.blit(glow, (cx - 8, cy - 8))

    # ── Soft drop shadow ──────────────────────────────────────────────────
    sh = pygame.Surface((cw + 8, ch + 8), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 70), (0, 0, cw + 8, ch + 8),
                     border_radius=card_r)
    screen.blit(sh, (cx + 3, cy + 5))

    # ── Card body ─────────────────────────────────────────────────────────
    draw_glass_panel(screen, (cx, cy, cw, ch),
                     fill_col=(240, 250, 240), alpha=242,
                     radius=card_r, border_col=next_col,
                     border_w=max(2, int(2 * UI)))

    # ── Pre-compute section heights ───────────────────────────────────────
    badge_h = int(20 * UI)              # header badge
    bar_h   = int(10 * UI)              # progress bar
    lh      = FONT_SMALL.get_height()   # single text-line height

    # Wrap name to card content width so no line ever overflows
    content_w  = cw - PAD_H * 2
    name_lines = wrap_text(next_name, FONT_SMALL, content_w)
    name_blk_h = len(name_lines) * lh

    # Space locked at top:    top-pad + badge + gap
    top_rsv    = PAD_V + badge_h + PAD_V
    # Space locked at bottom: sep + gap + label + gap + bar + bottom-pad
    bottom_rsv = int(2 * SCALE_Y) + PAD_V + lh + int(3 * SCALE_Y) + bar_h + PAD_V
    # Remaining middle is shared between sprite zone + gap + name block
    middle_h   = ch - top_rsv - bottom_rsv
    sprite_zone = max(int(28 * SCALE_Y), middle_h - PAD_V - name_blk_h)

    # ── 1. Header badge ───────────────────────────────────────────────────
    badge_y = cy + PAD_V
    rounded_rect(screen, next_col,
                 (cx + PAD_H, badge_y, content_w, badge_h),
                 radius=int(9 * UI))
    lbl = FONT_SMALL.render("SUIVANT  ▶", True, (255, 255, 255))
    screen.blit(lbl, (cx + cw // 2 - lbl.get_width() // 2,
                      badge_y + badge_h // 2 - lbl.get_height() // 2))

    # ── 2. Sprite (scaled to fit its zone, centred) ───────────────────────
    sprite_y    = badge_y + badge_h + PAD_V
    preview_img = _preview_waste._base_image
    max_px      = min(content_w, sprite_zone)
    pw, ph      = preview_img.get_width(), preview_img.get_height()
    scale       = min(max_px / max(pw, ph, 1), 1.0)
    if scale < 0.99:
        preview_img = pygame.transform.smoothscale(
            preview_img, (max(1, int(pw * scale)), max(1, int(ph * scale))))
    screen.blit(preview_img,
                (cx + cw // 2 - preview_img.get_width()  // 2,
                 sprite_y + sprite_zone // 2 - preview_img.get_height() // 2))

    # ── 3. Waste name (auto-wrapped, horizontally centred) ────────────────
    name_y = sprite_y + sprite_zone
    for i, line in enumerate(name_lines):
        t = FONT_SMALL.render(line, True, dark_col)
        screen.blit(t, (cx + cw // 2 - t.get_width() // 2,
                        name_y + i * lh))

    # ── 4. Separator line ─────────────────────────────────────────────────
    sep_y = cy + ch - bottom_rsv + int(2 * SCALE_Y)
    pygame.draw.line(screen, sep_col,
                     (cx + PAD_H, sep_y), (cx + cw - PAD_H, sep_y), 1)

    # ── 5. Progress label + bar (pinned to card bottom) ───────────────────
    bar_y  = cy + ch - PAD_V - bar_h
    prog_y = bar_y - int(3 * SCALE_Y) - lh
    bar_w  = content_w

    # "Manche X / Y"  — larger, bolder look via outlined helper
    draw_outlined_text(screen, f"Manche  {round_num} / {MAX_ROUNDS}",
                       FONT_SMALL, (255, 255, 255),
                       cx + cw // 2, prog_y,
                       outline_col=dark_col, outline_w=1, shadow=False)

    # Track (background)
    pygame.draw.rect(screen, (180, 220, 180),
                     (cx + PAD_H, bar_y, bar_w, bar_h),
                     border_radius=bar_h // 2)
    # Fill (rounds completed so far)
    filled = int(bar_w * min(round_num - 1, MAX_ROUNDS) / MAX_ROUNDS)
    if filled > 0:
        pygame.draw.rect(screen, next_col,
                         (cx + PAD_H, bar_y, filled, bar_h),
                         border_radius=bar_h // 2)
    # Border
    pygame.draw.rect(screen, dark_col,
                     (cx + PAD_H, bar_y, bar_w, bar_h),
                     max(1, bar_h // 5), border_radius=bar_h // 2)


def draw_tip_bar():
    """Bottom eco-tip bar — blit pre-rendered surface."""
    screen.blit(tip_surf, (0, SCREEN_H - tip_surf.get_height()))


def draw_controls_hint():
    """Key-badge style control hint shown before launch."""
    if waste_launched:
        return
    h = FONT_SMALL.render(
        "← Flipper gauche  |  ESPACE Lancer  |  Flipper droit →",
        True, (215, 255, 215))
    pad_x = int(16 * SCALE_X)
    pad_y = int(8 * SCALE_Y)
    hw = h.get_width() + pad_x * 2
    hh = h.get_height() + pad_y * 2
    hx = SCREEN_W // 2 - hw // 2
    hy = SCREEN_H - int(0.30 * SCREEN_H) - hh
    draw_glass_panel(screen, (hx, hy, hw, hh),
                     fill_col=(0, 0, 0), alpha=115, radius=int(16 * UI))
    screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, hy + pad_y))


def draw_screen_flash():
    """Full-screen color flash overlay: green for correct bin, red for wrong."""
    if screen_flash_timer <= 0:
        return
    fa = min(90, screen_flash_timer * 5)
    fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    fl.fill((*screen_flash_col, fa))
    screen.blit(fl, (0, 0))


def draw_feedback():
    """Animated feedback banner with fade and scale effect."""
    if msg_timer <= 0:
        return
    # Fade alpha
    alpha  = min(255, msg_timer * 6)
    bg_a   = min(210, msg_timer * 5)
    fw     = int(460 * SCALE_X)
    fh     = int(72 * SCALE_Y)
    fx     = SCREEN_W // 2 - fw // 2
    fy     = SCREEN_H // 2 - fh // 2

    # Panel
    panel  = pygame.Surface((fw, fh), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, bg_a), (0, 0, fw, fh), border_radius=int(24 * UI))
    # Colour accent stripe on left
    accent = (72, 220, 72) if msg_good else (240, 88, 72)
    pygame.draw.rect(panel, (*accent, bg_a),
                     (0, 0, max(6, int(8 * SCALE_X)), fh),
                     border_radius=int(24 * UI))
    screen.blit(panel, (fx, fy))

    # Message text
    col = (88, 228, 88) if msg_good else (248, 108, 88)
    msg_surf = FONT_BIG.render(message, True, col)
    msg_surf.set_alpha(alpha)
    screen.blit(msg_surf, (SCREEN_W // 2 - msg_surf.get_width() // 2,
                            SCREEN_H // 2 - msg_surf.get_height() // 2))


# ══════════════════════════════════════════════════════════════════════════════
# MENU SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def draw_menu():
    screen.blit(bg_surf, (0, 0))

    # Dark green overlay
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 28, 0, 95))
    screen.blit(ov, (0, 0))

    # Floating eco-sparkles (animated)
    for i in range(18):
        t_off = (frame * 0.012 + i * 0.62)
        px = int((i * 141 + math.sin(t_off) * 95) % SCREEN_W)
        py = int(SCREEN_H - (frame * 0.4 + i * 78) % (SCREEN_H + 60))
        sz = max(3, 5 + int(3 * math.sin(t_off * 1.5)))
        al = int(80 + 70 * abs(math.sin(t_off * 2)))
        dot = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (105, 230, 105, al), (sz, sz), sz)
        screen.blit(dot, (px - sz, py - sz))

    # ── Title card ────────────────────────────────────────────────────────────
    card_y  = int(48 * UI)
    mx_pad  = int(72 * SCALE_X)
    card_w  = SCREEN_W - 2 * mx_pad
    card_h  = int(102 * UI)
    draw_glass_panel(screen, (mx_pad, card_y, card_w, card_h),
                     fill_col=(18, 75, 18), alpha=215,
                     radius=int(26 * UI), border_col=(85, 208, 85), border_w=max(2, int(3 * UI)))

    draw_outlined_text(screen, "🌍 Recycle Bounce", FONT_TITLE,
                       (255, 238, 72), SCREEN_W // 2,
                       card_y + int(5 * SCALE_Y),
                       outline_col=(18, 75, 18), outline_w=3)

    sub = FONT_MED.render("Le Flipper du Tri  ♻", True, (165, 255, 165))
    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2,
                      card_y + int(62 * SCALE_Y)))

    # ── Description ───────────────────────────────────────────────────────────
    desc_y   = int(168 * UI)
    desc_pad = int(58 * SCALE_X)
    desc_w   = SCREEN_W - 2 * desc_pad
    desc_h   = int(72 * UI)
    draw_glass_panel(screen, (desc_pad, desc_y, desc_w, desc_h),
                     fill_col=(10, 48, 10), alpha=195,
                     radius=int(18 * UI), border_col=(55, 155, 55), border_w=max(1, int(2 * UI)))

    d1 = FONT_SMALL.render("Aide la planète en triant les déchets ! 🐇🦔🌸", True, (205, 255, 205))
    d2 = FONT_SMALL.render("Utilise les flippers pour diriger le déchet vers la bonne poubelle.",
                            True, (172, 235, 172))
    screen.blit(d1, (SCREEN_W // 2 - d1.get_width() // 2, desc_y + int(10 * SCALE_Y)))
    screen.blit(d2, (SCREEN_W // 2 - d2.get_width() // 2, desc_y + int(38 * SCALE_Y)))

    # ── Buttons ───────────────────────────────────────────────────────────────
    mx, my  = pygame.mouse.get_pos()
    btn_y   = int(262 * UI)
    bw_btn  = int(268 * SCALE_X)
    bh_play = int(62 * SCALE_Y)
    bh_quit = int(54 * SCALE_Y)

    start_rect = pygame.Rect(SCREEN_W // 2 - bw_btn // 2, btn_y, bw_btn, bh_play)
    quit_rect  = pygame.Rect(SCREEN_W // 2 - bw_btn // 2,
                              btn_y + int(80 * SCALE_Y), bw_btn, bh_quit)

    draw_polished_button(screen, start_rect, COLOR_BTN_GREEN,
                         hovered=start_rect.collidepoint(mx, my),
                         radius=int(31 * UI), label="▶  Jouer !",
                         font=FONT_BIG, text_col=COLOR_WHITE)
    draw_polished_button(screen, quit_rect,  COLOR_BTN_RED,
                         hovered=quit_rect.collidepoint(mx, my),
                         radius=int(27 * UI), label="✕  Quitter",
                         font=FONT_BIG, text_col=COLOR_WHITE)

    # ── Controls hint ─────────────────────────────────────────────────────────
    hint_y = btn_y + int(152 * UI)
    hint_h = int(34 * SCALE_Y)
    draw_glass_panel(screen, (desc_pad, hint_y, desc_w, hint_h),
                     fill_col=(0, 38, 0), alpha=172, radius=int(17 * UI))
    h = FONT_SMALL.render(
        "← Flipper gauche  |  ESPACE Lancer  |  Flipper droit →",
        True, (182, 255, 182))
    screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2,
                    hint_y + int(8 * SCALE_Y)))

    # ── Credit ────────────────────────────────────────────────────────────────
    c = FONT_SMALL.render(
        "EarthTech · EFREI · TI250  —  BRIGUI · EL KAMEL · ABI SAAD",
        True, (138, 212, 138))
    screen.blit(c, (SCREEN_W // 2 - c.get_width() // 2, SCREEN_H - int(30 * SCALE_Y)))

    return start_rect, quit_rect


# ══════════════════════════════════════════════════════════════════════════════
# GAME SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def draw_game():
    ox, oy = get_shake_offset()

    screen.fill((0, 0, 0))
    screen.blit(bg_surf, (ox, oy))

    # Ground grass strip — background layer
    grass_h = grass_surf.get_height()
    screen.blit(grass_surf, (0, SCREEN_H - grass_h + oy))

    # Flower bumpers
    for (bx, by, br, ci) in BUMPERS:
        draw_flower_bumper(screen, bx + ox, by + oy, br, FLOWER_COLORS[ci], frame)

    # Side obstacles
    for g in side_guards:
        g.draw(screen, ox, oy)
    for sb in side_bumpers:
        sb.draw(screen, ox, oy)

    # Waste sprite (shake via rect offset, physics untouched)
    waste.sync_rect()
    bx, by = waste.x, waste.y
    waste.rect.center = (int(bx + ox), int(by + oy))
    waste.draw(screen)
    waste.rect.center = (int(bx), int(by))

    # Flippers (draw with shake offset then restore)
    lp_x, lp_y = left_flipper.px,  left_flipper.py
    rp_x, rp_y = right_flipper.px, right_flipper.py
    left_flipper.px,  left_flipper.py  = lp_x + ox, lp_y + oy
    right_flipper.px, right_flipper.py = rp_x + ox, rp_y + oy
    left_flipper.draw(screen)
    right_flipper.draw(screen)
    left_flipper.px,  left_flipper.py  = lp_x, lp_y
    right_flipper.px, right_flipper.py = rp_x, rp_y

    # Header gradient on top
    screen.blit(header_surf, (0, 0))
    pygame.draw.line(screen, (58, 148, 58),
                     (0, header_surf.get_height()),
                     (SCREEN_W, header_surf.get_height()),
                     max(2, int(2 * UI)))
    draw_header()

    # Top-level UI elements
    for b in BINS:
        b.draw(screen, FONT_ICON, FONT_ICON_SM)
    # Removed launch button

    # Particles
    draw_particles_offset(screen, ox, oy)

    # HUD elements
    draw_waste_card()
    draw_next_waste_panel()
    draw_controls_hint()
    draw_feedback()
    draw_tip_bar()
    draw_screen_flash()

    if paused:
        draw_pause_overlay()


# ══════════════════════════════════════════════════════════════════════════════
# GAME-OVER SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def draw_gameover():
    screen.blit(bg_surf, (0, 0))
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 18, 0, 148))
    screen.blit(ov, (0, 0))
    draw_particles(screen)

    # Central card
    cw = int(420 * SCALE_X)
    ch = int(320 * UI)
    cx = SCREEN_W // 2 - cw // 2
    cy = int(95 * UI)
    draw_glass_panel(screen, (cx, cy, cw, ch),
                     fill_col=(18, 72, 18), alpha=228,
                     radius=int(26 * UI), border_col=(82, 205, 82), border_w=max(2, int(3 * UI)))

    # Title
    if game_completed:
        title_text = "Mission Accomplie ! 🎉"
        eco_text = "Vous avez trié 10 déchets correctement ! 🌟"
    else:
        title_text = "Fin de Partie ! 🎉"
        eco_text = "Merci d'avoir aidé la planète ! 🌱"
    
    draw_outlined_text(screen, title_text, FONT_TITLE,
                       COLOR_YELLOW, SCREEN_W // 2, cy + int(18 * SCALE_Y),
                       outline_col=(18, 72, 18), outline_w=3)

    # Score display (large)
    score_line = FONT_BIG.render(f"⭐  Score final : {score}", True, COLOR_WHITE)
    # Score badge
    sw = score_line.get_width() + int(32 * SCALE_X)
    sh_badge = score_line.get_height() + int(14 * SCALE_Y)
    sx = SCREEN_W // 2 - sw // 2
    sy = cy + int(95 * SCALE_Y)
    rounded_rect(screen, (255, 185, 0), (sx, sy, sw, sh_badge), radius=int(18 * UI))
    screen.blit(score_line, (SCREEN_W // 2 - score_line.get_width() // 2,
                              sy + sh_badge // 2 - score_line.get_height() // 2))

    # Eco message
    eco = FONT_SMALL.render(eco_text, True, (165, 255, 165))
    screen.blit(eco, (SCREEN_W // 2 - eco.get_width() // 2,
                      cy + int(150 * SCALE_Y)))

    # Buttons
    mx, my  = pygame.mouse.get_pos()
    bw_btn  = int(268 * SCALE_X)
    rp_rect = pygame.Rect(SCREEN_W // 2 - bw_btn // 2,
                           cy + int(188 * SCALE_Y), bw_btn, int(54 * SCALE_Y))
    mn_rect = pygame.Rect(SCREEN_W // 2 - bw_btn // 2,
                           cy + int(252 * SCALE_Y), bw_btn, int(48 * SCALE_Y))

    draw_polished_button(screen, rp_rect, COLOR_BTN_GREEN,
                         hovered=rp_rect.collidepoint(mx, my),
                         radius=int(27 * UI), label="↺  Rejouer",
                         font=FONT_BIG, text_col=COLOR_WHITE)
    draw_polished_button(screen, mn_rect, COLOR_BTN_BLUE,
                         hovered=mn_rect.collidepoint(mx, my),
                         radius=int(24 * UI), label="⌂  Menu",
                         font=FONT_BIG, text_col=COLOR_WHITE)

    return rp_rect, mn_rect


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def correct_bin_for(waste_cat: str) -> str:
    names = {"plastic": "Plastique & Métal", "paper": "Papier & Carton",
             "glass": "Verre", "bio": "Bio-Déchets"}
    return names.get(waste_cat, "la bonne poubelle")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

import atexit
tracker = EmissionsTracker()
tracker.start()
atexit.register(tracker.stop)

reset_game()

while True:
    dt = clock.tick(FPS) / 1000.0
    frame += 1

    # ── Smooth score display ──────────────────────────────────────────────────
    score_display += (score - score_display) * min(1.0, dt * 10)
    if score_display > score:
        score_display = float(score)
    if score_flash > 0:
        score_flash -= 1
    if screen_flash_timer > 0:
        screen_flash_timer -= 1

    # ── Events ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                sr, qr = draw_menu()
                if sr.collidepoint(event.pos):
                    reset_game(); state = "game"
                elif qr.collidepoint(event.pos):
                    pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                reset_game(); state = "game"

        elif state == "game":
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Removed launch button click
                pass
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_SPACE and not waste_launched and not paused:
                    waste.launch(); waste_launched = True
                if event.key == pygame.K_ESCAPE:
                    state = "menu"

        elif state == "gameover":
            if event.type == pygame.MOUSEBUTTONDOWN:
                rp, mn = draw_gameover()
                if rp.collidepoint(event.pos):
                    reset_game(); state = "game"
                elif mn.collidepoint(event.pos):
                    state = "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game(); state = "game"
                if event.key == pygame.K_ESCAPE:
                    state = "menu"

    # ── Game logic ────────────────────────────────────────────────────────────
    if state == "game":
        keys = pygame.key.get_pressed()
        if not paused:
            left_flipper.update(keys[pygame.K_LEFT])
            right_flipper.update(keys[pygame.K_RIGHT])

            if waste_launched:
                waste.update(dt, SCREEN_W, SCREEN_H)

                # Nudge impulse
            if nudge_cd > 0:
                nudge_cd -= 1
            if nudge_cd == 0:
                if keys[pygame.K_a]:
                    waste.add_impulse(int(-140 * PHYS_SCALE), int(-35 * SCALE_Y))
                    nudge_cd = 10
                elif keys[pygame.K_d]:
                    waste.add_impulse(int(140 * PHYS_SCALE), int(-35 * SCALE_Y))
                    nudge_cd = 10

            # Flipper collisions
            for fl in (left_flipper, right_flipper):
                if fl.check_collision(waste):
                    waste.vx *= 0.78
                    waste.vy *= 0.78

            # Bumper collisions
            for (bx, by, br, _) in BUMPERS:
                dx = waste.x - bx; dy = waste.y - by
                dist = math.hypot(dx, dy)
                if dist < br + waste.radius:
                    nx, ny = dx / dist, dy / dist
                    dot = waste.vx * nx + waste.vy * ny
                    restitution = 1.2
                    waste.vx -= (1.0 + restitution) * dot * nx
                    waste.vy -= (1.0 + restitution) * dot * ny
                    overlap = br + waste.radius - dist
                    waste.x += nx * overlap; waste.y += ny * overlap
                    waste.stabilize_trajectory(); waste.limit_speed()

            # Side obstacles
            for g in side_guards:
                if g.collide(waste):
                    waste.vx *= 0.82
                    waste.vy *= 0.82
                    waste.stabilize_trajectory(); waste.limit_speed()
            for sb in side_bumpers:
                if sb.collide(waste):
                    waste.vx *= 0.82
                    waste.vy *= 0.82
                    waste.stabilize_trajectory(); waste.limit_speed()

            waste.sync_rect()

            # Bin collisions
            for b in BINS:
                if b.check_collision(waste):
                    name, _card_cat, col = WASTE_LIST[waste_idx]
                    round_num += 1
                    if waste.type == b.category:
                        score += 10
                        score_flash = 45
                        message  = "✅  Super ! +10 points"
                        msg_good = True
                        spawn_particles(int(waste.x), int(waste.y), col, n=22)
                        screen_flash_col   = (0, 220, 100)
                        screen_flash_timer = 20
                        print(f"[Tri] Correct: {waste.type!r} → {b.category!r} (+10)")
                    else:
                        score = max(0, score - 3)
                        message  = f"❌  -3 points ! Va dans {correct_bin_for(waste.type)} !"
                        msg_good = False
                        spawn_particles(int(waste.x), int(waste.y), (255, 80, 80), n=12)
                        screen_flash_col   = (255, 60, 60)
                        screen_flash_timer = 16
                        trigger_shake(strength=3.5, frames=8)
                        print(f"[Tri] Erreur: {waste.type!r} → {b.category!r} (-3)")

                    if round_num > MAX_ROUNDS:
                        game_completed = True
                        state = "gameover"
                    else:
                        msg_timer = 130
                        tip_idx   = (tip_idx + 1) % len(ECO_TIPS)
                        waste_idx = next_waste_idx
                        waste.reset(SCREEN_W // 2, LAUNCH_PAD_Y,
                                    waste_type=WASTE_LIST[waste_idx][1])
                        next_waste_idx = random.randrange(len(WASTE_LIST))
                        _preview_waste.reset(0, 0, waste_type=WASTE_LIST[next_waste_idx][1])
                        waste_launched = False
                    break

            # Waste fell off screen
            if waste.y > SCREEN_H + 20:
                waste_idx = next_waste_idx
                waste.reset(SCREEN_W // 2, LAUNCH_PAD_Y, waste_type=WASTE_LIST[waste_idx][1])
                next_waste_idx = random.randrange(len(WASTE_LIST))
                _preview_waste.reset(0, 0, waste_type=WASTE_LIST[next_waste_idx][1])
                waste_launched = False
                score    = max(0, score - 2)
                message  = "⚠️  Le déchet est tombé !"
                msg_good = False
                msg_timer = 80
                combo = 0; combo_timer = 0
                print(f"[Tri] Nouveau: type={WASTE_LIST[waste_idx][1]!r}")

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 0

        if msg_timer > 0:
            msg_timer -= 1
        update_particles(dt)

        tip_counter += 1
        if tip_counter > FPS * 9:
            tip_counter = 0
            tip_idx = (tip_idx + 1) % len(ECO_TIPS)
            build_tip_surf()

    elif state == "gameover":
        update_particles(dt)

    # ── Draw ──────────────────────────────────────────────────────────────────
    if state == "menu":
        draw_menu()
    elif state == "game":
        draw_game()
    elif state == "gameover":
        draw_gameover()

    pygame.display.flip()
