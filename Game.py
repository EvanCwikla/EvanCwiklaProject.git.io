# main.py
import pygame
from settings import *
from levels.level1 import Level1
from levels.level2 import Level2
from levels.level3 import Level3
from levels.level4 import Level4
from levels.level5 import Level5
from levels.level6 import Level6
from levels.level7 import Level7
from levels.level8 import Level8


# --- Helper function to format time ---
def format_time(milliseconds):
    """Converts milliseconds into an MM:SS:MS string."""
    total_seconds = milliseconds // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    # Get two-digit milliseconds
    ms = (milliseconds % 1000) // 10

    return f"{minutes:02}:{seconds:02}:{ms:02}"


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Temple Ruins")
        self.clock = pygame.time.Clock()

        self.game_state = "MENU"  # Can be MENU, PLAYING, WON

        # --- NEW: Timer and Font setup ---
        self.start_time = 0
        self.game_timer_running = False
        self.final_time = 0
        # Use a common system font, size 30
        self.timer_font = pygame.font.SysFont(None, 30)
        self.menu_font = pygame.font.SysFont(None, 60)
        self.title_font = pygame.font.SysFont(None, 40)
        # --- END NEW ---

        # All available levels
        self.all_levels = [
            Level1(), Level2(), Level3(), Level4(),
            Level5(), Level6(), Level7(), Level8()
        ]
        self.current_level_index = 0
        self.current_level = self.all_levels[self.current_level_index]

        # Level transition
        self.transition_timer = 0
        self.transition_duration = FPS * 2  # 2 seconds

    def run(self):
        running = True
        while running:
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.game_state == "PLAYING":
                    # Only send events to the level if playing
                    if self.transition_timer == 0:
                        self.current_level.handle_event(event)
                elif self.game_state == "MENU":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.game_state = "PLAYING"
                            # --- NEW: Start the game timer ---
                            if not self.game_timer_running and self.current_level_index == 0:
                                self.start_time = pygame.time.get_ticks()
                                self.game_timer_running = True
                            # --- END NEW ---
                            self.transition_timer = self.transition_duration  # Show "Level 1"
                        if event.key == pygame.K_q:
                            running = False
                elif self.game_state == "WON":
                    if event.type == pygame.KEYDOWN:
                        running = False

            # --- Game Logic ---
            if self.game_state == "PLAYING":
                if self.transition_timer > 0:
                    self.transition_timer -= 1
                else:
                    self.current_level.update()

                if self.current_level.is_complete:
                    self.load_next_level()

            # --- Drawing ---
            self.screen.fill(BLACK)
            self.draw()  # Call the main draw method

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def load_next_level(self):
        if self.current_level_index < len(self.all_levels) - 1:
            self.current_level_index += 1
            self.current_level = self.all_levels[self.current_level_index]
            self.transition_timer = self.transition_duration
        else:
            # --- NEW: Stop timer on win ---
            if self.game_timer_running:
                self.game_timer_running = False
                self.final_time = pygame.time.get_ticks() - self.start_time
            # --- END NEW ---
            self.game_state = "WON"

    def draw(self):
        if self.game_state == "MENU":
            self.draw_main_menu()
        elif self.game_state == "WON":
            self.draw_win_screen()
        elif self.game_state == "PLAYING":
            if self.transition_timer > 0:
                # Show "Level X" text
                level_text = f"Level {self.current_level_index + 1}"
                text_surf = self.menu_font.render(level_text, True, WHITE)
                text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                self.screen.blit(text_surf, text_rect)
            else:
                # Draw the current level
                self.current_level.draw(self.screen)

            # --- NEW: Draw the running timer ---
            if self.game_timer_running:
                # Calculate elapsed time
                elapsed_time = pygame.time.get_ticks() - self.start_time
                time_str = format_time(elapsed_time)

                text_surf = self.timer_font.render(time_str, True, WHITE)
                # Blit to top-left corner
                self.screen.blit(text_surf, (10, 10))
            # --- END NEW ---

    def draw_main_menu(self):
        title_surf = self.menu_font.render("Temple Ruins", True, WHITE)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

        start_surf = self.title_font.render("Press SPACE to Start", True, GREEN)
        start_rect = start_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))

        quit_surf = self.title_font.render("Press Q to Quit", True, RED)
        quit_rect = quit_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        self.screen.blit(title_surf, title_rect)
        self.screen.blit(start_surf, start_rect)
        self.screen.blit(quit_surf, quit_rect)

    def draw_win_screen(self):
        title_surf = self.menu_font.render("YOU WIN!", True, GREEN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

        # --- NEW: Display Final Time ---
        time_str = f"Final Time: {format_time(self.final_time)}"
        time_surf = self.title_font.render(time_str, True, WHITE)
        time_rect = time_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        # --- END NEW ---

        quit_surf = self.title_font.render("Press any key to quit", True, WHITE)
        quit_rect = quit_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

        self.screen.blit(title_surf, title_rect)
        self.screen.blit(time_surf, time_rect)
        self.screen.blit(quit_surf, quit_rect)


if __name__ == "__main__":
    game = Game()
    game.run()

# --- Main Execution ---
if __name__ == "__main__":
    game = Game()
    game.run()
