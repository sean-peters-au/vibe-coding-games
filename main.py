import pygame
import sys
import config
from map import GameMap
from entities import Enemy, Tower, Projectile, CannonTower, CannonProjectile
import math
from ui import UIPanel # Import the UI Panel

def main():
    pygame.init()

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36) # Font for UI text
    small_font = pygame.font.SysFont(None, 24) # Smaller font for selection text
    ui_font = pygame.font.SysFont(None, 20) # Font for UI panel text

    # Game state
    # Adjust map size to fit game area
    game_map = GameMap(config.GAME_AREA_WIDTH // config.TILE_SIZE, config.GRID_HEIGHT)
    enemies = pygame.sprite.Group()
    towers = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    player_money = config.STARTING_MONEY
    player_health = config.STARTING_HEALTH
    wave_number = 0
    last_spawn_time = 0
    enemies_in_wave = 10
    enemies_spawned_this_wave = 0
    wave_active = False
    # selected_tower_type = Tower # Selection now handled by UI panel

    # Create UI Panel
    ui_panel = UIPanel(start_y=50, font=ui_font)


    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0 # Delta time in seconds

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_SPACE and not wave_active: # Start next wave
                      wave_active = True
                      wave_number += 1
                      enemies_spawned_this_wave = 0
                      last_spawn_time = pygame.time.get_ticks() / 1000.0
                      enemies_in_wave = 5 + wave_number * 2
                 # Tower Selection Hotkeys (REMOVED)
                 # elif event.key == pygame.K_1:
                 #     selected_tower_type = Tower
                 #     print("Selected Basic Tower")
                 # elif event.key == pygame.K_2:
                 #     selected_tower_type = CannonTower
                 #     print("Selected Cannon Tower")

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_pos = event.pos

                    # --- UI Panel Click Handling ---
                    # Let the panel handle the click first
                    ui_clicked = ui_panel.handle_click(mouse_pos)

                    # --- Game Area Click Handling ---
                    # Only place tower if click was NOT in the UI panel
                    if not ui_clicked and mouse_pos[0] < config.GAME_AREA_WIDTH:
                        grid_x, grid_y = mouse_pos[0] // config.TILE_SIZE, mouse_pos[1] // config.TILE_SIZE

                        # Get selected tower type from the panel
                        selected_tower_type = ui_panel.get_selected_tower()

                        if selected_tower_type: # Ensure a tower type is actually selected
                             # Try placing the selected tower type
                             if player_money >= selected_tower_type.COST:
                                  if game_map.place_tower(grid_x, grid_y):
                                       tower = selected_tower_type(grid_x, grid_y)
                                       towers.add(tower)
                                       player_money -= tower.cost
                                  else:
                                       print("Cannot place tower here.")
                             else:
                                  print("Not enough money!")
                        else:
                             print("No tower type selected in UI.")


        # --- Game Logic ---

        # Enemy Spawning (if wave is active)
        current_time = pygame.time.get_ticks() / 1000.0
        if wave_active and enemies_spawned_this_wave < enemies_in_wave:
             if current_time - last_spawn_time >= config.ENEMY_SPAWN_RATE:
                 enemy = Enemy(game_map.get_path())
                 enemies.add(enemy)
                 enemies_spawned_this_wave += 1
                 last_spawn_time = current_time

        # Check if wave ended
        if wave_active and enemies_spawned_this_wave == enemies_in_wave and len(enemies) == 0:
             wave_active = False
             print(f"Wave {wave_number} cleared!")
             # Add bonus money, etc.


        # Update Entities
        enemies_reached_end = []
        for enemy in enemies:
             if enemy.update(dt): # update returns True if enemy reached end
                  enemies_reached_end.append(enemy)
                  player_health -= 1

        # Remove enemies that reached the end (do this after iteration)
        for enemy in enemies_reached_end:
             enemies.remove(enemy) # This calls kill() internally if not already killed


        towers.update(dt, enemies, projectiles)
        projectiles.update(dt, enemies)

        # --- Projectile Collision Handling ---
        # groupcollide: kill projectiles=False (dokill1), kill enemies=False (dokill2)
        # We handle kills manually now to manage splash damage.
        enemy_hits = pygame.sprite.groupcollide(enemies, projectiles, False, False)
        cannon_impacts = [] # List to store (impact_pos, damage, radius) for splash

        for enemy, projectiles_hit in enemy_hits.items():
            if not enemy.alive(): # Skip if enemy already died this frame
                continue

            for projectile in projectiles_hit:
                if not projectile.alive(): # Skip if projectile already handled (e.g. hit multiple enemies)
                    continue

                # Record impact location BEFORE applying damage/killing projectile
                impact_pos = projectile.rect.center

                # Apply direct damage
                enemy.take_damage(projectile.damage)
                killed_by_direct_hit = not enemy.alive() # Check if this hit was lethal

                if isinstance(projectile, CannonProjectile):
                    # Store cannon impact details for splash damage phase
                    cannon_impacts.append((impact_pos, projectile.damage, projectile.splash_radius))
                    if killed_by_direct_hit:
                        player_money += enemy.reward # Award money only for direct cannon kill
                elif isinstance(projectile, Projectile): # Basic projectile
                     if killed_by_direct_hit:
                          player_money += enemy.reward # Award money for direct basic kill
                else:
                    # Handle other projectile types if added later
                    pass

                # Kill the projectile after processing its hit
                projectile.kill()

                # If the enemy died from this hit, break inner loop (no need for other projectiles to hit it)
                if killed_by_direct_hit:
                     break # Move to the next enemy in enemy_hits

        # --- Apply Splash Damage ---
        if cannon_impacts:
             # Iterate over a copy of the enemies group, as health/alive status might change
             all_enemies_list = enemies.sprites()
             for impact_pos, damage, radius in cannon_impacts:
                  # Draw splash radius for debugging (optional)
                  # pygame.draw.circle(screen, config.ORANGE, impact_pos, radius, 1)

                  for enemy in all_enemies_list:
                       if enemy.alive(): # Only damage living enemies
                            dist = math.hypot(impact_pos[0] - enemy.rect.centerx, impact_pos[1] - enemy.rect.centery)
                            if dist <= radius:
                                 # Apply splash damage (potentially hitting the primary target again, often intended)
                                 enemy.take_damage(damage)
                                 # Do NOT award money for splash kills here to keep it simple


        # Check for game over
        if player_health <= 0:
            print("Game Over!")
            running = False # Or go to a game over screen

        # --- Drawing ---
        screen.fill(config.BLACK) # Background

        # Draw Map
        game_map.draw(screen)

        # Draw Entities
        towers.draw(screen)
        # enemies.draw(screen) # Generic draw only blits image
        # Manually call each enemy's draw method to include health bars
        for enemy in enemies:
            enemy.draw(screen)
        projectiles.draw(screen)

        # Draw UI
        health_text = font.render(f"Health: {player_health}", True, config.WHITE)
        money_text = font.render(f"Money: {player_money}", True, config.WHITE)
        wave_text = font.render(f"Wave: {wave_number}", True, config.WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(money_text, (10, 50))
        screen.blit(wave_text, (config.SCREEN_WIDTH - 150, 10))

        # Draw selected tower type info (REMOVED - Handled by panel)
        # selection_text = small_font.render(
        #     f"Selected: {selected_tower_type.__name__} (Cost: {selected_tower_type.COST}) [Keys 1, 2]",
        #     True, config.WHITE)
        # screen.blit(selection_text, (10, config.SCREEN_HEIGHT - 50))

        if not wave_active and player_health > 0:
             start_wave_text = font.render("Press SPACE to start next wave", True, config.WHITE)
             text_rect = start_wave_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 30))
             screen.blit(start_wave_text, text_rect)

        # Draw UI Panel
        ui_panel.draw(screen)

        pygame.display.flip() # Update the full screen

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main() 