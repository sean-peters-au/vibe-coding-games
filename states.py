# states.py
import pygame
import sys
import config
# Need imports for entities, modifiers used in the logic moved here
from entities import Enemy, Tower, Projectile, CannonTower, CannonProjectile, BaseProjectile, Effect, IceProjectile
from modifiers import SlowModifier
import math

class GameState:
    """Base class for different game states (e.g., Menu, Playing, GameOver)."""
    def __init__(self, game):
        self.game = game # Reference to the main Game object

    def handle_events(self, events):
        """Handle input events specific to this state."""
        raise NotImplementedError

    def update(self, dt):
        """Update game logic for this state."""
        raise NotImplementedError

    def draw(self, screen):
        """Draw elements specific to this state."""
        raise NotImplementedError

    def enter_state(self):
        """Code to run when entering this state."""
        pass

    def exit_state(self):
        """Code to run when exiting this state."""
        pass


class PlayingState(GameState):
    """The main state where the core tower defense gameplay happens."""
    def handle_events(self, events):
        for event in events:
            # Handle QUIT event globally? Or per state?
            # if event.type == pygame.QUIT:
            #     self.game.running = False 
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE:
                      self.game.running = False # For now, Esc quits game
                      # Later: transition to PauseState or MenuState
                 if event.key == pygame.K_SPACE and not self.game.wave_manager.is_wave_active():
                      self.game.wave_manager.start_next_wave()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_pos = event.pos
                    # --- UI Panel Click Handling ---
                    ui_clicked = self.game.ui_panel.handle_click(mouse_pos)
                    # --- Game Area Click Handling ---
                    if not ui_clicked and mouse_pos[0] < config.GAME_AREA_WIDTH:
                         self._handle_place_tower(mouse_pos)

    def _handle_place_tower(self, mouse_pos):
        """Logic for placing a tower (moved from Game class)."""
        grid_x, grid_y = mouse_pos[0] // config.TILE_SIZE, mouse_pos[1] // config.TILE_SIZE
        selected_tower_key = self.game.ui_panel.get_selected_tower_key()

        if selected_tower_key:
            selected_data = self.game.data_manager.get_tower_data(selected_tower_key)
            if selected_data:
                tower_cost = selected_data.get("cost", 9999)
                if self.game.player_money >= tower_cost:
                    if self.game.game_map.place_tower(grid_x, grid_y):
                        TowerClass = self.game.data_manager.get_tower_class(selected_tower_key)
                        if TowerClass:
                            tower = TowerClass(grid_x, grid_y, asset_manager=self.game.asset_manager, data_manager=self.game.data_manager)
                            self.game.towers.add(tower)
                            self.game.player_money -= tower.cost
                            place_sound = self.game.asset_manager.load_sound(config.TOWER_PLACE_SOUND)
                            self.game.asset_manager.play_sound(place_sound)
                        else:
                            print(f"Error: Class not found for key '{selected_tower_key}'")
                    else:
                        print("Cannot place tower here.")
                        error_sound = self.game.asset_manager.load_sound(config.ERROR_SOUND)
                        self.game.asset_manager.play_sound(error_sound)
                else:
                    print("Not enough money!")
                    error_sound = self.game.asset_manager.load_sound(config.ERROR_SOUND)
                    self.game.asset_manager.play_sound(error_sound)
            else:
                print(f"Error: No data found for selected tower '{selected_tower_key}'")
        else:
            print("No tower type selected in UI.")

    def update(self, dt):
        """Update game logic (moved from Game class)."""
        # Update Managers
        self.game.wave_manager.update(dt, self.game.game_map, self.game.enemies)

        # Update Entities
        enemies_reached_end = []
        for enemy in self.game.enemies:
            if enemy.update(dt):
                enemies_reached_end.append(enemy)
                self.game.player_health -= 1

        # Remove enemies that reached the end
        for enemy in enemies_reached_end:
            enemy_data = self.game.data_manager.get_enemy_data(enemy.type_key)
            if enemy_data and enemy_data.get("reach_end_sound"):
                reach_sound = self.game.asset_manager.load_sound(enemy_data["reach_end_sound"])
                self.game.asset_manager.play_sound(reach_sound)
            self.game.enemies.remove(enemy)

        self.game.towers.update(dt, self.game.enemies, self.game.projectiles)
        self.game.projectiles.update(dt, self.game.enemies)
        self.game.effects.update(dt)

        # --- Projectile Collision Handling ---
        self._handle_collisions()

        # Check Game Over state change
        if self.game.player_health <= 0:
            print("Game Over condition met!")
            # In a full state machine, we'd transition:
            # self.game.change_state(GameOverState(self.game))
            self.game.running = False # For now, just quit

        # --- Check for Enemy Kills and Award Money ---
        for enemy in list(self.game.enemies.sprites()):
            if not enemy.alive():
                # Potential issue: If multiple projectiles kill enemy in same frame, might award multiple times.
                # Need to ensure reward happens only once per enemy death.
                # Add a simple check or flag?
                if not hasattr(enemy, '_awarded') or not enemy._awarded:
                     self.game.player_money += enemy.reward
                     print(f"Enemy {enemy.type_key} killed! +{enemy.reward} money.")
                     enemy._awarded = True # Mark as awarded
                # Enemy is removed later or by kill()

        # Check Wave End
        if self.game.wave_manager.is_wave_active() and self.game.wave_manager.is_wave_complete() and len(self.game.enemies) == 0:
            print(f"Wave {self.game.wave_manager.current_wave_number} cleared!")
            self.game.wave_manager.end_wave()

    def _handle_collisions(self):
        """Handles collisions (moved from Game class)."""
        enemy_hits = pygame.sprite.groupcollide(self.game.enemies, self.game.projectiles, False, False)
        projectiles_to_kill = []
        for enemy, projectiles_hit in enemy_hits.items():
            if not enemy.alive(): continue
            for projectile in projectiles_hit:
                if projectile in projectiles_to_kill: continue
                should_kill = projectile.on_hit(enemy, self.game.enemies, self.game.effects)
                if should_kill:
                    projectiles_to_kill.append(projectile)
                if not enemy.alive():
                    break
        for projectile in projectiles_to_kill:
            projectile.kill()

    def draw(self, screen):
        """Draw game elements for the playing state."""
        # Background / Map
        screen.fill(config.BLACK)
        self.game.game_map.draw(screen)

        # Entities
        self.game.towers.draw(screen)
        for enemy in self.game.enemies:
            enemy.draw(screen)
        self.game.projectiles.draw(screen)
        self.game.effects.draw(screen)

        # Draw UI
        self.game.ui_panel.draw(
            screen,
            self.game.player_health,
            self.game.player_money,
            self.game.wave_manager.current_wave_number,
            self.game.wave_manager.is_wave_active()
        )