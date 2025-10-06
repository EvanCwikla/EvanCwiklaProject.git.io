# settings.py

# --- GAME CONFIG ---
TILE = 32
VIEW_W, VIEW_H = 20, 15
WIDTH, HEIGHT = VIEW_W * TILE, VIEW_H * TILE
FPS = 60

# --- GRID SIZES (can be overridden by each level) ---
# Default grid size, used by level 1
GRID_W, GRID_H = 41, 31

# --- COLORS ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (80, 80, 80)
GREEN = (0, 200, 0)
PLAYER_GREEN = (80, 255, 80)
RED = (255, 80, 80)
BLUE = (100, 100, 255)
YELLOW = (240, 240, 0)
BROWN = (160, 80, 40)
