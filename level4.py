# levels/level4.py
import pygame
import random
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, Enemy


# --- Helper class specific to this level's puzzle ---

class MemoryPuzzle:
    """Manages the 'Simon Says' memory puzzle logic and drawing."""

    def __init__(self, tiles, length=4):
        self.tiles = tiles
        self.sequence = [random.choice(self.tiles) for _ in range(length)]
        self.progress = []
        self.show_index = 0
        self.show_timer = 30
        self.showing = True
        self.complete = False
        self.last_player_pos = None

    def update(self, player):
        if self.complete:
            return

        # Phase 1: Show the sequence to the player
        if self.showing:
            self.show_timer -= 1
            if self.show_timer <= 0:
                self.show_index += 1
                self.show_timer = 30
                if self.show_index >= len(self.sequence):
                    self.showing = False
            return

        # Phase 2: Player tries to replicate the sequence
        player_pos = (player.x, player.y)
        if player_pos in self.tiles and player_pos != self.last_player_pos:
            self.progress.append(player_pos)
            if self.progress[-1] != self.sequence[len(self.progress) - 1]:
                print("Wrong sequence! Resetting puzzle.")
                self.progress = []
            elif len(self.progress) == len(self.sequence):
                print("Puzzle Solved!")
                self.complete = True
        self.last_player_pos = player_pos

    def draw(self, surf, camx, camy):
        for tile_pos in self.tiles:
            tx, ty = tile_pos
            rect = ((tx - camx) * TILE, (ty - camy) * TILE, TILE, TILE)
            pygame.draw.rect(surf, DARK_GRAY, rect, 2)

            if self.showing and self.sequence[self.show_index] == tile_pos and self.show_timer > 5:
                pygame.draw.rect(surf, YELLOW, rect)

            if tile_pos in self.progress:
                pygame.draw.rect(surf, GREEN, rect)


# --- Main Level Class ---

class Level4(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 61, 41

        self.walls = set()
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                self.walls.add((x, y))
        self._carve_rect(2, 2, 58, 38)

        self.player = Player(5, 20)
        self.door = Door(55, 20)
        self.walls.discard((self.door.x, self.door.y))

        tiles = [(20, 15), (22, 15), (24, 15), (26, 15),
                 (20, 17), (22, 17), (24, 17), (26, 17)]
        self.puzzle = MemoryPuzzle(tiles, length=5)

        self.enemies = [
            Enemy(15, 10, [(15, 10), (40, 10)]),
            Enemy(40, 30, [(40, 30), (15, 30)]),
            Enemy(30, 5, [(30, 5), (30, 35)])
        ]

    def _carve_rect(self, x1, y1, x2, y2):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.walls.discard((x, y))

    def handle_event(self, event):
        """This method is now empty for this level."""
        pass

    def update(self):
        """Updates player movement, puzzle logic, and enemies."""
        # --- NEW: Handle player's continuous movement ---
        self.player.update(self.walls)

        # Update puzzle and enemies
        self.puzzle.update(self.player)

        for en in self.enemies:
            if en.update(self.player) == "reset":
                print("Caught by enemy! Resetting level.")
                self.__init__()
                return

        if self.puzzle.complete:
            self.door.locked = False

        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 4 Complete!")
            self.is_complete = True

    def draw(self, surface):
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))

        surface.fill(BLACK)

        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, (y - camy) * TILE, TILE, TILE))

        self.puzzle.draw(surface, camx, camy)
        for en in self.enemies:
            en.draw(surface, camx, camy)

        self.door.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
