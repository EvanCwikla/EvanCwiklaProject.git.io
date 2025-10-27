# levels/level7.py
import pygame
from settings import *
from levels.level_base import Level
# We need to import the Key class
from game_objects import Player, Door, Gear, Key

class Level7(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 40, 25
        
        # --- Level Layout ---
        self._create_layout()
        self.player = Player(3, 3)
        self.door = Door(self.grid_w - 4, self.grid_h - 4)
        self.door.locked = True # Door starts locked
        
        # --- Puzzle Elements ---
        # Gears just spin and are dangerous
        self.gears = [
            Gear(x=10, y=8, radius=4, speed=1),
            Gear(x=20, y=15, radius=5, speed=-1.5),
            Gear(x=30, y=6, radius=4, speed=2)
        ]
        
        # --- Place keys in dangerous spots ---
        self.keys = [
            Key(x=10, y=13), # Tucked under gear 1
            Key(x=15, y=15), # Between gear 1 and 2
            Key(x=30, y=11)  # Tucked under gear 3
        ]

    def _create_layout(self):
        """Creates a simple room."""
        self.walls = set()
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if x == 0 or x == self.grid_w - 1 or y == 0 or y == self.grid_h - 1:
                    self.walls.add((x, y))

    def get_obstacles(self):
        """
        Returns all impassable tiles:
        1. Walls
        2. Spinning gear spokes
        3. Gear axles (the center)
        """
        obstacles = self.walls.copy()
        for gear in self.gears:
            obstacles.update(gear.get_hazard_tiles())
            obstacles.add(gear.get_axle_tile()) # Add center axle as an obstacle
        return obstacles

    def handle_event(self, event):
        """No interaction (like SPACE) is needed for this level."""
        pass

    def update(self):
        """Update player, gears, and check for hazards/wins."""
        # Update player movement, aware of gear hazards
        self.player.update(self.get_obstacles())

        all_hazards = set()
        # Update all gears
        for gear in self.gears:
            gear.update()
            all_hazards.update(gear.get_hazard_tiles())
            all_hazards.add(gear.get_axle_tile()) # Axle is also a hazard

        # --- Action Element: Check for player death ---
        if (self.player.x, self.player.y) in all_hazards:
            print("Hit by gear! Resetting level.")
            self.__init__() # Reload the level
            return

        # --- Key Collection Logic ---
        for k in self.keys:
            if not k.collected and (self.player.x, self.player.y) == (k.x, k.y):
                k.collected = True
                print("Collected a key!")
        
        # --- Win Condition Logic ---
        if all(k.collected for k in self.keys):
            self.door.locked = False
        
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 7 Complete!")
            self.is_complete = True

    def draw(self, surface):
        """Draws the room, gears, player, and door."""
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))
        
        surface.fill(BLACK)
        
        # Draw walls
        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, (y - camy) * TILE, TILE, TILE))

        # Draw gears
        for gear in self.gears:
            gear.draw(surface, camx, camy)
            
        # --- Draw keys ---
        for k in self.keys:
            k.draw(surface, camx, camy)
        
        # Draw player and door
        self.door.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
