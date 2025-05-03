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
    def __init__(self, game):
        super().__init__(game)
        self.selected_tower_for_move = None
        self.original_drag_pos = None
        self.original_grid_pos = None
        self.drag_offset = (0, 0)

    def enter_state(self):
        """Called when entering the playing state."""
        print("Entering Playing State - Starting initial wave delay.")
        # Generate initial path, pass necessary args for potential auto-sell
        self.game.game_map.regenerate_path(self.game.towers, self)
        # Start delay timer
        self.game.wave_manager.end_wave() # Triggers timer start

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE:
                      self.game.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    # Check UI first
                    ui_clicked = self.game.ui_panel.handle_click(mouse_pos)
                    if ui_clicked: continue # Handled by UI, do nothing else

                    # Check Tower Click (for Move or Click Actions)
                    tower_clicked_handled = False
                    clicked_on_tower = None
                    for tower in self.game.towers:
                        if tower.rect.collidepoint(mouse_pos):
                            clicked_on_tower = tower
                            # Handle Gold Mine click
                            if hasattr(tower, 'on_click'):
                                if tower.on_click(self):
                                    tower_clicked_handled = True
                            # Handle initiating a move IF cooldown is ready
                            elif tower.can_move(): # Check if tower is movable
                                self.selected_tower_for_move = tower
                                self.original_drag_pos = tower.rect.center
                                self.original_grid_pos = (tower.grid_x, tower.grid_y)
                                self.drag_offset = (tower.rect.centerx - mouse_pos[0], tower.rect.centery - mouse_pos[1])
                                print(f"Dragging tower {tower.type_key}")
                                tower_clicked_handled = True
                            else:
                                print(f"Tower {tower.type_key} move on cooldown.")
                                # Play error/cooldown sound?
                                tower_clicked_handled = True # Still counts as handled click
                            break # Only interact with one tower
                        
                    # --- Game Area Click Handling (Placement) ---
                    if not ui_clicked and not tower_clicked_handled and mouse_pos[0] < config.GAME_AREA_WIDTH:
                         self._handle_place_tower(mouse_pos)
                
                elif event.button == 3: # Right click
                     mouse_pos = event.pos
                     # Check if clicking within game area
                     if mouse_pos[0] < config.GAME_AREA_WIDTH:
                          self._handle_sell_tower(mouse_pos)

            elif event.type == pygame.MOUSEMOTION:
                 if self.selected_tower_for_move:
                      # Update position while dragging
                      self.selected_tower_for_move.rect.center = (mouse_pos[0] + self.drag_offset[0], mouse_pos[1] + self.drag_offset[1])

            elif event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1: # Left mouse button up
                      if self.selected_tower_for_move: # If we were dragging a tower
                           tower = self.selected_tower_for_move
                           new_grid_x = mouse_pos[0] // config.TILE_SIZE
                           new_grid_y = mouse_pos[1] // config.TILE_SIZE
                           is_same_cell = (new_grid_x == self.original_grid_pos[0] and new_grid_y == self.original_grid_pos[1])
                           is_valid_placement = self.game.game_map.is_buildable(new_grid_x, new_grid_y)

                           # Allow dropping back in same cell or onto a buildable cell
                           if is_same_cell or is_valid_placement:
                                # If moved to a NEW valid cell
                                if not is_same_cell:
                                     # Free up old grid cell
                                     self.game.game_map.sell_tower(self.original_grid_pos[0], self.original_grid_pos[1])
                                     # Occupy new grid cell
                                     self.game.game_map.place_tower(new_grid_x, new_grid_y)
                                     # Update tower's internal grid position
                                     tower.grid_x = new_grid_x
                                     tower.grid_y = new_grid_y
                                     # Snap visual position to new grid center
                                     tower.x = new_grid_x * config.TILE_SIZE + config.TILE_SIZE // 2
                                     tower.y = new_grid_y * config.TILE_SIZE + config.TILE_SIZE // 2
                                     tower.rect.center = (tower.x, tower.y)
                                     # Reset cooldown AFTER successful move
                                     tower.reset_move_cooldown()
                                     print(f"Moved tower {tower.type_key} to ({new_grid_x}, {new_grid_y})")
                                     # Play move/place sound?
                                     place_sound = self.game.asset_manager.load_sound(config.TOWER_PLACE_SOUND)
                                     self.game.asset_manager.play_sound(place_sound)
                                else:
                                     # Snapped back to original position (same cell click/drop)
                                     tower.rect.center = self.original_drag_pos
                           else:
                                # Invalid drop location, snap back
                                print(f"Invalid move location ({new_grid_x}, {new_grid_y}), snapping back.")
                                tower.rect.center = self.original_drag_pos
                                # Play error sound?
                                error_sound = self.game.asset_manager.load_sound(config.ERROR_SOUND)
                                self.game.asset_manager.play_sound(error_sound)
                           
                           # Clear dragging state regardless of success
                           self.selected_tower_for_move = None
                           self.original_drag_pos = None
                           self.original_grid_pos = None
                           self.drag_offset = (0, 0)

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

    def _handle_sell_tower(self, mouse_pos):
        """Handles selling a tower at the clicked position."""
        grid_x, grid_y = mouse_pos[0] // config.TILE_SIZE, mouse_pos[1] // config.TILE_SIZE
        
        tower_to_sell = None
        for tower in self.game.towers:
            if tower.grid_x == grid_x and tower.grid_y == grid_y:
                tower_to_sell = tower
                break
        
        if tower_to_sell:
            # Check if tower can be sold (e.g. Gold Mine might be unsellable later)
            if hasattr(tower_to_sell, 'cost'): # Check if it has a cost attribute
                 refund_amount = int(tower_to_sell.cost * config.SELL_REFUND_RATIO)
                 # Update map first to make cell buildable
                 if self.game.game_map.sell_tower(grid_x, grid_y):
                      # Remove tower from group
                      tower_to_sell.kill() 
                      # Add refund
                      self.game.player_money += refund_amount
                      print(f"Sold {tower_to_sell.type_key} for {refund_amount} gold.")
                      # Play sound
                      sell_sound = self.game.asset_manager.load_sound(config.SELL_SOUND)
                      self.game.asset_manager.play_sound(sell_sound)
                 else:
                      print(f"Error: Failed to update map for selling tower at ({grid_x}, {grid_y})")
            else:
                 print(f"Cannot sell tower type {tower_to_sell.type_key} (no cost defined).")
        else:
             print(f"No tower found at ({grid_x}, {grid_y}) to sell.")

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

        # Check Wave End
        if self.game.wave_manager.is_wave_active() and self.game.wave_manager.is_wave_complete() and len(self.game.enemies) == 0:
            current_wave_num = self.game.wave_manager.current_wave_number
            print(f"Wave {current_wave_num} cleared!")
            
            # Grant wave completion reward
            wave_reward = self.game.wave_manager.get_current_wave_reward()
            if wave_reward > 0:
                 self.game.player_money += wave_reward
                 print(f"Wave Reward: +{wave_reward} gold!")
            
            # Regenerate path BEFORE ending wave, pass args for auto-sell
            self.game.game_map.regenerate_path(self.game.towers, self)
            self.game.wave_manager.end_wave()

    def _handle_collisions(self):
        """Handles collisions (moved from Game class)."""
        enemy_hits = pygame.sprite.groupcollide(self.game.enemies, self.game.projectiles, False, False)
        projectiles_to_kill = []
        for enemy, projectiles_hit in enemy_hits.items():
            if not enemy.alive(): continue
            for projectile in projectiles_hit:
                if projectile in projectiles_to_kill: continue

                # Delegate hit handling and get result
                should_kill, reward = projectile.on_hit(enemy, self.game.enemies, self.game.effects)

                # Award money immediately if returned
                if reward > 0:
                    self.game.player_money += reward
                    print(f"Awarded {reward} gold from hit.") # Debug

                if should_kill:
                    projectiles_to_kill.append(projectile)

                # If enemy died from this hit, no need for other projectiles to hit it this frame
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
            self.game.wave_manager.is_wave_active(),
            self.game.wave_manager.waiting_for_next_wave,
            self.game.wave_manager.between_waves_timer
        )