# levels/level6.py
import pygame
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, Bridge


class Level6(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 50, 15

        # --- Level Layout ---
        self._create_layout()
        self.player = Player(2, self.grid_h // 2)
        self.door = Door(self.grid_w - 3, self.grid_h // 2)
        self.door.locked = False  # The challenge is timing, not a puzzle lock

    def _create_layout(self):
        """Creates platforms and the timed bridges between them."""
        self.walls = set()
        # Create a floor and ceiling
        for x in range(self.grid_w):
            self.walls.add((x, 0))
            self.walls.add((x, self.grid_h - 1))

        # Create solid platforms with gaps in between
        platforms = [(1, 8), (14, 20), (26, 32), (38, 48)]
        for start, end in platforms:
            for x in range(start, end):
                for y in range(1, self.grid_h - 1):
                    # Leave a path in the middle
                    if y != self.grid_h // 2:
                        self.walls.add((x, y))

        # --- Bridge Creation ---
        self.bridges = []
        # Gap 1: A simple, slow bridge
        for x in range(9, 14):
            self.bridges.append(Bridge(x, self.grid_h // 2, solid_time=FPS * 3, vanish_time=FPS * 2, offset=0))

        # Gap 2: A faster bridge, slightly offset
        for x in range(21, 26):
            self.bridges.append(Bridge(x, self.grid_h // 2, solid_time=FPS * 2, vanish_time=FPS * 2, offset=FPS))

        # Gap 3: A "running" bridge where tiles appear one after another
        for i, x in enumerate(range(33, 38)):
            # Each tile appears 1/4 second after the last one
            offset = FPS * 1.5 + (i * FPS // 4)
            self.bridges.append(Bridge(x, self.grid_h // 2, solid_time=FPS * 2, vanish_time=FPS * 2.5, offset=offset))

    def get_obstacles(self):
        """Return walls AND any bridge tiles that are NOT solid."""
        obstacles = self.walls.copy()
        for bridge in self.bridges:
            if not bridge.is_solid:
                obstacles.add((bridge.x, bridge.y))
        return obstacles

    def handle_event(self, event):
        # We use the player.update() for movement, so this is not needed for this level
        pass

    def update(self):
        """Update player movement and the state of all bridges."""
        # Update bridges first to determine where the player can move
        for bridge in self.bridges:
            bridge.update()

        # Update player movement based on the current obstacles
        self.player.update(self.get_obstacles())

        # Check for win condition
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 6 Complete!")
            self.is_complete = True

    def draw(self, surface):
        # This level is linear, so a simple camera works fine
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = 0  # No vertical camera movement needed

        surface.fill(BLACK)

        # Draw walls
        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, y * TILE, TILE, TILE))

        # Draw bridges
        for bridge in self.bridges:
            if camx <= bridge.x < camx + VIEW_W:
                bridge.draw(surface, camx, camy)

        # Draw player and door
        self.door.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
