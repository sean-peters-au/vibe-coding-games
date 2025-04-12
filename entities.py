import pygame
import config
import math
import os # Needed for path joining

def load_image(filename, colorkey=None):
    """Loads an image, prepares it for play.
       From: pygame.readthedocs.io/en/latest/tut/ChimpLineByLine.html"""
    fullname = os.path.join(config.ASSET_DIR, filename)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message: # Catch Pygame-specific errors
        print("Warning: Cannot load image (Pygame Error):", fullname)
        print(message)
        return None, None # Indicate failure
    except FileNotFoundError:
        print("Warning: Cannot load image (File Not Found):", fullname)
        return None, None # Indicate failure

    image = image.convert_alpha() # Preserve transparency
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()

# --- Base Classes ---
class BaseTower(pygame.sprite.Sprite):
    # Common attributes/methods for all towers
    def __init__(self, grid_x, grid_y):
        super().__init__()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.x = grid_x * config.TILE_SIZE + config.TILE_SIZE // 2
        self.y = grid_y * config.TILE_SIZE + config.TILE_SIZE // 2
        self.last_shot_time = 0
        self.target = None

    def find_target(self, enemies):
        self.target = None
        min_dist = self.range # Assumes self.range is set by subclass
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.rect.centerx, self.y - enemy.rect.centery)
            if dist <= min_dist:
                 min_dist = dist
                 self.target = enemy

    def update(self, dt, enemies, projectiles):
        current_time = pygame.time.get_ticks() / 1000.0

        # Find target
        if not self.target or not self.target.alive() or math.hypot(self.x - self.target.rect.centerx, self.y - self.target.rect.centery) > self.range:
            self.find_target(enemies)

        # Shoot
        if self.target and (current_time - self.last_shot_time >= self.fire_rate): # Assumes self.fire_rate set by subclass
            self.shoot(projectiles)
            self.last_shot_time = current_time

    # Abstract method - subclasses must implement
    def shoot(self, projectiles):
        raise NotImplementedError("Subclass must implement shoot method")

    def load_and_position_image(self, image_path, fallback_size, fallback_color):
        self.image, self.rect = load_image(image_path)
        if self.image is None:
            print(f"Using fallback for {image_path}")
            self.image = pygame.Surface([fallback_size, fallback_size])
            self.image.fill(fallback_color)
            self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


class BaseProjectile(pygame.sprite.Sprite):
    # Common attributes/methods for all projectiles
    def __init__(self, start_pos, target_enemy):
        super().__init__()
        self.x, self.y = start_pos
        self.target = target_enemy

    def move(self, dt):
        if not self.target or not self.target.alive():
            self.kill()
            return

        target_x, target_y = self.target.rect.center
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed * dt: # Assumes self.speed set by subclass
             pass # Let groupcollide handle the hit

        move_x = (dx / dist) * self.speed * dt
        move_y = (dy / dist) * self.speed * dt
        self.x += move_x
        self.y += move_y
        self.rect.center = (self.x, self.y) # Assumes self.rect set by subclass

    def update(self, dt, enemies):
        self.move(dt)

    def load_and_position_image(self, image_path, fallback_size, fallback_color):
        self.image, self.rect = load_image(image_path)
        if self.image is None:
            print(f"Using fallback for {image_path}")
            self.image = pygame.Surface([fallback_size, fallback_size])
            self.image.fill(fallback_color)
            self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


# --- Tower Class (now inherits from BaseTower) ---
class Tower(BaseTower):
    FALLBACK_SIZE = int(config.TILE_SIZE * 0.8)
    FALLBACK_COLOR = config.BLUE
    # Define specific stats
    COST = 50
    RANGE = 150 # Pixels
    FIRE_RATE = 1.0 # Seconds between shots

    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y)

        # Load image using helper from base class
        self.load_and_position_image(config.TOWER_IMAGE, self.FALLBACK_SIZE, self.FALLBACK_COLOR)

        # Set instance stats from class stats
        self.range = self.RANGE
        self.fire_rate = self.FIRE_RATE
        self.cost = self.COST

    # Implement the specific shooting action
    def shoot(self, projectiles):
        if self.target:
            # Note: Projectile class reference below is correct
            projectile = Projectile(self.rect.center, self.target)
            projectiles.add(projectile)


# --- Projectile Class (now inherits from BaseProjectile) ---
class Projectile(BaseProjectile):
    FALLBACK_SIZE = int(config.TILE_SIZE * 0.2)
    FALLBACK_COLOR = config.YELLOW
    # Define specific stats
    SPEED = 300 # Pixels per second
    DAMAGE = 25

    def __init__(self, start_pos, target_enemy):
        super().__init__(start_pos, target_enemy)

        # Load image using helper from base class
        self.load_and_position_image(config.PROJECTILE_IMAGE, self.FALLBACK_SIZE, self.FALLBACK_COLOR)

        # Set instance stats from class stats
        self.speed = self.SPEED
        self.damage = self.DAMAGE

# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):
    FALLBACK_SIZE = int(config.TILE_SIZE * 0.6)
    FALLBACK_COLOR = config.RED
    # Define stats here
    SPEED = 50 # Pixels per second
    HEALTH = 100
    REWARD = 10 # Money gained per kill

    def __init__(self, path):
        super().__init__()
        self.path = path # List of (x, y) pixel coordinates
        self.path_index = 0
        self.x, self.y = self.path[0]

        self.image, self.rect = load_image(config.ENEMY_IMAGE)

        if self.image is None: # Fallback if image loading failed
             print(f"Using fallback for {config.ENEMY_IMAGE}")
             self.image = pygame.Surface([self.FALLBACK_SIZE, self.FALLBACK_SIZE])
             self.image.fill(self.FALLBACK_COLOR)
             self.rect = self.image.get_rect()

        self.rect.center = (self.x, self.y)

        # Use class attributes for stats
        self.speed = self.SPEED
        self.health = self.HEALTH
        self.max_health = self.HEALTH # Base max health on initial health
        self.reward = self.REWARD

        # Ensure path has at least two points to avoid index error
        if len(self.path) > 1:
             self.target_x, self.target_y = self.path[1] # Start moving towards the second point
        else:
             # Handle case with short path (e.g., stay put or error)
             print(f"Warning: Enemy path for {self.__class__.__name__} too short.")
             self.target_x, self.target_y = self.x, self.y # Stay in place

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
             bar_width = self.rect.width
             bar_height = 5
             health_pct = max(0, self.health / self.max_health)
             health_bar_width = int(bar_width * health_pct)

             # Position below the sprite
             bar_y = self.rect.bottom + 2 # 2 pixels below the bottom edge

             # Background of the health bar (e.g., dark red)
             bg_rect = pygame.Rect(self.rect.left, bar_y, bar_width, bar_height)
             pygame.draw.rect(surface, config.DARK_RED, bg_rect)

             # Actual health bar (e.g., green)
             health_rect = pygame.Rect(self.rect.left, bar_y, health_bar_width, bar_height)
             pygame.draw.rect(surface, config.GREEN, health_rect)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.draw_health_bar(surface)

    def update(self, dt):
        reached_end = self.move(dt)
        return reached_end

# --- Cannon Tower Class ---
class CannonTower(BaseTower):
    FALLBACK_SIZE = int(config.TILE_SIZE * 0.9) # Slightly larger fallback
    FALLBACK_COLOR = config.DARK_RED
    # Define specific stats
    COST = 100
    RANGE = 180 # Longer range
    FIRE_RATE = 2.5 # Slower fire rate

    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y)

        # Load image using helper from base class
        self.load_and_position_image(config.CANNON_TOWER_IMAGE, self.FALLBACK_SIZE, self.FALLBACK_COLOR)

        # Set instance stats from class stats
        self.range = self.RANGE
        self.fire_rate = self.FIRE_RATE
        self.cost = self.COST

    # Implement the specific shooting action
    def shoot(self, projectiles):
        if self.target:
            projectile = CannonProjectile(self.rect.center, self.target)
            projectiles.add(projectile)


# --- Cannon Projectile Class ---
class CannonProjectile(BaseProjectile):
    FALLBACK_SIZE = int(config.TILE_SIZE * 0.3)
    FALLBACK_COLOR = config.ORANGE # Need to define ORANGE in config
    # Define specific stats
    SPEED = 200 # Slower projectile
    DAMAGE = 75 # Higher damage
    SPLASH_RADIUS = 50 # Pixels

    def __init__(self, start_pos, target_enemy):
        super().__init__(start_pos, target_enemy)

        # Load image using helper from base class
        self.load_and_position_image(config.CANNON_PROJECTILE_IMAGE, self.FALLBACK_SIZE, self.FALLBACK_COLOR)

        # Set instance stats from class stats
        self.speed = self.SPEED
        self.damage = self.DAMAGE
        self.splash_radius = self.SPLASH_RADIUS 