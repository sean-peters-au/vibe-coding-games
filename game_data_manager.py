# game_data_manager.py

# Global dictionary to hold loaded game data
GAME_DATA = {}

def init_data(loaded_data):
    """Initializes the global GAME_DATA with data loaded from main."""
    global GAME_DATA
    GAME_DATA.update(loaded_data)
    print("Game data manager initialized.")

def get_tower_data(type_key):
    return GAME_DATA.get('towers', {}).get(type_key)

def get_projectile_data(type_key):
    return GAME_DATA.get('projectiles', {}).get(type_key)

def get_enemy_data(type_key):
    return GAME_DATA.get('enemies', {}).get(type_key) 