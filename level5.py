# levels/level5.py
import pygame
import random
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, Boulder, PressurePlate


# --- Main Level Class ---
class Level5(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 25, 20
        self.walls = set()

        # Player movement timing
        self.move_cooldown = 8
        self.move_timer = 0

        # --- Level Design ---
        self._create_layout()
        self.player = Player(4, 5)
        self.door = Door(self.grid_w - 2, self.grid_h // 2)

        # --- Puzzle Elements ---
        self.boulders = [
            Boulder(7, 5),
            Boulder(10, 8),
            Boulder(7, 11)
        ]
        self.plates = [
            PressurePlate(18, 4),
            PressurePlate(20, 9),
            PressurePlate(18, 14)
        ]

    def _create_layout(self):
        """Creates the rooms and corridors for the level."""
        # Create a border of walls
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if x == 0 or x == self.grid_w - 1 or y == 0 or y == self.grid_h - 1:
                    self.walls.add((x, y))

        # Add some internal walls to make the puzzle interesting
        for y in range(8, 12): self.walls.add((14, y))
        for y in range(0, 5): self.walls.add((14, y))
        for y in range(15, 20): self.walls.add((14, y))

    def handle_event(self, event):
        """
        For this level, we handle movement here to implement push logic.
        We do NOT use player.update().
        """
        # This is a placeholder since movement is now in update()
        pass

    def update(self):
        """Updates player movement, puzzle logic, and win condition."""
        # --- Custom Player Movement for Sokoban Logic ---
        if self.move_timer > 0:
            self.move_timer -= 1

        if self.move_timer == 0:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]:
                dx = -1
            elif keys[pygame.K_RIGHT]:
                dx = 1
            elif keys[pygame.K_UP]:
                dy = -1
            elif keys[pygame.K_DOWN]:
                dy = 1

            if dx != 0 or dy != 0:
                self.try_move_player(dx, dy)
                self.move_timer = self.move_cooldown

        # --- Puzzle Logic ---
        all_plates_active = True
        boulder_positions = {(b.x, b.y) for b in self.boulders}
        for plate in self.plates:
            if (plate.x, plate.y) in boulder_positions:
                plate.is_active = True
            else:
                plate.is_active = False
                all_plates_active = False  # If any plate is not active, keep door locked

        # --- Win Condition ---
        if all_plates_active:
            self.door.locked = False

        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 5 Complete!")
            self.is_complete = True

    def try_move_player(self, dx, dy):
        """The core logic for pushing boulders."""
        target_x = self.player.x + dx
        target_y = self.player.y + dy

        # Check if the target tile is a wall
        if (target_x, target_y) in self.walls:
            return  # Can't move into a wall

        boulder_to_push = None
        for boulder in self.boulders:
            if boulder.x == target_x and boulder.y == target_y:
                boulder_to_push = boulder
                break

        # Case 1: Moving into an empty space
        if boulder_to_push is None:
            self.player.x = target_x
            self.player.y = target_y
            return

        # Case 2: Trying to push a boulder
        else:
            boulder_target_x = boulder_to_push.x + dx
            boulder_target_y = boulder_to_push.y + dy

            # Check if space behind boulder is blocked by a wall or another boulder
            if (boulder_target_x, boulder_target_y) in self.walls:
                return
            for other_boulder in self.boulders:
                if other_boulder.x == boulder_target_x and other_boulder.y == boulder_target_y:
                    return  # Blocked by another boulder

            # If the space is clear, move both player and boulder
            boulder_to_push.x = boulder_target_x
            boulder_to_push.y = boulder_target_y
            self.player.x = target_x
            self.player.y = target_y

    def draw(self, surface):
        # This level is small, so we don't need a scrolling camera
        camx, camy = 0, 0
        surface.fill(BLACK)

        for (x, y) in self.walls:
            pygame.draw.rect(surface, GRAY, (x * TILE, y * TILE, TILE, TILE))

        for plate in self.plates: plate.draw(surface, camx, camy)
        for boulder in self.boulders: boulder.draw(surface, camx, camy)

        self.door.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
