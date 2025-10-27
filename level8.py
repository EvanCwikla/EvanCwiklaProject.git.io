# levels/level8.py
import pygame
from settings import *
from levels.level_base import Level
from game_objects import (Player, Door, Boulder, PressurePlate, Bridge, 
                          Gear, Mirror, ChaserEnemy)

# --- Helper classes (copied from Level 3) ---
class LightBeam:
    """Manages the light beam for the final puzzle."""
    def __init__(self, source, mirrors, door):
        self.source = source
        self.mirrors = mirrors
        self.door = door
        self.path = []
        self.is_active = False
        self.grid_w, self.grid_h = GRID_W, GRID_H # Default bounds

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
            x += dx; y += dy
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
                    
            if not mirror_hit and not (0 < x < self.grid_w and 0 < y < self.grid_h):
                break

    def draw(self, surf, camx, camy):
        if not self.is_active:
            return
        for (x, y) in self.path:
            rect = ((x-camx)*TILE + TILE//4, (y-camy)*TILE + TILE//4, TILE//2, TILE//2)
            pygame.draw.rect(surf, YELLOW, rect)

# --- Level 8 Map ---
LEVEL8_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "WS              M B   P                       W",
    "WWWWWWWWWWWW    WWWWWWWWWWWWWW    WWWWWWWWWW  W",
    "W  g  g  g  W    W B       P  W    W  M       W",
    "W  g     g  W    W       WWWWWW    WWWWWWWWWW  W",
    "W  g  g  g  W    W B       P  W    W           W",
    "WWWWWWWWWWWW    WWWWWWWWWWWWWW    W           W",
    "W M             W C               W           W",
    "W               W                 W           W",
    "WWWWWWWWWWWW    WWWWWWWWWWWWWW    WWWWWWWWWW  W",
    "WbbbbbbbbbbW    W  g  g  g   W    W           W",
    "WbbbbbbbbbbW    W  g     g   W    W           W",
    "WbbbbbbbbbbW    W  g  g  g   W    W L       E W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

class Level8(Level):
    def __init__(self):
        super().__init__()
        self.grid_h = len(LEVEL8_MAP)
        self.grid_w = len(LEVEL8_MAP[0])
        
        self.move_cooldown = 8 
        self.move_timer = 0
        
        self.boulders = []
        self.plates = []
        self.bridges = []
        self.gears = []
        self.mirrors = []
        self.light_source_pos = (0,0)
        
        self._create_layout()
        
        self.chaser = ChaserEnemy(self.chaser_start_pos[0], self.chaser_start_pos[1])
        
        self.beam = LightBeam(self.light_source_pos, self.mirrors, self.door)
        self.beam.grid_w, self.beam.grid_h = self.grid_w, self.grid_h

    def _create_layout(self):
        """Parses the LEVEL8_MAP to create all game objects."""
        self.walls = set()
        for y, row in enumerate(LEVEL8_MAP):
            for x, char in enumerate(row):
                pos = (x, y)
                if char == 'W': self.walls.add(pos)
                elif char == 'S': self.player = Player(x, y)
                elif char == 'E': self.door = Door(x, y)
                elif char == 'C': self.chaser_start_pos = pos
                elif char == 'B': self.boulders.append(Boulder(x, y))
                elif char == 'P': self.plates.append(PressurePlate(x, y))
                elif char == 'M': self.mirrors.append(Mirror(x, y, "/"))
                elif char == 'L': self.light_source_pos = (x, y, -1, -1) # Source at (x,y) aiming Up-Left
                elif char == 'b': self.bridges.append(Bridge(x,y, FPS*2, FPS*2, (x+y)%2 * FPS))
                elif char == 'g': self.gears.append(Gear(x, y, 2, (x%2)+1))

    def get_obstacles(self):
        """Get all 'hard' obstacles (walls, hazards)."""
        obstacles = self.walls.copy()
        for bridge in self.bridges:
            if not bridge.is_solid: obstacles.add((bridge.x, bridge.y))
        for gear in self.gears: 
            obstacles.update(gear.get_hazard_tiles())
            obstacles.add(gear.get_axle_tile()) # Axle is an obstacle
        
        # NOTE: Boulders and Mirrors are NOT in this list
        # Boulders are handled by push logic
        # Mirrors can be walked up to
        return obstacles

    def handle_event(self, event):
        """Handle player interactions (rotating mirrors)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Try to interact with a mirror
                for mirror in self.mirrors:
                    # Check if player is standing on or *next to* the mirror
                    if abs(self.player.x - mirror.x) <= 1 and abs(self.player.y - mirror.y) <= 1:
                        mirror.rotate()
                        self.beam.update() # Recalculate beam on rotate
                        break

    def update(self):
        # --- Player Movement (Press-per-move) ---
        if self.move_timer > 0: self.move_timer -= 1
        if self.move_timer == 0:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]: dx = -1
            elif keys[pygame.K_RIGHT]: dx = 1
            elif keys[pygame.K_UP]: dy = -1
            elif keys[pygame.K_DOWN]: dy = 1
            if dx != 0 or dy != 0:
                self.try_move_player(dx, dy)
                self.move_timer = self.move_cooldown

        # --- Update all objects ---
        for bridge in self.bridges: bridge.update()
        for gear in self.gears: gear.update()
        
        # --- Update Chaser ---
        # The chaser needs a *different* obstacle list that includes boulders/mirrors
        chaser_obstacles = self.get_obstacles() # Get hard obstacles
        chaser_obstacles.update({(b.x, b.y) for b in self.boulders})
        chaser_obstacles.update({(m.x, m.y) for m in self.mirrors})
        if self.chaser.update(self.player, chaser_obstacles) == "reset":
            print("Caught by the chaser! Resetting level.")
            self.__init__()
            return

        # --- Check Hazards ---
        all_hazards = set()
        for gear in self.gears: 
            all_hazards.update(gear.get_hazard_tiles())
            all_hazards.add(gear.get_axle_tile())
        if (self.player.x, self.player.y) in all_hazards:
            print("Hit by gear! Resetting level.")
            self.__init__()
            return

        # --- Puzzle Logic (Plates) ---
        all_plates_active = True
        boulder_pos = {(b.x, b.y) for b in self.boulders}
        for plate in self.plates:
            if (plate.x, plate.y) in boulder_pos: plate.is_active = True
            else: plate.is_active = False; all_plates_active = False
        
        # --- Puzzle Logic (Light Beam) ---
        if all_plates_active and not self.beam.is_active:
            print("All plates active! Light beam is on!")
            self.beam.is_active = True
        
        if self.beam.is_active:
            self.beam.update() # Update beam path
        
        # --- Win Condition ---
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 8 Complete! YOU WIN!")
            self.is_complete = True

    def try_move_player(self, dx, dy):
        """The correct movement logic for pushing boulders."""
        target_x, target_y = self.player.x + dx, self.player.y + dy

        # Get all obstacles that *cannot* be pushed
        hard_obstacles = self.get_obstacles()
        mirror_positions = {(m.x, m.y) for m in self.mirrors}
        boulder_positions = {(b.x, b.y) for b in self.boulders}

        # Case 1: Target is a hard wall, hazard, or mirror
        if (target_x, target_y) in hard_obstacles or (target_x, target_y) in mirror_positions:
            return # Blocked
            
        # Case 2: Target is a boulder
        if (target_x, target_y) in boulder_positions:
            boulder_target_x = target_x + dx
            boulder_target_y = target_y + dy
            
            # Check space *behind* the boulder
            # Is it a hard obstacle, another boulder, or a mirror?
            if (boulder_target_x, boulder_target_y) in hard_obstacles or \
               (boulder_target_x, boulder_target_y) in boulder_positions or \
               (boulder_target_x, boulder_target_y) in mirror_positions:
                return # Blocked
            else:
                # Move both boulder and player
                for b in self.boulders: # Find the boulder and move it
                    if (b.x, b.y) == (target_x, target_y):
                        b.x = boulder_target_x
                        b.y = boulder_target_y
                        break
                self.player.x, self.player.y = target_x, target_y
                return

        # Case 3: Target is empty space
        self.player.x, self.player.y = target_x, target_y

    def draw(self, surface):
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))
        
        surface.fill(BLACK)
        
        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x-camx)*TILE, (y-camy)*TILE, TILE, TILE))

        for plate in self.plates: plate.draw(surface, camx, camy)
        for bridge in self.bridges: bridge.draw(surface, camx, camy)
        for gear in self.gears: gear.draw(surface, camx, camy)
        
        self.beam.draw(surface, camx, camy) # Draw beam under boulders/mirrors
        
        for mirror in self.mirrors: mirror.draw(surface, camx, camy)
        for boulder in self.boulders: boulder.draw(surface, camx, camy)
        
        self.door.draw(surface, camx, camy)
        self.chaser.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
