import pygame
import sys
import config
from map import GameMap
from entities import Projectile, CannonProjectile, IceProjectile, CoinShotProjectile
import math
from ui import UIPanel
import json
import os
# Import DataManager class
from game_data_manager import DataManager
from wave_manager import WaveManager
from modifiers import SlowModifier
from asset_manager import AssetManager
from states import GameState, PlayingState # Import states

# --- Game Class Definition ---
class Game:
    def __init__(self):
        """Initialize Pygame, load data, create screen and game objects."""
        # Initialize Pygame FIRST
        pygame.init()
        # Initialize Asset Manager (which initializes mixer)
        self.asset_manager = AssetManager()

        # --- Load Game Data via DataManager ---
        try:
            self.data_manager = DataManager() # Instantiate DataManager
        except (FileNotFoundError, json.JSONDecodeError, SystemExit) as e:
             print(f"Failed to initialize DataManager: {e}")
             sys.exit(1)

        # --- Preload Assets (replaces sound preloading) ---
        self.asset_manager.preload_assets()

        # --- End Load Game Data ---
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Tower Defense")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36) # Font for UI text
        self.small_font = pygame.font.SysFont(None, 24) # Smaller font for selection text
        self.ui_font = pygame.font.SysFont(None, 20) # Font for UI panel text
        self.status_font = pygame.font.SysFont(None, 28) # Font for status bar

        # Game state
        # Pass AssetManager to GameMap
        self.game_map = GameMap(config.GAME_AREA_WIDTH // config.TILE_SIZE, config.GRID_HEIGHT, self.asset_manager)
        self.enemies = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.player_money = config.STARTING_MONEY
        self.player_health = config.STARTING_HEALTH

        # Keep track of visual effects
        self.effects = pygame.sprite.Group()
        # selected_tower_type = Tower # Selection now handled by UI panel

        # Create Wave Manager (pass asset_manager and enemy_class_map)
        self.wave_manager = WaveManager(self.data_manager, self.asset_manager)

        # Create UI Panel (Needs DataManager and AssetManager)
        self.ui_panel = UIPanel(self.data_manager, start_y=50, font=self.ui_font, asset_manager=self.asset_manager)
        # self.tower_class_map = self.ui_panel.tower_class_map # No longer needed here

        self.running = True
        self.state_stack = [] # Use a stack for states (e.g., pause menu)
        self._init_starting_state()

        # --- Game State Variables ---
        self.projectile_class_map = {
            "Basic": Projectile,
            "Cannon": CannonProjectile,
            "Ice": IceProjectile,
            "CoinShot": CoinShotProjectile
        }

    def _init_starting_state(self):
        """Sets up the initial game state."""
        self.state_stack.append(PlayingState(self)) # Start in Playing state
        self.state_stack[-1].enter_state() # Call enter for the first state

    def get_current_state(self):
        return self.state_stack[-1] if self.state_stack else None

    def change_state(self, new_state):
        """Changes the current state (replaces the top of the stack)."""
        if self.state_stack:
            self.state_stack[-1].exit_state()
            self.state_stack.pop()
        self.state_stack.append(new_state)
        new_state.enter_state()

    def push_state(self, new_state):
        """Adds a new state on top (e.g., for pause menu)."""
        if self.state_stack:
            # Optionally pause previous state?
            pass
        self.state_stack.append(new_state)
        new_state.enter_state()

    def pop_state(self):
        """Removes the current state (e.g., exiting pause menu)."""
        if self.state_stack:
            self.state_stack[-1].exit_state()
            self.state_stack.pop()
        if self.state_stack:
            # Optionally resume previous state?
            pass
        else:
            # If stack is empty, maybe quit?
            self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            current_state = self.get_current_state()
            if not current_state:
                self.running = False # Exit if no state
                break

            # Get events once and pass them down
            events = pygame.event.get()
            # Handle global events like QUIT
            for event in events:
                 if event.type == pygame.QUIT:
                      self.running = False
            if not self.running: # Check if QUIT event set running to False
                 break

            current_state.handle_events(events)
            current_state.update(dt)
            current_state.draw(self.screen)
            # pygame.display.flip() is now called within state.draw or after loop?
            # Let's keep it here for now
            pygame.display.flip()

        pygame.quit()
        sys.exit()

# --- Main Execution ---
if __name__ == '__main__':
    game = Game()
    game.run() 