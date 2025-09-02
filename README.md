# EvanCwiklaProject.git.io

import pygame, random

# --- CONFIG ---
TILE = 20
ROWS, COLS = 61, 61   # big maze
WIDTH, HEIGHT = 620, 420  # screen size (fixed window)
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE  = (50, 50, 200)
RED   = (200, 50, 50)
GREEN = (50, 200, 50)

PLAYER_SPEED = 3

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smooth Maze Explorer")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

# --- Maze Generation (recursive backtracker) ---
def generate_maze(rows, cols):
    maze = [["#" for _ in range(cols)] for _ in range(rows)]

    def carve(r, c):
        dirs = [(2,0), (-2,0), (0,2), (0,-2)]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 < nr < rows-1 and 0 < nc < cols-1 and maze[nr][nc] == "#":
                maze[nr][nc] = "."
                maze[r+dr//2][c+dc//2] = "."
                carve(nr, nc)

    maze[1][1] = "."
    carve(1,1)
    return maze

maze = generate_maze(ROWS, COLS)
maze[ROWS-2][COLS-2] = "G"   # goal in bottom-right

# --- Player ---
player_rect = pygame.Rect(TILE+2, TILE+2, TILE-4, TILE-4)

# --- Movement with collision ---
def move_with_collision(rect, dx, dy):
    new_rect = rect.move(dx, dy)
    # check all corners of the rect against maze
    for px, py in [(new_rect.left, new_rect.top),
                   (new_rect.right-1, new_rect.top),
                   (new_rect.left, new_rect.bottom-1),
                   (new_rect.right-1, new_rect.bottom-1)]:
        grid_r, grid_c = py // TILE, px // TILE
        if 0 <= grid_r < ROWS and 0 <= grid_c < COLS:
            if maze[grid_r][grid_c] == "#":
                return rect  # block movement
    return new_rect

win = False
running = True
while running:
    clock.tick(FPS)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    dx = dy = 0
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: dx = -PLAYER_SPEED
    if keys[pygame.K_RIGHT]: dx = PLAYER_SPEED
    if keys[pygame.K_UP]: dy = -PLAYER_SPEED
    if keys[pygame.K_DOWN]: dy = PLAYER_SPEED

    player_rect = move_with_collision(player_rect, dx, dy)

    # --- Camera center on player ---
    cam_x = player_rect.centerx - WIDTH // 2
    cam_y = player_rect.centery - HEIGHT // 2

    # Clamp camera inside maze bounds
    cam_x = max(0, min(cam_x, COLS*TILE - WIDTH))
    cam_y = max(0, min(cam_y, ROWS*TILE - HEIGHT))

    # --- Check win ---
    grid_r, grid_c = player_rect.centery // TILE, player_rect.centerx // TILE
    if maze[grid_r][grid_c] == "G":
        win = True

    # --- Draw ---
    screen.fill(BLACK)

    start_r = cam_y // TILE
    end_r = (cam_y + HEIGHT) // TILE + 1
    start_c = cam_x // TILE
    end_c = (cam_x + WIDTH) // TILE + 1

    for r in range(start_r, min(end_r, ROWS)):
        for c in range(start_c, min(end_c, COLS)):
            cell = maze[r][c]
            x, y = c*TILE - cam_x, r*TILE - cam_y
            if cell == "#":
                pygame.draw.rect(screen, BLUE, (x, y, TILE, TILE))
            elif cell == "G":
                pygame.draw.rect(screen, GREEN, (x+4, y+4, TILE-8, TILE-8))

    # Draw player relative to camera
    pygame.draw.rect(screen, RED, (player_rect.x - cam_x, player_rect.y - cam_y,
                                   player_rect.width, player_rect.height))

    if win:
        txt = font.render("YOU WIN!", True, GREEN)
        screen.blit(txt, (WIDTH//2 - 80, HEIGHT//2 - 20))

    pygame.display.flip()

pygame.quit()
