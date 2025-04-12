import pygame
import config
import math

# --- Tower Class ---
class Tower(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y):
        super().__init__()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.x = grid_x * config.TILE_SIZE + config.TILE_SIZE // 2
        self.y = grid_y * config.TILE_SIZE + config.TILE_SIZE // 2

        self.image = pygame.Surface([config.TOWER_SIZE, config.TOWER_SIZE])
        self.image.fill(config.BLUE)
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.range = config.TOWER_RANGE
        self.fire_rate = config.TOWER_FIRE_RATE # Seconds between shots
        self.last_shot_time = 0
        self.target = None # Current enemy target

    def find_target(self, enemies):
        self.target = None
        min_dist = self.range
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.rect.centerx, self.y - enemy.rect.centery)
            if dist <= min_dist:
                 # Prioritize closest enemy or first in range? Add logic here if needed.
                 min_dist = dist
                 self.target = enemy

    def shoot(self, projectiles):
        if self.target:
            projectile = Projectile(self.rect.center, self.target)
            projectiles.add(projectile)

    def update(self, dt, enemies, projectiles):
        current_time = pygame.time.get_ticks() / 1000.0

        # Find target if we don't have one or current target is out of range/dead
        if not self.target or not self.target.alive() or math.hypot(self.x - self.target.rect.centerx, self.y - self.target.rect.centery) > self.range:
            self.find_target(enemies)

        # Shoot if target is found and fire rate allows
        if self.target and (current_time - self.last_shot_time >= self.fire_rate):
            self.shoot(projectiles)
            self.last_shot_time = current_time

# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, path):
        super().__init__()
        self.path = path # List of (x, y) pixel coordinates
        self.path_index = 0
        self.x, self.y = self.path[0]

        self.image = pygame.Surface([config.ENEMY_SIZE, config.ENEMY_SIZE])
        self.image.fill(config.RED)
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.speed = config.ENEMY_SPEED
        self.health = config.ENEMY_HEALTH
        self.max_health = config.ENEMY_HEALTH

        self.target_x, self.target_y = self.path[1] # Start moving towards the second point

    def move(self, dt):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed * dt: # Reached or passed the target waypoint
            self.x, self.y = self.target_x, self.target_y # Snap to waypoint
            self.path_index += 1
            if self.path_index >= len(self.path):
                return True # Reached the end
            self.target_x, self.target_y = self.path[self.path_index]

        else: # Move towards the target
            move_x = (dx / dist) * self.speed * dt
            move_y = (dy / dist) * self.speed * dt
            self.x += move_x
            self.y += move_y

        self.rect.center = (self.x, self.y)
        return False # Still moving

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill() # Remove sprite from all groups

    def draw_health_bar(self, surface):
         if self.health < self.max_health:
             bar_width = config.ENEMY_SIZE
             bar_height = 5
             health_pct = self.health / self.max_health
             health_bar_width = int(bar_width * health_pct)

             # Background of the health bar (e.g., dark red)
             bg_rect = pygame.Rect(self.rect.left, self.rect.top - bar_height - 2, bar_width, bar_height)
             pygame.draw.rect(surface, config.DARK_RED, bg_rect)

             # Actual health bar (e.g., green)
             health_rect = pygame.Rect(self.rect.left, self.rect.top - bar_height - 2, health_bar_width, bar_height)
             pygame.draw.rect(surface, config.GREEN, health_rect)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.draw_health_bar(surface)


    def update(self, dt):
        reached_end = self.move(dt)
        return reached_end

# --- Projectile Class ---
class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_enemy):
        super().__init__()
        self.x, self.y = start_pos
        self.target = target_enemy # Reference to the target enemy sprite

        self.image = pygame.Surface([config.PROJECTILE_SIZE, config.PROJECTILE_SIZE])
        self.image.fill(config.YELLOW)
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.speed = config.PROJECTILE_SPEED
        self.damage = config.PROJECTILE_DAMAGE

    def move(self, dt):
         if not self.target or not self.target.alive():
             self.kill() # Target is gone
             return

         target_x, target_y = self.target.rect.center
         dx = target_x - self.x
         dy = target_y - self.y
         dist = math.hypot(dx, dy)

         # Simplified: Projectile just moves towards target.
         # Collision detection and damage are now handled in the main loop.
         if dist < self.speed * dt:
             # Reached vicinity of target - let main loop handle collision
             # Move the projectile exactly to the target's last known center
             # to ensure collision is detected by groupcollide, then kill projectile.
             # Or simply let groupcollide handle it if it's close enough.
             # For simplicity, let's just move towards it.
             # If we move *past* it slightly, groupcollide should still work.
             pass # Let groupcollide handle the hit this frame

         # Move towards target
         move_x = (dx / dist) * self.speed * dt
         move_y = (dy / dist) * self.speed * dt
         self.x += move_x
         self.y += move_y
         self.rect.center = (self.x, self.y)

    def update(self, dt, enemies): # 'enemies' might not be needed if we just use self.target
        self.move(dt) 