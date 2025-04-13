# asset_manager.py
import pygame
import os
import config

class AssetManager:
    def __init__(self):
        self.image_cache = {}
        self.sound_cache = {}
        self._initialize_mixer() # Initialize mixer on creation

    def _initialize_mixer(self):
        """Initializes the pygame mixer, catching errors."""
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self.sound_enabled = True
            print("Mixer initialized successfully by AssetManager.")
        except pygame.error as e:
            print(f"Error initializing mixer in AssetManager: {e}. Sound disabled.")
            self.sound_enabled = False

    def load_image(self, filename, colorkey=None):
        """Loads an image, prepares it for play, uses caching. Returns (image, rect) tuple."""
        if filename in self.image_cache:
            cached_item = self.image_cache[filename]
            # Return image and its rect if cached successfully, else None, None
            return (cached_item, cached_item.get_rect()) if cached_item else (None, None)

        fullname = os.path.join(config.ASSET_DIR, filename)
        try:
            image = pygame.image.load(fullname).convert_alpha()
        except pygame.error as message:
            print(f"Warning: Cannot load image (Pygame Error): {fullname} - {message}")
            self.image_cache[filename] = None # Cache the failure
            return None, None
        except FileNotFoundError:
            print(f"Warning: Cannot load image (File Not Found): {fullname}")
            self.image_cache[filename] = None
            return None, None

        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        
        self.image_cache[filename] = image
        print(f"Loaded image: {filename}")
        # Return the loaded image and its rect
        return image, image.get_rect()

    def load_sound(self, filename):
        """Loads a sound file, uses caching."""
        if not self.sound_enabled:
            return None
        if filename in self.sound_cache:
            return self.sound_cache[filename]

        fullname = os.path.join(config.SOUND_DIR, filename)
        try:
            sound = pygame.mixer.Sound(fullname)
            self.sound_cache[filename] = sound
            print(f"Loaded sound: {filename}")
            return sound
        except pygame.error as message:
            print(f"Warning: Cannot load sound: {fullname} - {message}")
            self.sound_cache[filename] = None
            return None
        except FileNotFoundError:
            print(f"Warning: Sound file not found: {fullname}")
            self.sound_cache[filename] = None
            return None

    def play_sound(self, sound_object):
        """Plays a loaded sound object if sound is enabled."""
        if self.sound_enabled and sound_object:
            sound_object.play()

    def preload_assets(self):
        """Preload common sounds and potentially images."""
        print("AssetManager preloading assets...")
        # Preload general UI sounds from config
        if hasattr(config, 'TOWER_PLACE_SOUND'): self.load_sound(config.TOWER_PLACE_SOUND)
        if hasattr(config, 'ERROR_SOUND'): self.load_sound(config.ERROR_SOUND)
        if hasattr(config, 'SELL_SOUND'): self.load_sound(config.SELL_SOUND)
        # Could add preloading for other assets (e.g., tile images) here if desired
        print("AssetManager preloading complete.")

    # Optional: Add methods to get scaled images directly to simplify entity code?
    # def get_scaled_image(self, filename, size):
    #     img = self.load_image(filename)
    #     if img:
    #         # Add caching for scaled versions?
    #         return pygame.transform.smoothscale(img, size)
    #     return None 