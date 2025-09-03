import pygame, random, sys

pygame.init()

# --- CONFIG ---
WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (50, 50, 200)
GREEN = (50, 200, 50)
RED   = (200, 50, 50)
YELLOW= (200, 200, 50)

font = pygame.font.SysFont(None, 40)

# --- Base Level Class ---
class Level:
    def __init__(self, manager):
        self.manager = manager

    def handle_events(self, events): pass
    def update(self): pass
    def draw(self, surface): pass

# --- Maze Level ---
class MazeLevel(Level):
    TILE = 20
    ROWS, COLS = 61, 61
    PLAYER_SPEED = 3

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 40)

        # fixed maze every run
        random.seed(42)
        self.maze = self.generate_maze(self.ROWS, self.COLS)
        self.maze[self.ROWS-2][self.COLS-2] = "G"

        self.player_rect = pygame.Rect(self.TILE+2, self.TILE+2, self.TILE-4, self.TILE-4)

    def generate_maze(self, rows, cols):
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

        # deterministic extra openings
        for r in range(2, rows-2, 10):
            for c in range(2, cols-2, 10):
                maze[r][c] = "."

        return maze

    def move_with_collision(self, rect, dx, dy):
        new_rect = rect.move(dx, dy)
        for px, py in [(new_rect.left, new_rect.top),
                       (new_rect.right-1, new_rect.top),
                       (new_rect.left, new_rect.bottom-1),
                       (new_rect.right-1, new_rect.bottom-1)]:
            grid_r, grid_c = py // self.TILE, px // self.TILE
            if 0 <= grid_r < self.ROWS and 0 <= grid_c < self.COLS:
                if self.maze[grid_r][grid_c] == "#":
                    return rect
        return new_rect

    def handle_events(self, events):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]: dx = -self.PLAYER_SPEED
        if keys[pygame.K_RIGHT]: dx = self.PLAYER_SPEED
        if keys[pygame.K_UP]: dy = -self.PLAYER_SPEED
        if keys[pygame.K_DOWN]: dy = self.PLAYER_SPEED

        self.player_rect = self.move_with_collision(self.player_rect, dx, dy)

        grid_r, grid_c = self.player_rect.centery // self.TILE, self.player_rect.centerx // self.TILE
        if self.maze[grid_r][grid_c] == "G":
            self.manager.next_level()

    def update(self): pass

    def draw(self, surface):
        cam_x = self.player_rect.centerx - WIDTH // 2
        cam_y = self.player_rect.centery - HEIGHT // 2
        cam_x = max(0, min(cam_x, self.COLS*self.TILE - WIDTH))
        cam_y = max(0, min(cam_y, self.ROWS*self.TILE - HEIGHT))

        surface.fill(BLACK)

        start_r = cam_y // self.TILE
        end_r = (cam_y + HEIGHT) // self.TILE + 1
        start_c = cam_x // self.TILE
        end_c = (cam_x + WIDTH) // self.TILE + 1

        for r in range(start_r, min(end_r, self.ROWS)):
            for c in range(start_c, min(end_c, self.COLS)):
                cell = self.maze[r][c]
                x, y = c*self.TILE - cam_x, r*self.TILE - cam_y
                if cell == "#":
                    pygame.draw.rect(surface, BLUE, (x, y, self.TILE, self.TILE))
                elif cell == "G":
                    pygame.draw.rect(surface, GREEN, (x+4, y+4, self.TILE-8, self.TILE-8))

        pygame.draw.rect(surface, RED, (self.player_rect.x - cam_x,
                                        self.player_rect.y - cam_y,
                                        self.player_rect.width,
                                        self.player_rect.height))

# --- Placeholder Memory Puzzle ---
class MemoryLevel(Level):
    def __init__(self, manager):
        super().__init__(manager)
        self.counter = 180

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self.manager.next_level()

    def update(self):
        self.counter -= 1
        if self.counter <= 0:
            self.manager.next_level()

    def draw(self, surface):
        surface.fill(BLACK)
        text = font.render("Memory Puzzle (Press SPACE)", True, WHITE)
        surface.blit(text, (WIDTH//2 - 200, HEIGHT//2))

# --- Placeholder Sokoban Puzzle ---
class SokobanLevel(Level):
    def __init__(self, manager):
        super().__init__(manager)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                self.manager.next_level()

    def draw(self, surface):
        surface.fill(YELLOW)
        text = font.render("Sokoban Puzzle (Press ENTER)", True, BLACK)
        surface.blit(text, (WIDTH//2 - 200, HEIGHT//2))

# --- Level Manager ---
class LevelManager:
    def __init__(self):
        self.levels = [MazeLevel(self), MemoryLevel(self), SokobanLevel(self)]
        self.current = 0
        self.active_level = self.levels[self.current]

    def next_level(self):
        self.current += 1
        if self.current < len(self.levels):
            self.active_level = self.levels[self.current]
        else:
            print("Game Complete!")
            pygame.quit()
            sys.exit()

    def handle_events(self, events):
        self.active_level.handle_events(events)

    def update(self):
        self.active_level.update()

    def draw(self, surface):
        self.active_level.draw(surface)

# --- Main Game Loop ---
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Arcade Puzzle Game")
    clock = pygame.time.Clock()

    manager = LevelManager()
    running = True

    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False

        manager.handle_events(events)
        manager.update()
        manager.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
