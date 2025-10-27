# game_objects.py
import pygame
import random
import math
from settings import *


# --- PLAYER CLASS (UPDATED) ---
class Player:
    """Represents the player character with continuous movement."""

    def __init__(self, x, y):
        self.x, self.y = x, y

        # --- New additions for continuous movement ---
        self.move_cooldown = 8  # How many frames to wait between moves. Lower is faster.
        self.move_timer = 0  # The current countdown timer.

    def update(self, obstacles):
        # First, count down the timer
        if self.move_timer > 0:
            self.move_timer -= 1

        # Only check for input if the cooldown timer is ready
        if self.move_timer == 0:
            # Get a dictionary of all keys currently being held down
            keys = pygame.key.get_pressed()

            # Check which arrow key is pressed and move accordingly
            moved = False
            if keys[pygame.K_LEFT]:
                self.move(-1, 0, obstacles)
                moved = True
            elif keys[pygame.K_RIGHT]:
                self.move(1, 0, obstacles)
                moved = True
            elif keys[pygame.K_UP]:
                self.move(0, -1, obstacles)
                moved = True
            elif keys[pygame.K_DOWN]:
                self.move(0, 1, obstacles)
                moved = True

            # If the player moved, reset the cooldown timer
            if moved:
                self.move_timer = self.move_cooldown

    def move(self, dx, dy, obstacles):
        """
        This method is now called by the new update method.
        It moves the player if the destination is not in the obstacles set.
        """
        next_x, next_y = self.x + dx, self.y + dy
        if (next_x, next_y) not in obstacles:
            self.x, self.y = next_x, next_y

    def draw(self, surf, cam_x, cam_y):
        """Draws the player on the screen."""
        pygame.draw.rect(surf, PLAYER_GREEN,
                         ((self.x - cam_x) * TILE, (self.y - cam_y) * TILE, TILE, TILE))

# --- GENERIC LEVEL OBJECTS ---
class Door:
    """A door that can be locked or unlocked."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.locked = True

    def draw(self, surf, cam_x, cam_y):
        color = BROWN if self.locked else BLUE
        pygame.draw.rect(surf, color,
                         ((self.x - cam_x) * TILE, (self.y - cam_y) * TILE, TILE, TILE))


class Key:
    """A key that can be collected by the player."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.collected = False

    def draw(self, surf, cam_x, cam_y):
        if not self.collected:
            pygame.draw.circle(surf, YELLOW,
                               ((self.x - cam_x) * TILE + TILE // 2,
                                (self.y - cam_y) * TILE + TILE // 2), TILE // 3)


class Switch:
    """A floor switch for puzzles."""

    def __init__(self, x, y, color, order_index, group_id):
        self.x, self.y = x, y
        self.color = color
        self.order_index = order_index
        self.group_id = group_id
        self.activated = False

    def draw(self, surf, cam_x, cam_y):
        c = self.color if not self.activated else WHITE
        pygame.draw.circle(surf, c,
                           ((self.x - cam_x) * TILE + TILE // 2,
                            (self.y - cam_y) * TILE + TILE // 2), TILE // 3)


class Mirror:
    """A mirror for the light beam puzzle that can be rotated."""

    def __init__(self, x, y, orientation="/"):
        self.x, self.y = x, y
        self.orientation = orientation  # Can be "/" or "\\"

    def rotate(self):
        self.orientation = "/" if self.orientation == "\\" else "\\"

    def draw(self, surf, camx, camy):
        rect = ((self.x - camx) * TILE, (self.y - camy) * TILE, TILE, TILE)
        pygame.draw.rect(surf, DARK_GRAY, rect, 2)
        font = pygame.font.SysFont(None, 24)
        text = font.render(self.orientation, True, WHITE)
        surf.blit(text, (rect[0] + 8, rect[1] + 4))


class Enemy:
    """An enemy that patrols a set path."""

    def __init__(self, x, y, path):
        self.x, self.y = x, y
        self.path = path  # A list of (x,y) coordinates to follow
        self.path_index = 0
        self.wait_timer = 0
        self.speed_timer = 0

    def update(self, player):
        """Updates the enemy's position and checks for player collision."""
        self.speed_timer += 1
        if self.speed_timer < 5:  # This slows the enemy down, moving 1 tile per 5 frames
            return None
        self.speed_timer = 0

        if self.wait_timer > 0:
            self.wait_timer -= 1
            return None

        target = self.path[self.path_index]
        if (self.x, self.y) == target:
            self.path_index = (self.path_index + 1) % len(self.path)
            target = self.path[self.path_index]
            self.wait_timer = 5  # Wait for 5 update cycles at the waypoint

        dx = target[0] - self.x
        dy = target[1] - self.y

        if dx != 0: self.x += dx // abs(dx)
        if dy != 0: self.y += dy // abs(dy)

        # If the player is caught, signal the level to reset
        if (self.x, self.y) == (player.x, player.y):
            return "reset"

        return None

    def draw(self, surf, camx, camy):
        """Draws the enemy on the screen."""
        rect = ((self.x - camx) * TILE, (self.y - camy) * TILE, TILE, TILE)
        pygame.draw.rect(surf, RED, rect)

class Boulder:
    """A boulder that can be pushed by the player."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def draw(self, surf, cam_x, cam_y):
        rect = ((self.x - cam_x) * TILE, (self.y - cam_y) * TILE, TILE, TILE)
        pygame.draw.rect(surf, (110, 80, 50), rect)  # A dark brown color

class PressurePlate:
    """A pressure plate that activates when a boulder is on it."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.is_active = False

    def draw(self, surf, cam_x, cam_y):
        rect = ((self.x - cam_x) * TILE, (self.y - cam_y) * TILE, TILE, TILE)
        # The plate glows green when active
        color = (0, 70, 0) if not self.is_active else (50, 255, 50)
        pygame.draw.rect(surf, color, rect)

class Bridge:
    """A bridge tile that appears and disappears on a timer."""
    def __init__(self, x, y, solid_time, vanish_time, offset=0):
        self.x, self.y = x, y
        self.solid_duration = solid_time  # How long it stays solid (in frames)
        self.vanish_duration = vanish_time # How long it stays vanished (in frames)
        self.timer = offset
        self.is_solid = offset <= 0 # If offset is 0, start solid

    def update(self):
        """Updates the bridge's timer and toggles its state."""
        self.timer -= 1
        if self.timer <= 0:
            self.is_solid = not self.is_solid
            # Reset timer to the appropriate duration for the new state
            self.timer = self.solid_duration if self.is_solid else self.vanish_duration

    def draw(self, surf, cam_x, cam_y):
        rect = ((self.x - cam_x) * TILE, (self.y - cam_y) * TILE, TILE, TILE)
        if self.is_solid:
            # Draw a solid, light-blue bridge
            pygame.draw.rect(surf, (150, 200, 255), rect)
        else:
            # Draw a faint outline to show where the bridge will be
            pygame.draw.rect(surf, (50, 70, 90), rect, 2) # The '2' means draw a 2px outline


class Gear:
    """
    A rotating gear that acts as a spinning hazard.
    The spokes are dangerous, and the axle (center) is also impassable.
    """

    def __init__(self, x, y, radius, speed):
        self.x, self.y = x, y  # Axle (center) position
        self.radius = radius
        self.speed = speed
        self.current_angle = 0.0
        self.is_rotating = True
        self.spoke_angles = [0, 90, 180, 270]  # 4 spokes

    def update(self):
        """Updates the gear's rotation."""
        if self.is_rotating:
            self.current_angle = (self.current_angle + self.speed) % 360

    def get_axle_tile(self):
        """Returns the safe center tile."""
        return (self.x, self.y)

    def get_hazard_tiles(self):
        """Returns a set of all tiles covered by the spinning spokes."""
        tiles = set()

        for angle_offset in self.spoke_angles:
            angle_deg = (self.current_angle + angle_offset) % 360
            angle_rad = math.radians(angle_deg)
            dx, dy = math.cos(angle_rad), math.sin(angle_rad)

            # Get all tiles along the spoke from center to radius
            for r in range(1, self.radius + 1):
                tx = round(self.x + dx * r)
                ty = round(self.y + dy * r)
                tiles.add((tx, ty))

        tiles.discard((self.x, self.y))  # The axle is handled separately
        return tiles

    def draw(self, surf, camx, camy):
        # 1. Draw hazard spokes
        for (tx, ty) in self.get_hazard_tiles():
            if camx <= tx < camx + VIEW_W and camy <= ty < camy + VIEW_H:
                rect = ((tx - camx) * TILE, (ty - camy) * TILE, TILE, TILE)
                pygame.draw.rect(surf, RED, rect)  # Spokes are always dangerous

        # 2. Draw axle (center tile)
        if camx <= self.x < camx + VIEW_W and camy <= self.y < camy + VIEW_H:
            axle_rect = ((self.x - camx) * TILE, (self.y - camy) * TILE, TILE, TILE)
            pygame.draw.rect(surf, DARK_GRAY, axle_rect)  # Axle is just a block


class ChaserEnemy:
    """An enemy that actively chases the player."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed_timer = 0
        self.move_cooldown = 12  # Moves slightly slower than the player

    def update(self, player, obstacles):
        """
        Updates the chaser's position using a simple pathfinding.
        Moves toward the player, checking obstacles.
        """
        self.speed_timer += 1
        if self.speed_timer < self.move_cooldown:
            return None
        self.speed_timer = 0

        if (self.x, self.y) == (player.x, player.y):
            return "reset"  # Player is caught

        dx = player.x - self.x
        dy = player.y - self.y

        # Try to move in the direction of the largest distance
        if abs(dx) > abs(dy):
            # Try to move horizontally
            move_x = dx // abs(dx) if dx != 0 else 0
            if (self.x + move_x, self.y) not in obstacles:
                self.x += move_x
            # If blocked, try to move vertically
            elif dy != 0:
                move_y = dy // abs(dy)
                if (self.x, self.y + move_y) not in obstacles:
                    self.y += move_y
        else:
            # Try to move vertically
            move_y = dy // abs(dy) if dy != 0 else 0
            if (self.x, self.y + move_y) not in obstacles:
                self.y += move_y
            # If blocked, try to move horizontally
            elif dx != 0:
                move_x = dx // abs(dx)
                if (self.x + move_x, self.y) not in obstacles:
                    self.x += move_x

        if (self.x, self.y) == (player.x, player.y):
            return "reset"  # Player is caught

    def draw(self, surf, camx, camy):
        rect = ((self.x - camx) * TILE, (self.y - camy) * TILE, TILE, TILE)
        # Draw a scarier-looking enemy
        pygame.draw.rect(surf, (255, 0, 100), rect)  # Bright Pink/Magenta
