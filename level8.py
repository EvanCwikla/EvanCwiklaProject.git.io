# levels/level8.py
import pygame
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, ChaserEnemy
from game_objects import Boulder, PressurePlate, Gear, Bridge
from game_objects import Mirror


# --- LIGHTBEAM HELPER CLASS ---
class LightBeam:
    """Manages the light beam for the final puzzle."""

    def __init__(self, source, mirrors, door, grid_w, grid_h):
        self.source = source
        self.mirrors = mirrors
        self.door = door
        self.path = []
        self.is_active = False
        self.grid_w, self.grid_h = grid_w, grid_h

    def update(self):
        """Calculates the beam's path if it's active."""
        if not self.is_active:
            self.path = []
            self.door.locked = True
            return

        self.door.locked = True
        self.path = []
        x, y, dx, dy = self.source

        for _ in range(self.grid_w * self.grid_h):
            x += dx;
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

            if not mirror_hit and not (0 < x < self.grid_w - 1 and 0 < y < self.grid_h - 1):
                break

    def draw(self, surf, camx, camy):
        if not self.is_active:
            return
        color = GREEN if not self.door.locked else YELLOW
        for (x, y) in self.path:
            rect = ((x - camx) * TILE + TILE // 4, (y - camy) * TILE + TILE // 4, TILE // 2, TILE // 2)
            pygame.draw.rect(surf, color, rect)


# --- END HELPER CLASS ---


class Level8(Level):
    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 30, 20
        self.walls = set()

        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if x == 0 or x == self.grid_w - 1 or y == 0 or y == self.grid_h - 1:
                    self.walls.add((x, y))

        for x in range(1, self.grid_w - 1):
            self.walls.add((x, 8))
            self.walls.add((x, 12))

        for x in range(12, 18):
            self.walls.discard((x, 8))
            self.walls.discard((x, 12))

        self.player = Player(5, 5)

        self.door = Door(self.grid_w - 2, self.grid_h // 2)  # Door is at (28, 10)
        self.door.locked = True

        self.chaser = ChaserEnemy(26, 3)

        self.boulders = [Boulder(10, 15)]
        self.plates = [PressurePlate(18, 15)]

        self.gears = [
            Gear(x=25, y=16, radius=2, speed=1.5),
            Gear(x=20, y=5, radius=3, speed=-1)
        ]

        self.bridges = []
        for x in range(12, 18):
            self.bridges.append(Bridge(x, 9, FPS * 2, FPS * 2, offset=(x % 2) * FPS * 2))
            self.bridges.append(Bridge(x, 11, FPS * 2, FPS * 2, offset=((x + 1) % 2) * FPS * 2))

        # --- NEW: Corrected Light Beam puzzle ---
        # Mirror is at (25, 10), starts with the WRONG orientation
        self.mirrors = [Mirror(25, 10, "\\")]
        # Source is in the wall at (25, 12), aiming UP
        self.light_source_pos = (25, 12, 0, -1)
        # --- END NEW ---

        self.beam = LightBeam(self.light_source_pos, self.mirrors, self.door, self.grid_w, self.grid_h)

        self.move_cooldown = 8
        self.move_timer = 0

    def get_obstacles(self):
        """Returns all impassable tiles (walls, gear axles, spokes, bridges)."""
        obstacles = self.walls.copy()

        for gear in self.gears:
            obstacles.update(gear.get_hazard_tiles())
            obstacles.add(gear.get_axle_tile())

        for bridge in self.bridges:
            if not bridge.is_solid:
                obstacles.add((bridge.x, bridge.y))

        return obstacles

    def handle_event(self, event):
        """Handles player input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                for mirror in self.mirrors:
                    if (self.player.x, self.player.y) == (mirror.x, mirror.y):
                        mirror.rotate()
                        self.beam.update()  # Recalculate beam path
                        break

    def update(self):
        """Updates all game logic for the level."""

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

        for gear in self.gears:
            gear.update()

        for bridge in self.bridges:
            bridge.update()

        chaser_obstacles = self.get_obstacles().copy()
        for b in self.boulders:
            chaser_obstacles.add((b.x, b.y))
        for m in self.mirrors:
            chaser_obstacles.add((m.x, m.y))

        if self.chaser.update(self.player, chaser_obstacles) == "reset":
            print("Caught by the chaser! Resetting level.")
            self.__init__()
            return

        all_hazards = set()
        for gear in self.gears:
            all_hazards.update(gear.get_hazard_tiles())
            all_hazards.add(gear.get_axle_tile())

        if (self.player.x, self.player.y) in all_hazards:
            print("Hit by gear! Resetting level.")
            self.__init__()
            return

        boulder_positions = {(b.x, b.y) for b in self.boulders}
        all_plates_active = True
        for plate in self.plates:
            if (plate.x, plate.y) in boulder_positions:
                plate.is_active = True
            else:
                plate.is_active = False
                all_plates_active = False

        self.beam.is_active = all_plates_active
        self.beam.update()

        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 8 Complete! YOU WIN!")
            self.is_complete = True

    def try_move_player(self, dx, dy):
        """Handles player movement and boulder pushing."""
        target_x = self.player.x + dx
        target_y = self.player.y + dy

        if (target_x, target_y) in self.get_obstacles():
            return

        boulder_to_push = None
        for boulder in self.boulders:
            if boulder.x == target_x and boulder.y == target_y:
                boulder_to_push = boulder
                break

        if boulder_to_push is None:
            # Player can move onto mirrors, so no special check needed
            self.player.x = target_x
            self.player.y = target_y
            return

        else:
            boulder_target_x = boulder_to_push.x + dx
            boulder_target_y = boulder_to_push.y + dy

            if (boulder_target_x, boulder_target_y) in self.get_obstacles():
                return
            for other_boulder in self.boulders:
                if other_boulder.x == boulder_target_x and other_boulder.y == boulder_target_y:
                    return
            for m in self.mirrors:
                if (boulder_target_x, boulder_target_y) == (m.x, m.y):
                    return

            boulder_to_push.x = boulder_target_x
            boulder_to_push.y = boulder_target_y
            self.player.x = target_x
            self.player.y = target_y

    def draw(self, surface):
        """Draws all level elements."""
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))

        surface.fill(BLACK)

        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, (y - camy) * TILE, TILE, TILE))

        for plate in self.plates:
            plate.draw(surface, camx, camy)

        self.beam.draw(surface, camx, camy)

        for mirror in self.mirrors:
            mirror.draw(surface, camx, camy)

        for boulder in self.boulders:
            boulder.draw(surface, camx, camy)
        for gear in self.gears:
            gear.draw(surface, camx, camy)
        for bridge in self.bridges:
            bridge.draw(surface, camx, camy)

        self.door.draw(surface, camx, camy)
        self.chaser.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
