from settings import *

# Import all your level classes
from levels.level1 import Level1
from levels.level2 import Level2
from levels.level3 import Level3
from levels.level4 import Level4
from levels.level5 import Level5
from levels.level6 import Level6

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Temple Ruins")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 50)
        self.show_transition = False
        self.transition_timer = 0

        # A list of all level classes in order
        self.levels = [Level1, Level2, Level3, Level4, Level5, Level6]  # <-- ADDED THE NEW LEVELS
        self.current_level_index = 0
        self.load_current_level()

    def load_current_level(self):
        """ Loads the level corresponding to the current index. """
        if self.current_level_index < len(self.levels):
            level_class = self.levels[self.current_level_index]
            self.current_level = level_class()
            print(f"Loading Level {self.current_level_index + 1}...")
            self.show_transition = True
            self.transition_timer = FPS * 2  # Show transition for 2 seconds
        else:
            print("You have completed all levels! Congratulations!")
            self.quit_game()

    def run(self):
        """ The main game loop. """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if not self.show_transition:
                    self.current_level.handle_event(event)

            # --- Update ---
            if not self.show_transition:
                self.current_level.update()
            else:
                self.transition_timer -= 1
                if self.transition_timer <= 0:
                    self.show_transition = False

            # --- Check for level completion ---
            if self.current_level.is_complete:
                self.current_level_index += 1
                self.load_current_level()

            # --- Draw ---
            self.screen.fill(BLACK)
            self.current_level.draw(self.screen)
            if self.show_transition:
                self.draw_transition()

            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_transition(self):
        text = self.font.render(f"LEVEL {self.current_level_index + 1}", True, WHITE)
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        pygame.draw.rect(self.screen, BLACK, rect.inflate(20, 20))
        self.screen.blit(text, rect)

    def quit_game(self):
        pygame.quit()
        sys.exit()


# --- Main Execution ---
if __name__ == "__main__":
    game = Game()
    game.run()
