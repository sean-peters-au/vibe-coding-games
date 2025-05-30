# Game Configuration

# Screen dimensions
TILE_SIZE = 40
GRID_WIDTH = 16 # Reduced from 20
GRID_HEIGHT = 12 # Reduced from 15
UI_PANEL_WIDTH = 160 # Pixels for the UI panel on the right
GAME_AREA_WIDTH = GRID_WIDTH * TILE_SIZE # 16*40 = 640
SCREEN_WIDTH = GAME_AREA_WIDTH + UI_PANEL_WIDTH # Total window width (640 + 160 = 800)
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE # 12*40 = 480

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
ORANGE = (255, 165, 0)
UI_BG_COLOR = (50, 50, 50) # Dark grey for UI panel
UI_BORDER_COLOR = (100, 100, 100) # Lighter grey for borders
UI_HIGHLIGHT_COLOR = (255, 255, 0) # Yellow highlight for selection
CYAN = (0, 255, 255)
GOLD = (255, 215, 0) # For gold mine fallback

# Map color names used in JSON data to RGB tuples
COLOR_MAP = {
    "WHITE": WHITE,
    "BLACK": BLACK,
    "RED": RED,
    "DARK_RED": DARK_RED,
    "GREEN": GREEN,
    "BLUE": BLUE,
    "YELLOW": YELLOW,
    "GREY": GREY,
    "DARK_GREEN": DARK_GREEN,
    "BROWN": BROWN,
    "ORANGE": ORANGE,
    "CYAN": CYAN,
    "GOLD": GOLD
}

# Asset Paths
ASSET_DIR = "assets"
GRASS_TILE = "tiles/grass.png"
DIRT_TILE = "tiles/dirt.png"
# UI Icons (User needs to provide)
HEART_ICON = "icons/heart.png"
COIN_ICON = "icons/coin.png"
NEXT_WAVE_ICON = "icons/next_wave.png"

# UI Colors
STATUS_BAR_BG_COLOR = (40, 40, 40) # Slightly darker grey for status bar

# Sound Paths (User needs to provide .wav or .ogg files)
SOUND_DIR = "assets/sounds"
# General UI/Game Sounds
TOWER_PLACE_SOUND = "place_tower.mp3"
ERROR_SOUND = "error.mp3"
SELL_SOUND = "sell.wav" # Sound for selling a tower

# Player stats
STARTING_MONEY = 700
STARTING_HEALTH = 20

# Gameplay Settings
SELL_REFUND_RATIO = 0.75 # 75% refund
TOWER_MOVE_COOLDOWN = 10.0 # Seconds before a tower can be moved again

# Enemy stats
ENEMY_SPAWN_RATE = 0.75 # Seconds between spawns
INTER_WAVE_DELAY = 5.0 # Seconds between end of wave and start of next

# Debugging
DEBUG_STARTING_WAVE = 8 # Set to higher number to start on a later wave