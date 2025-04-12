# Game Configuration

# Screen dimensions
TILE_SIZE = 40
GRID_WIDTH = 20 # Grid cells for the game area
GRID_HEIGHT = 15
UI_PANEL_WIDTH = 160 # Pixels for the UI panel on the right
GAME_AREA_WIDTH = GRID_WIDTH * TILE_SIZE # 800
SCREEN_WIDTH = GAME_AREA_WIDTH + UI_PANEL_WIDTH # Total window width (800 + 160 = 960)
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
ORANGE = (255, 165, 0) # For cannon projectile fallback
UI_BG_COLOR = (50, 50, 50) # Dark grey for UI panel
UI_BORDER_COLOR = (100, 100, 100) # Lighter grey for borders
UI_HIGHLIGHT_COLOR = (255, 255, 0) # Yellow highlight for selection

# Asset Paths
ASSET_DIR = "assets"
TOWER_IMAGE = "tower.png"
ENEMY_IMAGE = "enemy.png"
PROJECTILE_IMAGE = "projectile.png"
CANNON_TOWER_IMAGE = "cannon_tower.png"
CANNON_PROJECTILE_IMAGE = "cannon_projectile.png"
# Icons for UI Panel (optional, will use fallback colors)
TOWER_ICON = "tower_icon.png"
CANNON_TOWER_ICON = "cannon_tower_icon.png"

# Player stats
STARTING_MONEY = 100
STARTING_HEALTH = 20

# Enemy stats
ENEMY_SPAWN_RATE = 1.0 # Seconds between spawns - Wave/Game logic, keep here for now