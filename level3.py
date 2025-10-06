# levels/level3.py
import pygame
import random
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, Mirror


# --- Helper classes specific to this level ---

class LightBeam:
    """Calculates and manages the path of the light beam."""

    def __init__(self, source, mirrors, door):
        self.source = source
        self.mirrors = mirrors
        self.door = door
        self.path = []
        self.update()

    def update(self):
        """Recalculates the beam's path based on mirror orientations."""
        self.door.locked = True
        self.path = []
        x, y, dx, dy = self.source

        for _ in range(GRID_W * GRID_H):
            x += dx
            y += dy
            self.path.append((x, y))

            if (x, y) == (self.door.x, self.door.y):
                self.door.locked = False
                break

            mirror_hit = False
            for m in self.mirrors:
                if (x, y) == (m.x, m.y):
                    dx, dy = (-dy, -dx) if m.orientation == "/" else (dy, dx)
                    mirror_hit = True
                    break

            if not mirror_hit and not (0 < x < self.door.x + 5 and 0 < y < self.door.y + 30):
                break

    def draw(self, surf, camx, camy):
        for (x, y) in self.path:
            rect = ((x - camx) * TILE + TILE // 4,
                    (y - camy) * TILE + TILE // 4,
                    TILE // 2, TILE // 2)
            pygame.draw.rect(surf, YELLOW, rect)


class Hazard:
    """A moving hazard that resets the level on contact with the player."""

    def __init__(self, x, y, dx, dy):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.speed_timer = random.randint(0, 10)

    def update(self, player, walls):
        self.speed_timer += 1
        if self.speed_timer < 10:
            return None
        self.speed_timer = 0

        nx, ny = self.x + self.dx, self.y + self.dy
        if (nx, ny) in walls:
            if (self.x + self.dx, self.y) in walls: self.dx *= -1
            if (self.x, self.y + self.dy) in walls: self.dy *= -1
            nx, ny = self.x + self.dx, self.y + self.dy

        self.x, self.y = nx, ny

        if (self.x, self.y) == (player.x, player.y):
            return "reset"

    def draw(self, surf, camx, camy):
        pygame.draw.rect(surf, RED, ((self.x - camx) * TILE, (self.y - camy) * TILE, TILE, TILE))


# --- Main Level Class ---

class Level3(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 61, 41

        self.walls = set()
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                self.walls.add((x, y))
        self._carve_rect(2, 2, 58, 38)

        self.player = Player(4, 10)
        self.door = Door(55, 6)
        self.walls.discard((self.door.x, self.door.y))

        self.mirrors = [
            Mirror(12, 10, "/"), Mirror(12, 6, "\\"), Mirror(30, 6, "\\"),
            Mirror(30, 12, "/"), Mirror(48, 12, "\\"), Mirror(48, 6, "/")
        ]
        self.hazards = [
            Hazard(random.randint(8, 50), random.randint(5, 30), *random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])) for
            _ in range(8)]

        source = (5, 10, 1, 0)
        self.beam = LightBeam(source, self.mirrors, self.door)

    def _carve_rect(self, x1, y1, x2, y2):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.walls.discard((x, y))

    def handle_event(self, event):
        """Handles single-press actions like rotating mirrors."""
        if event.type == pygame.KEYDOWN:
            # The arrow key logic is gone, but the spacebar logic remains.
            if event.key == pygame.K_SPACE:
                for m in self.mirrors:
                    if (m.x, m.y) == (self.player.x, self.player.y):
                        m.rotate()
                        self.beam.update()

    def update(self):
        """Updates player movement and all puzzle/hazard logic."""
        # --- NEW: Handle player's continuous movement ---
        self.player.update(self.walls)  # For this level, only walls are obstacles.

        # Update hazards and check if player was hit
        for h in self.hazards:
            if h.update(self.player, self.walls) == "reset":
                print("Hit by hazard! Resetting level.")
                self.__init__()
                return

        # Check for win condition
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 3 Complete!")
            self.is_complete = True

    def draw(self, surface):
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))

        surface.fill(BLACK)

        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, (y - camy) * TILE, TILE, TILE))

        for m in self.mirrors: m.draw(surface, camx, camy)
        self.beam.draw(surface, camx, camy)
        self.door.draw(surface, camx, camy)
        for h in self.hazards: h.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
