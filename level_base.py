# levels/level_base.py

class Level:
    """
    This is a base class for all levels in the game.
    It provides a template for the essential functions that every level must have.
    The main game loop in main.py will call these methods on the currently active level.
    """

    def __init__(self):
        # A flag to signal to the main loop when the level is complete.
        self.is_complete = False

        # Every level should create its own player instance.
        self.player = None

        # Every level should have a set of wall coordinates for collision.
        self.walls = set()

    def handle_event(self, event):
        """
        Handles any user input (like key presses) for the level.
        This method will be implemented by each specific level class.
        """
        pass

    def update(self):
        """
        Updates the state of all objects in the level for a single frame.
        This includes puzzle logic, enemy movement, and checking win/loss conditions.
        This method will be implemented by each specific level class.
        """
        pass

    def draw(self, surface):
        """
        Draws all the elements of the level onto the provided screen surface.
        This method will be implemented by each specific level class.
        """
        pass

    def get_obstacles(self):
        """
        Returns a set of all grid coordinates that the player cannot move into.
        By default, this is just the walls, but levels can add things like
        closed gates or other temporary barriers.
        """
        return self.walls
