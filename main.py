import pygame
import sys
import config
from map import GameMap
from entities import Enemy, Tower, Projectile, CannonTower, CannonProjectile, BaseProjectile, Effect, IceProjectile, load_image
import math
from ui import UIPanel
import json
import os
import game_data_manager
import sound_manager
from wave_manager import WaveManager
from modifiers import SlowModifier

def load_game_data(data_dir="data"):
    """Loads all JSON data files from the specified directory."""
    data = {}
    try:
        with open(os.path.join(data_dir, "towers.json"), 'r') as f:
            data['towers'] = json.load(f)
        with open(os.path.join(data_dir, "projectiles.json"), 'r') as f:
            data['projectiles'] = json.load(f)
        with open(os.path.join(data_dir, "enemies.json"), 'r') as f:
            data['enemies'] = json.load(f)
        print("Game data loaded successfully.")
    except FileNotFoundError as e:
        print(f"Error loading game data: {e}. Make sure JSON files exist in '{data_dir}'.")
        raise SystemExit
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data: {e}. Check JSON file formatting.")
        raise SystemExit
    return data

def main():
    # Initialize Pygame modules
    sound_manager.init_mixer() # Initialize sound system first
    pygame.init()

    # --- Load Game Data ---
    game_data = load_game_data()
    game_data_manager.init_data(game_data)

    # --- Preload Sounds ---
    sound_manager.preload_sounds()

    # We might not need these local copies anymore, but keep for now
    tower_data = game_data['towers']
    projectile_data = game_data['projectiles']
    enemy_data = game_data['enemies']
    # --- End Load Game Data ---

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36) # Font for UI text
    small_font = pygame.font.SysFont(None, 24) # Smaller font for selection text
    ui_font = pygame.font.SysFont(None, 20) # Font for UI panel text
    status_font = pygame.font.SysFont(None, 28) # Font for status bar

    # --- Load UI Icons (with fallback) ---
    heart_icon, _ = load_image(config.HEART_ICON)
    coin_icon, _ = load_image(config.COIN_ICON)
    # Scale icons
    icon_size = (24, 24) # Desired icon size
    if heart_icon:
        heart_icon = pygame.transform.smoothscale(heart_icon, icon_size)
    if coin_icon:
        coin_icon = pygame.transform.smoothscale(coin_icon, icon_size)
    # Load next wave icon
    next_wave_icon, _ = load_image(config.NEXT_WAVE_ICON)
    if next_wave_icon:
        next_wave_icon = pygame.transform.smoothscale(next_wave_icon, icon_size)
    # --- End Load UI Icons ---

    # --- Define Class Maps (Before creating instances that need them) ---
    # Need to define enemy map before WaveManager
    ENEMY_CLASS_MAP = {
        "Goblin": Enemy,
        "Ogre": Enemy # Ogre uses the same Enemy class, just different data
    }
    # Define others here too for clarity
    # Note: TOWER_CLASS_MAP depends on ui_panel, so it stays later for now
    # If WaveManager needed tower classes, we'd need to rethink UI init
    PROJECTILE_CLASS_MAP = {
        "Basic": Projectile,
        "Cannon": CannonProjectile,
        "Ice": IceProjectile
    }

    # Game state
    # Adjust map size to fit game area
    game_map = GameMap(config.GAME_AREA_WIDTH // config.TILE_SIZE, config.GRID_HEIGHT)
    enemies = pygame.sprite.Group()
    towers = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    player_money = config.STARTING_MONEY
    player_health = config.STARTING_HEALTH

    # Keep track of visual effects
    effects = pygame.sprite.Group()
    # selected_tower_type = Tower # Selection now handled by UI panel

    # Create Wave Manager (pass enemy class map)
    wave_manager = WaveManager(enemy_class_map=ENEMY_CLASS_MAP)

    # Create UI Panel (Needs tower_data)
    ui_panel = UIPanel(tower_data=tower_data, start_y=50, font=ui_font)

    # Get Tower Class Map from UI Panel (after it's created)
    TOWER_CLASS_MAP = ui_panel.tower_class_map

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0 # Delta time in seconds

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_SPACE and not wave_manager.is_wave_active(): # Check WaveManager state
                      # Start the next wave via the manager
                      wave_manager.start_next_wave()

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

                        # Get selected tower type KEY from the panel
                        selected_tower_key = ui_panel.get_selected_tower_key()

                        if selected_tower_key:
                             # Get tower data for cost check
                             selected_data = game_data_manager.get_tower_data(selected_tower_key)
                             if selected_data:
                                  tower_cost = selected_data.get("cost", 9999)
                                  # Try placing the selected tower type
                                  if player_money >= tower_cost:
                                       if game_map.place_tower(grid_x, grid_y):
                                            # Get class from map using key
                                            TowerClass = TOWER_CLASS_MAP.get(selected_tower_key)
                                            if TowerClass:
                                                 # Instantiate with grid coords (key is handled internally now)
                                                 tower = TowerClass(grid_x, grid_y)
                                                 towers.add(tower)
                                                 player_money -= tower.cost # Use cost from instance
                                                 # Play sound on successful placement
                                                 sound_manager.play_sound(sound_manager.SOUND_CACHE.get(config.TOWER_PLACE_SOUND))
                                            else:
                                                 print(f"Error: Class not found for key '{selected_tower_key}'")
                                       else:
                                            print("Cannot place tower here.")
                                            sound_manager.play_sound(sound_manager.SOUND_CACHE.get(config.ERROR_SOUND))
                                  else:
                                       print("Not enough money!")
                                       sound_manager.play_sound(sound_manager.SOUND_CACHE.get(config.ERROR_SOUND))
                             else:
                                  print(f"Error: No data found for selected tower '{selected_tower_key}'")
                        else:
                             print("No tower type selected in UI.")


        # --- Game Logic ---

        # Enemy Spawning (handled by WaveManager update)
        wave_manager.update(dt, game_map, enemies) # Pass necessary arguments

        # Check if wave ended (All spawned AND all defeated)
        if wave_manager.is_wave_active() and wave_manager.is_wave_complete() and len(enemies) == 0:
             print(f"Wave {wave_manager.current_wave_number} cleared!")
             wave_manager.end_wave() # Tell manager wave is over
             # Add bonus money, etc.


        # Update Entities
        enemies_reached_end = []
        for enemy in enemies:
             if enemy.update(dt): # update returns True if enemy reached end
                  enemies_reached_end.append(enemy)
                  player_health -= 1

        # Remove enemies that reached the end (do this after iteration)
        for enemy in enemies_reached_end:
             # Play reach end sound from enemy data
             enemy_data = game_data_manager.get_enemy_data(enemy.type_key)
             if enemy_data and enemy_data.get("reach_end_sound"):
                  sound_manager.play_sound(sound_manager.load_sound(enemy_data["reach_end_sound"]))
             # Remove the sprite AFTER playing sound (or it might not play)
             enemies.remove(enemy)


        towers.update(dt, enemies, projectiles)
        projectiles.update(dt, enemies)
        effects.update(dt) # Update visual effects

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

                # Play hit sound from projectile data
                proj_data = game_data_manager.get_projectile_data(projectile.type_key)
                if proj_data and proj_data.get("hit_sound"):
                    sound_manager.play_sound(sound_manager.load_sound(proj_data["hit_sound"]))

                # Record impact location BEFORE applying damage/killing projectile
                impact_pos = projectile.rect.center

                # Apply direct damage
                enemy.take_damage(projectile.damage)
                killed_by_direct_hit = not enemy.alive() # Check if this hit was lethal

                # Use class map to check projectile type by key
                ProjectileClass = PROJECTILE_CLASS_MAP.get("Basic")
                CannonProjectileClass = PROJECTILE_CLASS_MAP.get("Cannon")
                IceProjectileClass = PROJECTILE_CLASS_MAP.get("Ice") # Get Ice class

                # Check instance type carefully
                is_cannon = CannonProjectileClass is not None and isinstance(projectile, CannonProjectileClass)
                is_basic = ProjectileClass is not None and isinstance(projectile, ProjectileClass)
                is_ice = IceProjectileClass is not None and isinstance(projectile, IceProjectileClass)

                if is_cannon:
                    # Store cannon impact details for splash damage phase
                    cannon_impacts.append((impact_pos, projectile.damage, projectile.splash_radius))
                    if killed_by_direct_hit:
                        player_money += enemy.reward
                elif is_basic:
                     if killed_by_direct_hit:
                          player_money += enemy.reward
                elif is_ice:
                     # Apply direct damage first
                     enemy.take_damage(projectile.damage)
                     killed_by_direct_hit = not enemy.alive()

                     # Apply slow effect modifier in an area
                     for target_enemy in enemies.sprites():
                          if target_enemy.alive():
                               dist = math.hypot(impact_pos[0] - target_enemy.rect.centerx, impact_pos[1] - target_enemy.rect.centery)
                               if dist <= projectile.splash_radius:
                                    # Create and add SlowModifier
                                    slow_mod = SlowModifier(projectile.slow_factor, projectile.slow_duration)
                                    target_enemy.add_modifier(slow_mod)

                     if killed_by_direct_hit:
                          player_money += enemy.reward

                # Kill the projectile after processing its hit
                projectile.kill()

                # If the enemy died from this hit, break inner loop (no need for other projectiles to hit it)
                if killed_by_direct_hit:
                     break # Move to the next enemy in enemy_hits

        # --- Apply Splash Damage ---
        if cannon_impacts:
             all_enemies_list = enemies.sprites()
             for impact_pos, damage, radius in cannon_impacts:
                  # --- Create Splash Visual Effect --- #
                  # Fetch the splash image path from cannon projectile data
                  cannon_data = game_data_manager.get_projectile_data("Cannon")
                  if cannon_data and "splash_image" in cannon_data:
                      splash_image_path = cannon_data["splash_image"]
                      # Calculate target size based on splash radius
                      # e.g., make diameter match splash radius * 2
                      target_diameter = int(radius)
                      effect_size = (target_diameter, target_diameter)

                      # Create effect with target size
                      effect = Effect(impact_pos, splash_image_path, 100, target_size=effect_size)
                      effects.add(effect)
                  # ---------------------------------- #

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
        effects.draw(screen) # Draw visual effects

        # Draw UI Elements
        # Status Bar (drawn over game area)
        draw_status_bar(screen, player_health, player_money, wave_manager.current_wave_number, heart_icon, coin_icon, status_font)

        # UI Panel (drawn in its own area)
        ui_panel.draw(screen)

        # Draw "Start Wave" prompt (Improved Location/Style Needed Later)
        if not wave_manager.is_wave_active() and player_health > 0:
            # Use an icon and less intrusive text
            prompt_y = config.SCREEN_HEIGHT - 30
            prompt_text = small_font.render("Next Wave (SPACE)", True, config.WHITE)
            # Center based on game area width
            prompt_rect = prompt_text.get_rect(center=(config.GAME_AREA_WIDTH // 2, prompt_y))

            if next_wave_icon:
                # Position icon to the left of text
                icon_rect = next_wave_icon.get_rect(midright=(prompt_rect.left - 5, prompt_y))
                screen.blit(next_wave_icon, icon_rect)
                screen.blit(prompt_text, prompt_rect)
            else:
                # Fallback: just draw text if icon missing
                screen.blit(prompt_text, prompt_rect)

        pygame.display.flip() # Update the full screen

    pygame.quit()
    sys.exit()

# --- Helper Functions ---
def draw_status_bar(surface, health, money, wave, heart_icon, coin_icon, font):
    """Draws the top status bar with icons and text."""
    bar_height = 40 # Height of the status bar
    bar_rect = pygame.Rect(0, 0, config.GAME_AREA_WIDTH, bar_height)
    pygame.draw.rect(surface, config.STATUS_BAR_BG_COLOR, bar_rect)

    padding = 10
    icon_text_padding = 5
    current_x = padding

    # Health
    if heart_icon:
        surface.blit(heart_icon, (current_x, (bar_height - heart_icon.get_height()) // 2))
        current_x += heart_icon.get_width() + icon_text_padding
    health_text = font.render(f"{health}", True, config.WHITE)
    health_rect = health_text.get_rect(midleft=(current_x, bar_height // 2))
    surface.blit(health_text, health_rect)
    current_x += health_rect.width + padding * 2 # Add more space before next item

    # Money
    if coin_icon:
        surface.blit(coin_icon, (current_x, (bar_height - coin_icon.get_height()) // 2))
        current_x += coin_icon.get_width() + icon_text_padding
    money_text = font.render(f"{money}", True, config.WHITE)
    money_rect = money_text.get_rect(midleft=(current_x, bar_height // 2))
    surface.blit(money_text, money_rect)
    current_x += money_rect.width + padding * 2

    # Wave (align to right)
    wave_text = font.render(f"Wave: {wave}", True, config.WHITE)
    wave_rect = wave_text.get_rect(midright=(config.GAME_AREA_WIDTH - padding, bar_height // 2))
    surface.blit(wave_text, wave_rect)

if __name__ == '__main__':
    main() 