# Game Configuration

# Screen dimensions
TILE_SIZE = 40
GRID_WIDTH = 20
GRID_HEIGHT = 15
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE # 800
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE # 600

# Frame rate
FPS = 60

# Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREY = (128, 128, 128)
DARK_GREEN = (0, 100, 0) # Path color
BROWN = (165, 42, 42) # Tower placed tile color


# Player stats
STARTING_MONEY = 100
STARTING_HEALTH = 20

# Enemy stats
ENEMY_SIZE = int(TILE_SIZE * 0.6)
ENEMY_SPEED = 50 # Pixels per second
ENEMY_HEALTH = 100
ENEMY_REWARD = 10 # Money gained per kill
ENEMY_SPAWN_RATE = 1.0 # Seconds between spawns

# Tower stats
TOWER_SIZE = int(TILE_SIZE * 0.8)
TOWER_COST = 50
TOWER_RANGE = 150 # Pixels
TOWER_FIRE_RATE = 1.0 # Shots per second (lower is faster, will be inverted in logic)
                      # Correction: This should be seconds per shot (higher is slower)
TOWER_FIRE_RATE = 1.0 # Seconds between shots

# Projectile stats
PROJECTILE_SIZE = int(TILE_SIZE * 0.2)
PROJECTILE_SPEED = 300 # Pixels per second
PROJECTILE_DAMAGE = 25 