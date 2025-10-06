# levels/level1.py
import pygame
import random
from settings import *
from levels.level_base import Level
from game_objects import Player, Key, Door


class Level1(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 41, 31
        self.walls = self._generate_maze(self.grid_w, self.grid_h)
        self.player = Player(1, 1)
        open_spaces = [(x, y) for x in range(1, self.grid_w - 1)
                       for y in range(1, self.grid_h - 1) if (x, y) not in self.walls]
        random.shuffle(open_spaces)
        self.keys = [Key(*pos) for pos in open_spaces[:3]]
        self.door = Door(self.grid_w - 2, self.grid_h - 2)

    # _generate_maze method remains the same...
    def _generate_maze(self, w, h):
        walls = {(x, y) for x in range(w) for y in range(h)}
        start = (1, 1)
        stack, carved = [start], {start}
        walls.remove(start)
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        while stack:
            x, y = stack[-1]
            random.shuffle(dirs)
            moved = False
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < w - 1 and 1 <= ny < h - 1 and (nx, ny) not in carved:
                    walls.discard((x + dx // 2, y + dy // 2))
                    walls.discard((nx, ny))
                    carved.add((nx, ny))
                    stack.append((nx, ny))
                    moved = True
                    break
            if not moved:
                stack.pop()
        return walls

    def get_obstacles(self):
        """Level 1 only has walls as obstacles."""
        return self.walls

    def handle_event(self, event):
        """
        Handles player input.
        Notice the arrow key logic has been REMOVED from here.
        This method is now empty for this level, but other levels might
        still need it for things like the spacebar in Level 3.
        """
        pass

    def update(self):
        """Updates the logic for the level."""
        # --- NEW ---
        # Call the player's own update method for movement
        self.player.update(self.get_obstacles())

        # Check for key collection
        for k in self.keys:
            if not k.collected and (self.player.x, self.player.y) == (k.x, k.y):
                k.collected = True
                print("Collected a key!")

        # Unlock the door if all keys are collected
        if all(k.collected for k in self.keys):
            self.door.locked = False

        # Check for the win condition
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 1 Complete!")
            self.is_complete = True

    # draw method remains the same...
    def draw(self, surface):
        cam_x = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        cam_y = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))
        surface.fill(BLACK)
        for (x, y) in self.walls:
            if cam_x <= x < cam_x + VIEW_W and cam_y <= y < cam_y + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - cam_x) * TILE, (y - cam_y) * TILE, TILE, TILE))
        for k in self.keys: k.draw(surface, cam_x, cam_y)
        self.door.draw(surface, cam_x, cam_y)
        self.player.draw(surface, cam_x, cam_y)
