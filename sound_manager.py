# sound_manager.py
import pygame
import os
import config

# Dictionary to cache loaded sounds
SOUND_CACHE = {}
SOUND_ENABLED = True # Global flag to easily disable sound

def load_sound(filename):
    """Loads a sound file from the SOUND_DIR, handling errors."""
    if not SOUND_ENABLED or not pygame.mixer or not pygame.mixer.get_init():
        return None # Mixer not initialized or sound disabled
    if filename in SOUND_CACHE:
        return SOUND_CACHE[filename]

    fullname = os.path.join(config.SOUND_DIR, filename)
    try:
        sound = pygame.mixer.Sound(fullname)
        SOUND_CACHE[filename] = sound
        print(f"Loaded sound: {filename}")
        return sound
    except pygame.error as message:
        print(f"Warning: Cannot load sound: {fullname} - {message}")
        SOUND_CACHE[filename] = None # Cache failure so we don't retry
        return None
    except FileNotFoundError:
        print(f"Warning: Sound file not found: {fullname}")
        SOUND_CACHE[filename] = None
        return None

def play_sound(sound_object):
    """Plays a loaded sound object if sound is enabled."""
    if SOUND_ENABLED and sound_object:
        sound_object.play()

def preload_sounds():
    """Preload common sounds into the cache."""
    print("Preloading sounds...")
    # Only preload general sounds defined in config
    load_sound(config.TOWER_PLACE_SOUND)
    load_sound(config.ERROR_SOUND)
    print("Sound preloading complete.")

def init_mixer():
    """Initializes the pygame mixer."""
    global SOUND_ENABLED
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512) # Common settings
        pygame.mixer.init()
        print("Pygame mixer initialized successfully.")
        SOUND_ENABLED = True
    except pygame.error as e:
        print(f"Error initializing pygame mixer: {e}")
        print("Sound will be disabled.")
        SOUND_ENABLED = False 