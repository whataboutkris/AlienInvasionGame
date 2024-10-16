import sys
import pygame as pg
import json
from colors import OFF_WHITE, DARK_GREY
from settings import Settings
from ship import Ship
from vector import Vector
from fleet import Fleet
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard
from event import Event
from barrier import Barriers
from sound import Sound


class AlienInvasion:
    def __init__(self):
        pg.init()   

        self.clock = pg.time.Clock()

        screen_info = pg.display.Info()
        #screen_width, screen_height = screen_info.current_w, screen_info.current_h

        self.settings = Settings()
        self.settings.w_h = (self.settings.scr_width, self.settings.scr_height)
        self.screen = pg.display.set_mode(self.settings.w_h)  # Edited this for bugs

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.sound = Sound()

        self.alien_lasers = pg.sprite.Group()  # Group to hold alien lasers

        self.ship = Ship(ai_game=self)
        self.fleet = Fleet(ai_game=self)  # Instantiate AlienFleet instead of Fleet
        self.ship.set_fleet(self.fleet)
        self.ship.set_sb(self.sb)
        self.barriers = Barriers(ai_game=self)

        pg.display.set_caption("Alien Invasion")

        # Load background images for menu, highscore and game
        self.menu_bg_image = pg.transform.scale(pg.image.load("images\menu_background.png"), (self.settings.w_h))
        self.game_bg_image = pg.transform.scale(pg.image.load("images\game_background.png"), (self.settings.w_h))
        self.highscore_bg_image = pg.transform.scale(pg.image.load("images\highscore_background.png"), (self.settings.w_h))

        # Start Alien Invasion in an inactive state.
        self.game_active = False
        self.showing_high_scores = False
        self.first = True

        # Buttons
        self.play_button = Button(self, "Play")
        self.high_scores_button = Button(self, "High Scores", y_offset=100)  # Offset the button vertically

        self.event = Event(self)

        # Set up title font and text {Used PNG here for aesthetics - kris}
        self.title_font = pg.font.SysFont(None, 72)
        #self.title_text = self.title_font.render("Alien Invasion", True, OFF_WHITE)

        # Load high scores from file
        self.high_scores = self.load_high_scores()

        

        # Load menu music
        self.menu_music_file = "sounds/menu_music.wav"  # Path to your menu music file
        pg.mixer.music.load(self.menu_music_file)

    def load_high_scores(self):
        """Load high scores from a file."""
        try:
            with open("high_scores.txt", "r") as file:
                return json.load(file)  # Load the scores from the JSON file
        except FileNotFoundError:
            return [0] * 5  # If the file doesn't exist, return default scores

    def save_high_scores(self):
        """Save the current high scores to a file."""
        with open("high_scores.txt", "w") as file:
            json.dump(self.high_scores, file)  # Save the scores in JSON format

    # Add a method to display the title
    #def draw_title(self): {Used PNG here for aesthetics - Kris}
        #title_rect = self.title_text.get_rect()
        #title_rect.centerx = self.screen.get_rect().centerx
        #title_rect.top = 100  # Positioning it near the top of the screen
        #self.screen.blit(self.title_text, title_rect)

    def draw_high_scores(self): 
        """Display the high scores on the screen."""
        self.screen.blit(self.highscore_bg_image, (0, 0))
        title_text = self.title_font.render("High Scores", True, OFF_WHITE)
        title_rect = title_text.get_rect(center=(600, 300))
        self.screen.blit(title_text, title_rect)

        # Display each high score
        font = pg.font.SysFont(None, 48)
        for i, score in enumerate(self.high_scores):
            score_text = font.render(f"{i + 1}. {score}", True, OFF_WHITE)
            score_rect = score_text.get_rect(center=(600, 360 + i * 50))
            self.screen.blit(score_text, score_rect)

    def game_over(self):
        print("Game over!") 
        self.sound.play_gameover()

        # Check if the current score is a high score
        if self.stats.score > min(self.high_scores):
            self.check_high_score(self.stats.score)

        # Set game to inactive, so it will return to the main menu
        self.game_active = False
        self.first = True  # Ensure the main menu and its music gets displayed again
        pg.mixer.music.load(self.menu_music_file)
        pg.mixer.music.play()

    def check_high_score(self, new_score):
        """Check if the new score is a high score and update the list."""
        if new_score > min(self.high_scores):
            self.high_scores.append(new_score)
            self.high_scores = sorted(self.high_scores, reverse=True)[:5]  # Keep only top 5
            self.save_high_scores()  # Save the updated high scores to disk

    def reset_game(self):
        self.stats.reset_stats()
        self.sb.prep_score_level_ships()
        self.game_active = True
        self.sound.play_background()

        self.ship.reset_ship()
        self.fleet.aliens.empty()
        self.fleet.create_fleet()  # Reset thew alien fleet
        self.alien_lasers.empty()
        pg.mouse.set_visible(True)

    def restart_game(self):
        self.game_active = False
        self.first = True
        self.play_button.reset_message("Play again? (q for quit)")
        self.reset_game()

    def run_game(self):
        self.finished = False
        self.first = True
        self.game_active = False

        pg.mixer.music.play() #play main menu music

        while not self.finished:
            self.finished = self.event.check_events()

            # If the game is active, update the game objects and display the screen
            if self.first or self.game_active:
                self.first = False
                self.screen.blit(self.game_bg_image, (0, 0))  # Draw game background
                self.ship.update()
                self.fleet.update()  # Update the entire fleet of aliens
                self.sb.show_score()
                self.barriers.update()

                remaining_aliens = len(self.fleet.aliens)
                total_aliens = self.fleet.total_aliens

                self.sound.adjust_music_speed(remaining_aliens, total_aliens)

                self.alien_lasers.update()

                if pg.sprite.spritecollideany(self.ship, self.alien_lasers):
                    self.ship.ship_hit()

                self.ship.lasers.update()
                for laser in self.ship.lasers.sprites():
                    laser.draw()

                for laser in self.alien_lasers.sprites():
                    laser.draw()

            # If not active, display the main menu or high scores
            if not self.game_active:
                if self.showing_high_scores:
                    self.draw_high_scores()  # Display high scores
                else:
                    self.screen.blit(self.menu_bg_image, (0, 0))  # Draw menu background
                    self.play_button.draw_button()
                    self.high_scores_button.draw_button()

            # Refresh the screen and regulate the game loop speed
            pg.display.flip()
            self.clock.tick(60)

        sys.exit()  # Exit the game after the main loop finishes

if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()