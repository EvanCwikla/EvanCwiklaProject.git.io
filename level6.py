# levels/level6.py
import pygame
from settings import *
from levels.level_base import Level
from game_objects import Player, Door, Bridge

# --- NEW: Braided Path Layout ---
# W = Wall (Solid Platform)
# S = Player Start
# E = Exit Door
# 1 = Bridge Type 1 (Very Slow, 5s on / 2s off)
# 2 = Bridge Type 2 (Alternating, 3s on / 1s off)
# ' ' = Empty Space (Abyss/Fall)
LEVEL6_MAP = [
    "WWW                                    ",
    "WSW  1111                              ",
    "WWW  1  1                              ",
    "WWW111  111WWW222222W222222W           ",
    "                           1           ",
    "        WWWWWW             2           ",
    "        2    2       1WWW121           ",
    "        2    2      11                 ",
    "        2    2     11                  ",
    "        2    2    11                   ",
    "     WWWW    WWWW11                    ",
    "     2                                 ",
    "     2                                 ",
    "     W1111111111111111111111111111111W ",
    "                                     W ",
    "       WWW11111111111111WWW2222  2222W ",
    "       2                      2222     ",
    "       2 222 222                    WWW",
    "       222 2W2 222WWW111111111111111WEW",
    "                                    WWW",
]


class Level6(Level):
    def __init__(self):
        super().__init__()

        self.grid_h = len(LEVEL6_MAP)
        self.grid_w = len(LEVEL6_MAP[0])

        self.bridges = []
        self._create_layout()

        self.door.locked = False  # The challenge is timing

    def _create_layout(self):
        """Creates the maze layout based on the LEVEL6_MAP."""
        self.walls = set()

        for y, row in enumerate(LEVEL6_MAP):
            for x, char in enumerate(row):
                pos = (x, y)
                if char == 'W':
                    self.walls.add(pos)
                elif char == 'S':
                    self.player = Player(x, y)
                    self.walls.add(pos)  # Add a solid wall under the player
                elif char == 'E':
                    self.door = Door(x, y)
                    self.walls.add(pos)  # Add a solid wall under the door
                elif char == '1':
                    # Type 1: VERY Slow and steady
                    # 5 seconds ON, 2 seconds OFF (Very forgiving)
                    self.bridges.append(Bridge(x, y, solid_time=FPS * 5, vanish_time=FPS * 2, offset=0))
                elif char == '2':
                    # Type 2: Fast, alternating
                    # 3 seconds ON, 1 second OFF (Still very generous)
                    offset = FPS if (x + y) % 2 == 0 else 0
                    self.bridges.append(Bridge(x, y, solid_time=FPS * 3, vanish_time=FPS, offset=offset))

    def get_obstacles(self):
        """
        Returns all impassable tiles. This includes:
        1. Vanished (non-solid) bridge tiles.
        2. Empty ' ' abyss tiles.
        """
        obstacles = set()

        for bridge in self.bridges:
            if not bridge.is_solid:
                obstacles.add((bridge.x, bridge.y))

        # Add all empty spaces (' ') from the map as permanent obstacles
        for y, row in enumerate(LEVEL6_MAP):
            for x, char in enumerate(row):
                if char == ' ':
                    obstacles.add((x, y))

        return obstacles

    def handle_event(self, event):
        pass  # Player movement is handled in update()

    def update(self):
        """Update player movement and the state of all bridges."""
        # Update all bridges first to determine where the player can move
        for bridge in self.bridges:
            bridge.update()

        # Update player movement based on the *current* obstacle map
        self.player.update(self.get_obstacles())

        # Check for win condition
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 6 Complete!")
            self.is_complete = True

    def draw(self, surface):
        """Draws the maze, bridges, and player."""
        # Camera follows player
        camx = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        camy = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))

        surface.fill(BLACK)

        # Draw solid 'W' platforms
        for (x, y) in self.walls:
            if camx <= x < camx + VIEW_W and camy <= y < camy + VIEW_H:
                pygame.draw.rect(surface, GRAY, ((x - camx) * TILE, (y - camy) * TILE, TILE, TILE))

        # Draw bridges
        for bridge in self.bridges:
            if camx <= bridge.x < camx + VIEW_W and camy <= bridge.y < camy + VIEW_H:
                bridge.draw(surface, camx, camy)

        # Draw player and door (which are on top of wall tiles)
        self.door.draw(surface, camx, camy)
        self.player.draw(surface, camx, camy)
