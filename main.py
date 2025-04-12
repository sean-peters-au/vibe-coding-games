import pygame
import sys
import config
from map import GameMap
from entities import Enemy, Tower, Projectile

def main():
    pygame.init()

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36) # Font for UI text

    # Game state
    game_map = GameMap(config.SCREEN_WIDTH // config.TILE_SIZE, config.SCREEN_HEIGHT // config.TILE_SIZE)
    enemies = pygame.sprite.Group()
    towers = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    player_money = config.STARTING_MONEY
    player_health = config.STARTING_HEALTH
    wave_number = 0
    last_spawn_time = 0
    enemies_in_wave = 10
    enemies_spawned_this_wave = 0
    wave_active = False # Start waves manually (e.g., with a key press) or automatically


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
                      enemies_in_wave = 5 + wave_number * 2 # Increase enemies per wave

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_x, mouse_y = event.pos
                    grid_x, grid_y = mouse_x // config.TILE_SIZE, mouse_y // config.TILE_SIZE

                    # Try placing a tower
                    if player_money >= config.TOWER_COST:
                        if game_map.place_tower(grid_x, grid_y):
                            tower = Tower(grid_x, grid_y)
                            towers.add(tower)
                            player_money -= config.TOWER_COST
                        else:
                            print("Cannot place tower here.")
                    else:
                        print("Not enough money!")


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
        # Detect collisions between projectiles and enemies
        # groupcollide returns a dict {enemy_hit: [list_of_projectiles_that_hit_it]}
        # The last two True arguments mean: kill projectiles (dokill1=True), do not kill enemies (dokill2=False) automatically
        enemy_hits = pygame.sprite.groupcollide(enemies, projectiles, False, True)

        for enemy, projectiles_hit in enemy_hits.items():
            if enemy.alive(): # Ensure enemy hasn't already been killed this frame
                for projectile in projectiles_hit:
                     enemy.take_damage(projectile.damage)
                # After applying damage from all projectiles that hit this frame,
                # check if the enemy died.
                if not enemy.alive(): # Check if take_damage resulted in kill()
                    player_money += config.ENEMY_REWARD
                    # enemy.kill() was already called within take_damage if health <= 0

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
        enemies.draw(screen) # Draw enemies after towers
        # Draw enemy health bars (handled within enemy.draw now)
        projectiles.draw(screen)

        # Draw UI
        health_text = font.render(f"Health: {player_health}", True, config.WHITE)
        money_text = font.render(f"Money: {player_money}", True, config.WHITE)
        wave_text = font.render(f"Wave: {wave_number}", True, config.WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(money_text, (10, 50))
        screen.blit(wave_text, (config.SCREEN_WIDTH - 150, 10))

        if not wave_active and player_health > 0:
             start_wave_text = font.render("Press SPACE to start next wave", True, config.WHITE)
             text_rect = start_wave_text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 30))
             screen.blit(start_wave_text, text_rect)


        pygame.display.flip() # Update the full screen

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main() 