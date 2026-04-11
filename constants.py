"""
constants.py — Recycle Bounce  (v3 – Polished Mobile UI)
"""

# ── Screen ────────────────────────────────────────────────────────────────────
REF_W = 680
REF_H = 580
SCREEN_W = 720
SCREEN_H = 720
FPS = 60

SCALE_X = SCREEN_W / REF_W
SCALE_Y = SCREEN_H / REF_H
PHYS_SCALE = (SCALE_X + SCALE_Y) / 2

HEADER_H = int(90 * SCALE_X)

# Bin hitbox
BIN_W = int(90 * SCALE_X)
BIN_H = int(BIN_W * 88 // 100)

# ── Palette — eco-friendly, vibrant, mobile-game style ────────────────────────
COLOR_SKY          = ( 45, 165, 230)
COLOR_GRASS_DARK   = ( 28,  95,  28)
COLOR_GRASS_MID    = ( 50, 142,  36)
COLOR_GRASS_LIGHT  = ( 72, 188,  52)
COLOR_RIVER        = ( 68, 168, 218)

COLOR_WHITE        = (255, 255, 255)
COLOR_YELLOW       = (255, 215,   0)
COLOR_GOLD         = (255, 190,  20)
COLOR_DARK_TEXT    = ( 25,  42,  14)
COLOR_CREAM        = (255, 250, 228)
COLOR_ORANGE       = (255, 138,  18)
COLOR_LIGHT_GREEN  = (160, 255, 160)

# Header (gradient: top→bottom)
COLOR_HEADER       = ( 18,  62,  18)
COLOR_HEADER_MID   = ( 28,  88,  28)
COLOR_HEADER_LIGHT = ( 40, 115,  40)

# Bins
COLOR_BIN_YELLOW   = (255, 188,   0)
COLOR_BIN_BLUE     = ( 42, 122, 218)
COLOR_BIN_GREEN    = ( 34, 158,  56)
COLOR_BIN_BROWN    = (148,  86,  24)

# Buttons — 3D style (main / hover / dark base)
COLOR_BTN_GREEN    = ( 46, 170,  68)
COLOR_BTN_GREEN_H  = ( 68, 210,  92)
COLOR_BTN_GREEN_D  = ( 28, 118,  44)
COLOR_BTN_RED      = (210,  52,  52)
COLOR_BTN_RED_H    = (240,  78,  78)
COLOR_BTN_RED_D    = (150,  30,  30)
COLOR_BTN_BLUE     = ( 52, 118, 225)
COLOR_BTN_BLUE_H   = ( 78, 148, 255)
COLOR_BTN_BLUE_D   = ( 30,  80, 165)

# Ball
COLOR_BALL         = (220, 242, 255)
COLOR_BALL_BORDER  = ( 78, 148, 220)

# Flippers
COLOR_FLIPPER_MAIN = (200,  46,  46)
COLOR_FLIPPER_DARK = (138,  18,  18)
COLOR_FLIPPER_GLOW = (255, 170,  85)
COLOR_FLIPPER_ACCENT = (255, 220, 150)

# Bumper petal colours
FLOWER_COLORS = [
    (255, 198,  38),
    (195, 218, 255),
    (255, 175, 198),
    (255, 238,  95),
    (175, 238, 175),
]

# Bumpers (x, y, radius, colour-index) — scaled from REF layout
_RAW_BUMPERS = [
    (160, 370, 26, 0),  # Left guide (higher)
    (160, 220, 26, 1),  # Left guide (higher)
    (450, 350, 26, 1),  # Center (higher)
    (480, 200, 26, 2),  # Right guide (higher)
]
BUMPERS = [
    (int(x * SCALE_X), int(y * SCALE_Y), max(14, int(r * PHYS_SCALE)), c)
    for x, y, r, c in _RAW_BUMPERS
]

# Waste items (display-name, bin-category, badge-colour)
WASTE_LIST = [
    ("Une Bouteille\nen Plastique",  "plastic",  COLOR_BIN_YELLOW),
    ("Une Canette\nen Métal",        "plastic",  COLOR_BIN_YELLOW),
    ("Une Bouteille\nen Verre",      "glass",    COLOR_BIN_GREEN),
    ("Du Papier\nUsagé",             "paper",    COLOR_BIN_BLUE),
    ("Un Carton\nde Lait",           "paper",    COLOR_BIN_BLUE),
    ("Des Épluchures",               "bio",      COLOR_BIN_BROWN),
    ("Une Peau\nde Banane",          "bio",      COLOR_BIN_BROWN),
]

ECO_TIPS = [
    "💡  Le plastique met 450 ans à se décomposer !",
    "💡  Le verre peut être recyclé à l'infini !",
    "💡  1 tonne de papier recyclé = 17 arbres sauvés.",
    "💡  Les bio-déchets font d'excellent compost !",
    "💡  Recycler 1 kg d'alu économise 8 kg de CO₂.",
    "💡  En France, on recycle 68 % du verre !",
]
