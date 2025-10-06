# levels/level2.py
import pygame
import time
from settings import *
from levels.level_base import Level
from game_objects import Player, Switch, Door


class Level2(Level):
    """
    Level 2: Switches & Gates.
    The player must activate switches in the correct sequence to open
    timed gates and reach the exit.
    """

    def __init__(self):
        super().__init__()
        self.grid_w, self.grid_h = 61, 20
        self.walls = set()
        self._carve_layout()

        self.gates = {
            "A": {(12, 9)}, "B": {(24, 9)}, "C": {(36, 9)},
        }

        self.switches = [
            Switch(4, 7, RED, 0, "A"), Switch(8, 11, GREEN, 1, "A"),
            Switch(16, 7, BLUE, 0, "B"), Switch(20, 11, YELLOW, 1, "B"),
            Switch(28, 7, RED, 0, "C"), Switch(32, 11, GREEN, 1, "C"),
        ]

        self.door = Door(48, 9)
        self.walls.discard((self.door.x, self.door.y))
        self.player = Player(4, 9)

        self.sequences = {"A": [0, 1], "B": [0, 1], "C": [0, 1]}
        self.current_orders = {"A": [], "B": [], "C": []}
        self.gates_open = {"A": False, "B": False, "C": False}
        self.timers = {"A": 0, "B": 0, "C": 0}

    def _carve_layout(self):
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                self.walls.add((x, y))

        def carve_rect(x1, y1, x2, y2):
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.walls.discard((x, y))

        carve_rect(2, 5, 10, 13)
        carve_rect(14, 5, 22, 13)
        carve_rect(26, 5, 34, 13)
        carve_rect(38, 5, 50, 13)
        carve_rect(10, 9, 14, 9)
        carve_rect(22, 9, 26, 9)
        carve_rect(34, 9, 38, 9)

    def get_obstacles(self):
        """Returns all impassable tiles, including walls and closed gates."""
        closed_gates = set().union(*[g for gid, g in self.gates.items() if not self.gates_open[gid]])
        return self.walls.union(closed_gates)

    def handle_event(self, event):
        """
        Handles player input. The arrow key logic has been removed.
        This method is now empty for this level.
        """
        pass

    def update(self):
        """Updates all puzzle logic and player movement for the level."""
        # --- NEW: Handle player's continuous movement ---
        self.player.update(self.get_obstacles())

        # --- Switch activation logic ---
        for s in self.switches:
            if (self.player.x, self.player.y) == (s.x, s.y) and not s.activated:
                s.activated = True
                group_id = s.group_id
                self.current_orders[group_id].append(s.order_index)

                current_seq = self.current_orders[group_id]
                target_seq = self.sequences[group_id]

                if current_seq == target_seq:
                    print(f"Gate {group_id} opened!")
                    self.gates_open[group_id] = True
                    self.timers[group_id] = time.time()
                elif not target_seq[:len(current_seq)] == current_seq:
                    print(f"Wrong order for Gate {group_id}, puzzle reset.")
                    self.current_orders[group_id] = []
                    for sw in self.switches:
                        if sw.group_id == group_id:
                            sw.activated = False

        # --- Timed gates logic ---
        for gid in self.gates_open:
            if self.gates_open[gid] and time.time() - self.timers[gid] > 15:
                print(f"Gate {gid} closed!")
                self.gates_open[gid] = False

        # --- Final door logic ---
        if self.gates_open["C"]:
            self.door.locked = False

        # --- Win condition ---
        if not self.door.locked and (self.player.x, self.player.y) == (self.door.x, self.door.y):
            print("Level 2 Complete!")
            self.is_complete = True

    def draw(self, surface):
        """Draws all level elements."""
        cam_x = max(0, min(self.player.x - VIEW_W // 2, self.grid_w - VIEW_W))
        cam_y = max(0, min(self.player.y - VIEW_H // 2, self.grid_h - VIEW_H))

        surface.fill(BLACK)
        for (x, y) in self.walls:
            if cam_x <= x < cam_x + VIEW_W and cam_y <= y < cam_y + VIEW_H:
                pygame.draw.rect(surface, DARK_GRAY, ((x - cam_x) * TILE, (y - cam_y) * TILE, TILE, TILE))

        for gid, gset in self.gates.items():
            if not self.gates_open[gid]:
                for (x, y) in gset:
                    if cam_x <= x < cam_x + VIEW_W and cam_y <= y < cam_y + VIEW_H:
                        pygame.draw.rect(surface, BROWN, ((x - cam_x) * TILE, (y - cam_y) * TILE, TILE, TILE))

        for s in self.switches: s.draw(surface, cam_x, cam_y)
        self.door.draw(surface, cam_x, cam_y)
        self.player.draw(surface, cam_x, cam_y)
