"""
Temple Ruins Prototype (PyGame)
- Grid-based prototype implementing 8 levels of puzzles + hazards.
- Arrow keys to move on grid (one tile per key press).
- SPACE to interact/pull/rotate (context-sensitive).
"""

import pygame
import sys
import random
from collections import deque

pygame.init()

# --- CONFIG ---
TILE = 40
GRID_W, GRID_H = 20, 15   # 20x15 tiles -> 800x600
WIDTH, HEIGHT = TILE * GRID_W, TILE * GRID_H
FPS = 60
MOVE_COOLDOWN = 140  # ms between grid moves

# Colors
BG = (90, 74, 50)
WHITE = (255, 255, 255)
HUD_BG = (30, 30, 30)
KEY_COLORS = [(0, 200, 255), (0, 255, 100), (255, 200, 0), (255, 0, 200)]
SWITCH_COLOR = (60, 200, 60)
GATE_COLOR = (20, 90, 160)
MIRROR_COLOR = (190, 190, 255)
MIRROR_TARGET = (255, 255, 100)
MEMORY_COLOR = (255, 100, 255)
BOULDER_COLOR = (120, 70, 40)
PLATFORM_COLOR = (0, 150, 150)
GEAR_COLOR = (200, 200, 200)
HAZARD_RED = (200, 30, 30)
GUARDIAN_COLOR = (10, 10, 10)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Temple Ruins Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
bigfont = pygame.font.SysFont("Arial", 28)

# Helper functions
def grid_to_pix(pos):
    x, y = pos
    return x * TILE, y * TILE

def pix_to_grid(rect):
    return rect.x // TILE, rect.y // TILE

# --- Player (grid movement) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.grid_pos = list(pos)
        self.image = pygame.Surface((TILE-6, TILE-6))
        self.image.fill((230, 210, 80))
        self.rect = self.image.get_rect(topleft=(self.grid_pos[0]*TILE+3, self.grid_pos[1]*TILE+3))
        self.health = 5
        self.last_move = 0

    def try_move(self, dx, dy, obstacles, pushables):
        now = pygame.time.get_ticks()
        if now - self.last_move < MOVE_COOLDOWN:
            return
        target = (self.grid_pos[0] + dx, self.grid_pos[1] + dy)
        # bounds
        if not (0 <= target[0] < GRID_W and 0 <= target[1] < GRID_H):
            return
        # check pushables first: if there's a pushable at target, attempt to push
        push = None
        for pb in pushables:
            if tuple(pb.grid_pos) == target and pb.pushable:
                push = pb
                break
        if push:
            push_success = push.push(dx, dy, obstacles, pushables)
            if not push_success:
                return
        # check obstacles (walls, closed gates)
        for o in obstacles:
            if tuple(o.pos) == target and o.blocks:
                return
        # move
        self.grid_pos = [target[0], target[1]]
        self.rect.topleft = (self.grid_pos[0]*TILE+3, self.grid_pos[1]*TILE+3)
        self.last_move = now

    def update(self):
        pass

    def take_damage(self, amount=1):
        self.health -= amount
        print(f"Player damaged! Health={self.health}")
        if self.health <= 0:
            print("Game Over")
            pygame.quit()
            sys.exit()

# --- Generic object classes ---
class Obstacle:
    def __init__(self, pos, blocks=True):
        self.pos = tuple(pos)
        self.blocks = blocks
    def draw(self, surf):
        x,y = grid_to_pix(self.pos)
        r = pygame.Rect(x, y, TILE, TILE)
        pygame.draw.rect(surf, (60,60,60), r)

class Pushable:
    def __init__(self, pos, color=BOULDER_COLOR, pushable=True):
        self.grid_pos = list(pos)
        self.color = color
        self.pushable = pushable
    def push(self, dx, dy, obstacles, pushables):
        target = (self.grid_pos[0]+dx, self.grid_pos[1]+dy)
        # bounds
        if not (0 <= target[0] < GRID_W and 0 <= target[1] < GRID_H):
            return False
        # can't move into obstacle or another pushable
        for o in obstacles:
            if tuple(o.pos) == target and o.blocks:
                return False
        for pb in pushables:
            if pb is not self and tuple(pb.grid_pos) == target:
                return False
        self.grid_pos = [target[0], target[1]]
        return True
    def draw(self, surf):
        x,y = grid_to_pix(self.grid_pos)
        r = pygame.Rect(x+4, y+4, TILE-8, TILE-8)
        pygame.draw.rect(surf, self.color, r)

# --- Hazard classes ---
class MovingBlock(Pushable):
    def __init__(self, pos, path, speed=400):
        super().__init__(pos, color=(130,80,200), pushable=False)
        self.path = list(path)  # list of grid positions
        self.idx = 0
        self.dir = 1
        self.last = pygame.time.get_ticks()
        self.speed = speed
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last >= self.speed:
            self.idx += self.dir
            if self.idx >= len(self.path): 
                self.idx = len(self.path)-2
                self.dir = -1
            if self.idx < 0:
                self.idx = 1
                self.dir = 1
            self.grid_pos = list(self.path[self.idx])
            self.last = now

class FallingStalactite:
    def __init__(self, pos, delay=1500):
        self.spawn = tuple(pos)
        self.pos = tuple(pos)
        self.falling = False
        self.last = pygame.time.get_ticks()
        self.delay = delay
        self.y = pos[1]
    def update(self):
        now = pygame.time.get_ticks()
        if not self.falling and now - self.last >= self.delay:
            self.falling = True
            self.last = now
        if self.falling:
            self.y += 0.8  # pixel fall, not grid, faster feel
            if self.y > GRID_H:
                # reset
                self.y = self.spawn[1]
                self.falling = False
                self.last = now + 800
    def draw(self, surf):
        x = self.spawn[0]*TILE + TILE//2
        y = int(self.y * TILE) + 6
        pygame.draw.polygon(surf, (170,170,170), [(x,y-18),(x-8,y),(x+8,y)])

class EnemyPatrol:
    def __init__(self, path, speed=300):
        self.path = list(path)
        self.idx = 0
        self.pos = list(self.path[0])
        self.dir = 1
        self.last = pygame.time.get_ticks()
        self.speed = speed
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last >= self.speed:
            self.idx += self.dir
            if self.idx >= len(self.path):
                self.idx = len(self.path)-2
                self.dir = -1
            if self.idx < 0:
                self.idx = 1
                self.dir = 1
            self.pos = list(self.path[self.idx])
            self.last = now
    def draw(self, surf):
        x,y = grid_to_pix(self.pos)
        r = pygame.Rect(x+6, y+6, TILE-12, TILE-12)
        pygame.draw.rect(surf, (220,100,100), r)
    def grid_pos(self):
        return tuple(self.pos)

class Guardian:
    def __init__(self, pos):
        self.pos = list(pos)
        self.last_move = 0
        self.speed = 220
    def update(self, player):
        now = pygame.time.get_ticks()
        if now - self.last_move < self.speed:
            return
        dx = player.grid_pos[0] - self.pos[0]
        dy = player.grid_pos[1] - self.pos[1]
        if abs(dx) > abs(dy):
            step = (1 if dx>0 else -1, 0)
        else:
            step = (0, 1 if dy>0 else -1)
        new = (self.pos[0]+step[0], self.pos[1]+step[1])
        if 0 <= new[0] < GRID_W and 0 <= new[1] < GRID_H:
            self.pos = [new[0], new[1]]
        self.last_move = now
    def draw(self, surf):
        x,y = grid_to_pix(self.pos)
        r = pygame.Rect(x+3, y+3, TILE-6, TILE-6)
        pygame.draw.rect(surf, GUARDIAN_COLOR, r)


# --- Level class (core) ---
class Level:
    def __init__(self, level_num, name, puzzle_type, difficulty, hazards):
        self.level_num = level_num
        self.name = name
        self.puzzle_type = puzzle_type
        self.difficulty = difficulty
        self.hazards_spec = hazards
        self.obstacles = []   # list of Obstacle
        self.pushables = []   # list of Pushable
        self.moving_hazards = []
        self.falling_hazards = []
        self.enemies = []
        self.guardian = None
        self.puzzle_objects = []  # list of dicts with positions / state
        self.gates = {}
        self.switches = {}
        self.targets = []
        self.memory_sequence = []
        self.memory_progress = 0
        self.timed_bridges = []
        self.gears = []
        self.objective_desc = ""
        self.setup_level()

    def add_wall_border(self):
        for x in range(GRID_W):
            self.obstacles.append(Obstacle((x,0)))
            self.obstacles.append(Obstacle((x,GRID_H-1)))
        for y in range(GRID_H):
            self.obstacles.append(Obstacle((0,y)))
            self.obstacles.append(Obstacle((GRID_W-1,y)))

    def setup_level(self):
        # put border
        self.add_wall_border()
        # central player start will be provided externally
        if self.puzzle_type == "keys":
            # place keys in order and some moving blocks
            for i in range(self.difficulty + 1):
                pos = (3+i*3, 3 + (i%2)*4)
                self.puzzle_objects.append({"type":"key", "pos":pos, "collected":False, "order": i})
            # hazards: moving blocks with paths
            for i in range(self.difficulty):
                path = [(8+i,5),(10+i,5),(12+i,5)]
                mb = MovingBlock(path[0], path, speed=600 - i*80)
                self.moving_hazards.append(mb)
            self.objective_desc = f"Collect keys in order: {len(self.puzzle_objects)}"
        elif self.puzzle_type == "switches":
            # switches and gates
            # create two gates and two switches
            sw_positions = [(5,5),(7,5)]
            gate_positions = [(9,5),(11,5)]
            for i, s in enumerate(sw_positions):
                self.switches[tuple(s)] = False
                self.puzzle_objects.append({"type":"switch", "pos":s, "on":False})
            for i, g in enumerate(gate_positions):
                self.gates[tuple(g)] = True  # blocked when True
            self.objective_desc = "Activate switches and pass gates"
            # timed gates: will open on stepping switch and close after timeout if 'timed_gates' hazard present
        elif self.puzzle_type == "mirrors":
            # mirrors: movable pushables that must be placed onto targets
            for i in range(self.difficulty+1):
                self.pushables.append(Pushable((4+i*3, 6), color=MIRROR_COLOR))
                self.targets.append((12+i*2, 6))
            self.objective_desc = "Move mirrors onto glowing targets"
            if "falling_stalactites" in self.hazards_spec:
                for i in range(3):
                    fs = FallingStalactite((10+i, 3), delay=1000 + i*400)
                    self.falling_hazards.append(fs)
        elif self.puzzle_type == "memory":
            # memory tiles - make N tiles and a target sequence
            base_x, base_y = 6,6
            for i in range(self.difficulty+2):
                self.puzzle_objects.append({"type":"memory_tile","pos":(base_x+i, base_y), "lit":False})
            # generate random sequence
            seq = list(range(len(self.puzzle_objects)))
            random.shuffle(seq)
            self.memory_sequence = seq[:min(len(seq), 4 + self.difficulty)]
            self.memory_progress = 0
            self.objective_desc = f"Repeat sequence of length {len(self.memory_sequence)}"
            # enemy patrols
            patrol = EnemyPatrol([(2,9),(8,9),(12,9)], speed=450)
            self.enemies.append(patrol)
        elif self.puzzle_type == "boulders":
            # sokoban: push boulders onto pressure plates
            spots = [(10,6),(11,6),(12,6)]
            for i,pos in enumerate(spots[:self.difficulty+1]):
                self.pushables.append(Pushable((4+i*2, 8), color=BOULDER_COLOR))
                self.targets.append(pos)
            self.objective_desc = f"Push boulders onto plates ({len(self.targets)})"
            # rolling hazards
            self.moving_hazards.append(MovingBlock((15,2), [(15,2),(15,6),(15,10)], speed=350))
        elif self.puzzle_type == "timed_bridges":
            # platforms that toggle on/off
            for i in range(self.difficulty+2):
                pos=(6+i*2, 10)
                self.timed_bridges.append({"pos":pos, "active": (i%2==0), "last":pygame.time.get_ticks(), "interval": 900 - i*80})
            self.objective_desc = "Cross timed bridges to reach goal"
            self.moving_hazards.append(MovingBlock((3,3), [(3,3),(6,3),(9,3)], speed=480))
        elif self.puzzle_type == "gears":
            # gears: rotate to match target orientation (0-3)
            for i in range(self.difficulty+1):
                pos=(8+i*2, 5)
                self.gears.append({"pos":pos, "rot":random.randint(0,3), "target": random.randint(0,3)})
            self.objective_desc = "Rotate gears to match targets"
            # gear teeth hazard positions
            self.obstacles.append(Obstacle((12,7), blocks=False))  # decorative
        elif self.puzzle_type == "final_mix":
            # small combination of several mechanics
            # keys
            for i in range(2):
                self.puzzle_objects.append({"type":"key","pos":(4+i*3,4),"collected":False,"order":i})
            # a boulder to push
            self.pushables.append(Pushable((8,8), color=BOULDER_COLOR))
            # guardian enemy
            self.guardian = Guardian((15,10))
            self.objective_desc = "Collect keys and use boulder to reach switch while avoiding guardian"
        # add some random walls for visual interest (not blocking puzzle)
        for i in range(6):
            x = random.randint(2, GRID_W-4)
            y = random.randint(2, GRID_H-4)
            self.obstacles.append(Obstacle((x,y), blocks=False))

    # Checks for blocking obstacles that actually block (used for movement)
    def blocking_positions(self):
        return [o for o in self.obstacles if o.blocks] + [
            Pushable(p.grid_pos, pushable=False) for p in self.pushables if not p.pushable
        ] + [
            MovingBlock(m.grid_pos, [m.grid_pos]) for m in self.moving_hazards if not isinstance(m, MovingBlock)
        ]

    def update(self, player):
        # update hazards
        for mb in self.moving_hazards:
            mb.update()
        for fs in self.falling_hazards:
            fs.update()
        for ep in self.enemies:
            ep.update()
        if self.guardian:
            self.guardian.update(player)

        # memory tiles: blinking reveal at start of level for a few seconds
        # no extra logic here except input handling in main loop

        # timed bridges toggle
        for tb in self.timed_bridges:
            now = pygame.time.get_ticks()
            if now - tb["last"] > tb["interval"]:
                tb["active"] = not tb["active"]
                tb["last"] = now

        # check hazards collisions
        # moving blocks
        for mb in self.moving_hazards:
            if tuple(mb.grid_pos) == tuple(player.grid_pos):
                player.take_damage(1)
        # falling stalactites (if falling and in same column)
        for fs in self.falling_hazards:
            if fs.falling:
                # approximate collision: if player's column equal and vertical overlap
                px, py = player.grid_pos
                if px == fs.spawn[0]:
                    # y in pixels vs grid - approximate by comparing grid y to fs.y
                    if py >= int(fs.y):
                        player.take_damage(1)
            # else safe
        # enemies
        for ep in self.enemies:
            if tuple(ep.pos) == tuple(player.grid_pos):
                player.take_damage(1)
        if self.guardian and tuple(self.guardian.pos) == tuple(player.grid_pos):
            player.take_damage(2)

    def try_interact(self, player):
        # context-sensitive interaction triggered by SPACE
        # depending on puzzle_type
        px, py = player.grid_pos
        if self.puzzle_type == "keys":
            for k in self.puzzle_objects:
                if k["type"] == "key" and tuple(k["pos"]) == (px,py) and not k["collected"]:
                    # ensure order
                    smallest_uncollected = min([x["order"] for x in self.puzzle_objects if not x["collected"]], default=None)
                    if k["order"] == smallest_uncollected:
                        k["collected"] = True
                        print(f"Collected key {k['order']}")
                    else:
                        print("Wrong key order!")
        elif self.puzzle_type == "switches":
            # stepping on switch toggles gates (some gates may be timed)
            for s in self.puzzle_objects:
                if s["type"] == "switch" and tuple(s["pos"]) == (px,py):
                    s["on"] = not s["on"]
                    # toggle gates positions: if switch toggled, open next gate for a while if timed
                    for gpos in list(self.gates.keys()):
                        self.gates[gpos] = not self.gates[gpos]
                        # if timed gate hazard specified, set a timer to reclose
                        if "timed_gates" in self.hazards_spec and not self.gates[gpos]:
                            # open gate; schedule reclose
                            pygame.time.set_timer(pygame.USEREVENT + 1, 2200)
                    print("Switch toggled")
        elif self.puzzle_type == "mirrors":
            # push mirrors by moving into them (handled via movement), but allow space to select a mirror to rotate color for demo
            for pb in self.pushables:
                if tuple(pb.grid_pos) == (px,py):
                    # rotate color as simple interaction
                    pb.color = (random.randint(120,255), random.randint(120,255), random.randint(120,255))
                    print("Tuned mirror")
        elif self.puzzle_type == "memory":
            # check if stepping tile matches next in sequence
            for idx, t in enumerate(self.puzzle_objects):
                if tuple(t["pos"]) == (px,py):
                    if idx == self.memory_sequence[self.memory_progress]:
                        self.memory_progress += 1
                        print(f"Memory correct: {self.memory_progress}/{len(self.memory_sequence)}")
                    else:
                        print("Wrong memory tile! Resetting progress.")
                        self.memory_progress = 0
        elif self.puzzle_type == "boulders":
            # pushing boulders done via movement into them (handled in Player.try_move)
            pass
        elif self.puzzle_type == "timed_bridges":
            # nothing to interact with; player must traverse
            pass
        elif self.puzzle_type == "gears":
            # rotate gear under player if present
            for g in self.gears:
                if tuple(g["pos"]) == (px,py):
                    g["rot"] = (g["rot"] + 1) % 4
                    print(f"Rotated gear at {g['pos']} to {g['rot']}")
        elif self.puzzle_type == "final_mix":
            # try interact with switch/gates or pushable
            for pb in self.pushables:
                if tuple(pb.grid_pos) == (px,py):
                    pb.color = (200,150,120)
                    print("Nudged boulder")

    def check_completed(self):
        # returns True if level objective is complete
        if self.puzzle_type == "keys":
            all_collected = all(k["collected"] for k in self.puzzle_objects if k["type"]=="key")
            return all_collected
        elif self.puzzle_type == "switches":
            # allow passing through gates if gates are open in at least some key positions; define completion as reaching right side
            # For prototype, consider completed if any gate is open and player has toggled a switch
            return any(s["on"] for s in self.puzzle_objects if s["type"]=="switch")
        elif self.puzzle_type == "mirrors":
            # completed when each target contains a pushable
            for tgt in self.targets:
                found = False
                for pb in self.pushables:
                    if tuple(pb.grid_pos) == tuple(tgt):
                        found = True
                if not found:
                    return False
            return True
        elif self.puzzle_type == "memory":
            return self.memory_progress >= len(self.memory_sequence)
        elif self.puzzle_type == "boulders":
            # all targets covered by pushables
            for tgt in self.targets:
                if not any(tuple(pb.grid_pos)==tuple(tgt) for pb in self.pushables):
                    return False
            return True
        elif self.puzzle_type == "timed_bridges":
            # reached the far right area (goal)
            # for prototype, check if any pushable is on far right tile
            return any(pb.grid_pos[0] > GRID_W - 4 for pb in self.pushables)
        elif self.puzzle_type == "gears":
            return all(g["rot"] == g["target"] for g in self.gears)
        elif self.puzzle_type == "final_mix":
            # keys collected and boulder moved to a switch area
            keys_ok = all(k["collected"] for k in self.puzzle_objects if k["type"]=="key")
            # boulder on some target near (12,8)
            boulder_ok = any(pb.grid_pos[0] >= 11 for pb in self.pushables)
            return keys_ok and boulder_ok
        return False

    def draw(self, surf):
        # draw background tiles
        surf.fill(BG)
        # draw grid lines lightly
        for x in range(0, WIDTH, TILE):
            pygame.draw.line(surf, (50,50,50), (x,0),(x,HEIGHT))
        for y in range(0, HEIGHT, TILE):
            pygame.draw.line(surf, (50,50,50), (0,y),(WIDTH,y))
        # draw obstacles
        for o in self.obstacles:
            if o.blocks:
                x,y = grid_to_pix(o.pos)
                r = pygame.Rect(x, y, TILE, TILE)
                pygame.draw.rect(surf, (80,80,80), r)
        # draw puzzle objects
        for obj in self.puzzle_objects:
            if obj["type"] == "key":
                x,y = grid_to_pix(obj["pos"])
                if not obj.get("collected", False):
                    r = pygame.Rect(x+8,y+8,TILE-16,TILE-16)
                    pygame.draw.rect(surf, KEY_COLORS[obj["order"] % len(KEY_COLORS)], r)
            elif obj["type"] == "switch":
                x,y = grid_to_pix(obj["pos"])
                color = SWITCH_COLOR if obj.get("on",False) else (80,160,80)
                pygame.draw.rect(surf, color, (x+6,y+6,TILE-12,TILE-12))
            elif obj["type"] == "memory_tile":
                x,y = grid_to_pix(obj["pos"])
                color = MEMORY_COLOR if obj.get("lit",False) else (120,30,120)
                pygame.draw.rect(surf, color, (x+6,y+6,TILE-12,TILE-12))
        # draw pushables
        for pb in self.pushables:
            pb.draw(surf)
        # draw moving hazards
        for mb in self.moving_hazards:
            x,y = grid_to_pix(mb.grid_pos)
            pygame.draw.rect(surf, (130,80,200), (x+6,y+6,TILE-12,TILE-12))
        # draw falling hazards
        for fs in self.falling_hazards:
            fs.draw(surf)
        # draw enemies
        for ep in self.enemies:
            ep.draw(surf)
        # draw timed bridges
        for tb in self.timed_bridges:
            x,y = grid_to_pix(tb["pos"])
            if tb["active"]:
                pygame.draw.rect(surf, PLATFORM_COLOR, (x+4,y+10,TILE-8, TILE-20))
        # gates
        for gpos, blocked in self.gates.items():
            x,y = grid_to_pix(gpos)
            color = GATE_COLOR if blocked else (30,200,200)
            if blocked:
                pygame.draw.rect(surf, color, (x+2,y+2,TILE-4,TILE-4))
            else:
                # show open gate as smaller highlight
                pygame.draw.rect(surf, (30,200,200), (x+TILE//4,y+TILE//4,TILE//2,TILE//2))
        # draw targets
        for t in self.targets:
            x,y = grid_to_pix(t)
            pygame.draw.rect(surf, MIRROR_TARGET, (x+10,y+10, TILE-20, TILE-20))
        # draw gears: show rotation tick and target
        for g in self.gears:
            x,y = grid_to_pix(g["pos"])
            rect = pygame.Rect(x+6,y+6,TILE-12,TILE-12)
            pygame.draw.rect(surf, GEAR_COLOR, rect)
            # draw a small mark for rotation
            cx, cy = x + TILE//2, y + TILE//2
            angle = g["rot"] * 90
            end = (cx + 10 * (1 if g["rot"] in (0,1) else -1), cy + 10 * (1 if g["rot"] in (0,3) else -1))
            pygame.draw.line(surf, (120,120,120), (cx,cy), end, 3)
            # draw target as tiny mark
            tx = x + TILE - 10
            ty = y + 6
            pygame.draw.circle(surf, (255,80,80), (tx,ty), 5)

        # guardian draw
        if self.guardian:
            self.guardian.draw(surf)

# --- Level definitions according to refined roadmap ---
def make_levels():
    return [
        Level(1, "Tutorial Labyrinth", "keys", 1, ["moving_blocks"]),
        Level(2, "Switches & Gates", "switches", 2, ["timed_gates"]),
        Level(3, "Mirror Path", "mirrors", 2, ["falling_stalactites"]),
        Level(4, "Memory Run", "memory", 3, ["enemy_patrols"]),
        Level(5, "Boulder Logic", "boulders", 3, ["rolling_hazards"]),
        Level(6, "The Bridge of Time", "timed_bridges", 4, ["falling_platforms"]),
        Level(7, "Pattern Locks", "gears", 4, ["gear_teeth"]),
        Level(8, "The Final Chamber", "final_mix", 6, ["guardian_enemy"]),
    ]

# --- Main Game ---
levels = make_levels()
current_idx = 0
player = Player((2,2))
all_sprites = pygame.sprite.Group(player)
level_start_pos = (2,2)

# helper to place player start per level (simple approach)
def place_player_for_level(idx):
    if idx == 0: return (2,2)
    if idx == 1: return (2,6)
    if idx == 2: return (2,5)
    if idx == 3: return (2,9)
    if idx == 4: return (2,8)
    if idx == 5: return (2,10)
    if idx == 6: return (2,4)
    if idx == 7: return (2,2)
    return (2,2)

# fancy: reveal memory sequence for a few seconds at level start
memory_reveal_time = 2200
level_reveal_start = pygame.time.get_ticks()
show_memory_reveal = False

def start_level(idx):
    global player, level_reveal_start, show_memory_reveal
    lvl = levels[idx]
    player.grid_pos = list(place_player_for_level(idx))
    player.rect.topleft = (player.grid_pos[0]*TILE+3, player.grid_pos[1]*TILE+3)
    level_reveal_start = pygame.time.get_ticks()
    show_memory_reveal = lvl.puzzle_type == "memory"
    # if memory, light tiles briefly
    if show_memory_reveal:
        for t in lvl.puzzle_objects:
            t["lit"] = True

start_level(current_idx)

running = True
last_key_pressed = None

while running:
    dt = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.USEREVENT + 1:
            # timed gate reclose event
            # For simplicity close all gates
            for gpos in list(levels[current_idx].gates.keys()):
                levels[current_idx].gates[gpos] = True
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                last_key_pressed = event.key
            elif event.key == pygame.K_SPACE:
                levels[current_idx].try_interact(player)
            elif event.key == pygame.K_r:
                # restart level
                start_level(current_idx)

    # handle discrete grid movement on keydown (not held)
    keys = pygame.key.get_pressed()
    if last_key_pressed:
        if last_key_pressed == pygame.K_UP:
            dx,dy = 0,-1
        elif last_key_pressed == pygame.K_DOWN:
            dx,dy = 0,1
        elif last_key_pressed == pygame.K_LEFT:
            dx,dy = -1,0
        elif last_key_pressed == pygame.K_RIGHT:
            dx,dy = 1,0
        else:
            dx,dy = 0,0
        # prepare obstacle list for movement blocking
        lvl = levels[current_idx]
        obstacles_for_movement = []
        for o in lvl.obstacles:
            if o.blocks:
                obstacles_for_movement.append(o)
        # add gates as blocking obstacles if blocked
        for gpos, blocked in lvl.gates.items():
            if blocked:
                obstacles_for_movement.append(Obstacle(gpos, blocks=True))
        # include moving hazards positions as blocks for pushing logic
        pushables_list = lvl.pushables
        player.try_move(dx, dy, obstacles_for_movement, pushables_list)
        last_key_pressed = None

    # update level hazards and systems
    levels[current_idx].update(player)

    # reveal memory tiles briefly at start
    if show_memory_reveal:
        now = pygame.time.get_ticks()
        if now - level_reveal_start > memory_reveal_time:
            show_memory_reveal = False
            for t in levels[current_idx].puzzle_objects:
                if t["type"] == "memory_tile":
                    t["lit"] = False

    # update moving hazards/dynamics for pushables etc.
    # (already inside level.update for moving blocks, enemies, etc.)

    # draw level
    levels[current_idx].draw(screen)
    all_sprites.draw(screen)

    # HUD
    hud = pygame.Surface((WIDTH, 80))
    hud.fill(HUD_BG)
    # text
    lvl = levels[current_idx]
    t1 = bigfont.render(f"Level {lvl.level_num}: {lvl.name}", True, WHITE)
    t2 = font.render(lvl.objective_desc, True, WHITE)
    t3 = font.render(f"Health: {player.health}     Level {current_idx+1}/{len(levels)}", True, WHITE)
    hud.blit(t1, (10,6))
    hud.blit(t2, (10,36))
    hud.blit(t3, (WIDTH-280, 10))
    screen.blit(hud, (0, HEIGHT - 80))

    # small indicator of puzzle progress
    if lvl.puzzle_type == "keys":
        collected = sum(1 for k in lvl.puzzle_objects if k.get("collected", False))
        prog = font.render(f"Keys: {collected}/{len(lvl.puzzle_objects)}", True, WHITE)
        screen.blit(prog, (10, HEIGHT - 50))
    if lvl.puzzle_type == "memory":
        prog = font.render(f"Memory progress: {lvl.memory_progress}/{len(lvl.memory_sequence)}", True, WHITE)
        screen.blit(prog, (10, HEIGHT - 50))

    pygame.display.flip()

    # check completion
    if levels[current_idx].check_completed():
        print(f"Level {levels[current_idx].level_num} complete!")
        current_idx += 1
        if current_idx >= len(levels):
            # game complete
            screen.fill(BG)
            msg = bigfont.render("All levels complete! Well done!", True, (240,240,240))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - msg.get_height()//2))
            pygame.display.flip()
            pygame.time.delay(3000)
            running = False
            break
        else:
            start_level(current_idx)

pygame.quit()
sys.exit()
