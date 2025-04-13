import pygame
import config
import math
import os
import game_data_manager
from modifiers import Modifier, SlowModifier # Import modifiers
from game_data_manager import DataManager

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
        print(f"Warning: Cannot load image (File Not Found):", fullname)
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
    def __init__(self, grid_x, grid_y, type_key, asset_manager, data_manager):
        super().__init__()
        self.asset_manager = asset_manager
        self.data_manager = data_manager # Store data manager
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.x = grid_x * config.TILE_SIZE + config.TILE_SIZE // 2
        self.y = grid_y * config.TILE_SIZE + config.TILE_SIZE // 2
        self.last_shot_time = 0
        self.target = None
        self.type_key = type_key # Store the type key (e.g., "Basic", "Cannon")

        # === Load Data and Set Attributes FIRST ===
        data = self.data_manager.get_tower_data(type_key)
        if not data:
            print(f"Error: No data found for tower type '{type_key}'")
            return

        self.cost = data.get("cost", 9999)
        self.range = data.get("range", 0)
        self.fire_rate = data.get("fire_rate", 0)
        self.projectile_type = data.get("projectile_type", "Basic")
        self.click_gold = data.get("click_gold", 0)
        # Load paths and ratios needed later
        image_path = data.get("image", "default_tower.png")
        scale_ratio = data.get("scale_ratio", 0.9)
        fallback_size_ratio = data.get("fallback_size_ratio", 0.8)
        fallback_color_name = data.get("fallback_color", "GREY")
        # === End Data Loading ===

        # --- Click Animation (Now scale_ratio is available) ---
        self.click_animation_frames = []
        self.click_animation_speed = 150
        self.is_animating = False
        self.current_animation_frame_index = 0
        self.last_animation_update = 0

        anim_data = data.get("click_animation")
        if anim_data and isinstance(anim_data.get("frames"), list):
            self.click_animation_speed = anim_data.get("speed", 150)
            # Calculate target size using the loaded scale_ratio
            target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))
            for frame_filename in anim_data["frames"]:
                frame_surface, _ = asset_manager.load_image(frame_filename)
                if frame_surface:
                    try:
                        scaled_frame = pygame.transform.smoothscale(frame_surface.copy(), target_size)
                        self.click_animation_frames.append(scaled_frame)
                    except ValueError as e:
                        print(f"Error scaling click anim frame {frame_filename}: {e}")
            if not self.click_animation_frames:
                 print(f"Warning: Failed loading click anim frames for {type_key}")

        # --- Load Idle Image and Position --- 
        fallback_size = int(config.TILE_SIZE * fallback_size_ratio)
        fallback_color = config.COLOR_MAP.get(fallback_color_name, config.GREY)
        # Pass asset_manager, paths, and fallback info to loading helper
        self.load_and_position_image(asset_manager, image_path, fallback_size, fallback_color)
        # Store the base image AFTER loading/scaling
        self.idle_image = self.image

    def find_target(self, enemies):
        self.target = None
        min_dist = self.range # Assumes self.range is set by subclass
        for enemy in enemies:
            dist = math.hypot(self.x - enemy.rect.centerx, self.y - enemy.rect.centery)
            if dist <= min_dist:
                 min_dist = dist
                 self.target = enemy

    def update(self, dt, enemies, projectiles):
        current_time_ms = pygame.time.get_ticks()

        # Handle Click Animation
        if self.is_animating:
            if current_time_ms - self.last_animation_update > self.click_animation_speed:
                self.last_animation_update = current_time_ms
                self.current_animation_frame_index += 1
                if self.current_animation_frame_index >= len(self.click_animation_frames):
                    # Animation finished
                    self.is_animating = False
                    self.image = self.idle_image # Revert to idle image
                else:
                    # Continue animation
                    self.image = self.click_animation_frames[self.current_animation_frame_index]
        
        # Original update logic (Shooting)
        if self.range > 0 and self.fire_rate > 0: # Only shoot if range/rate are valid
            current_time_sec = current_time_ms / 1000.0
            # Find target
            if not self.target or not self.target.alive() or math.hypot(self.x - self.target.rect.centerx, self.y - self.target.rect.centery) > self.range:
                self.find_target(enemies)
            # Shoot
            if self.target and (current_time_sec - self.last_shot_time >= self.fire_rate):
                self.shoot(projectiles)
                self.last_shot_time = current_time_sec

    # Abstract method - subclasses must implement
    def shoot(self, projectiles):
        if self.target:
            # Use self.data_manager
            projectile_data = self.data_manager.get_projectile_data(self.projectile_type)
            if projectile_data:
                # Need a way to map projectile_type key to Projectile class
                # We'll handle instantiation in specific Tower classes for now
                # This shoot method in BaseTower might need rethinking or removal if
                # subclasses handle it entirely.
                 pass # Subclasses will implement actual projectile creation
            else:
                print(f"Error: No projectile data found for type '{self.projectile_type}'")

    def load_and_position_image(self, asset_manager, image_path, fallback_size, fallback_color):
        self.image, self.rect = asset_manager.load_image(image_path)
        data = self.data_manager.get_tower_data(self.type_key)
        scale_ratio = data.get("scale_ratio", 0.9) if data else 0.9
        target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))

        if self.image is None:
            print(f"Using fallback for {image_path}")
            self.image = pygame.Surface([fallback_size, fallback_size])
            self.image.fill(fallback_color)
            # Scale fallback image too, just in case fallback_size differs from target
            self.image = pygame.transform.smoothscale(self.image, target_size)
            self.rect = self.image.get_rect()
        else:
            # Scale the loaded image
            loaded_image = self.image # Keep original before scaling
            try:
                self.image = pygame.transform.smoothscale(loaded_image.copy(), target_size)
            except ValueError as e:
                 print(f"Error scaling tower image {image_path}: {e}")
                 self.image = loaded_image # Use unscaled
            self.rect = self.image.get_rect()

        self.rect.center = (self.x, self.y)
        # Now self.image holds the final scaled image/fallback

    def trigger_click_animation(self):
        """Starts the click animation if frames exist."""
        if self.click_animation_frames:
            self.is_animating = True
            self.current_animation_frame_index = 0
            self.last_animation_update = pygame.time.get_ticks()
            self.image = self.click_animation_frames[0] # Show first frame immediately


class BaseProjectile(pygame.sprite.Sprite):
    # Common attributes/methods for all projectiles
    def __init__(self, start_pos, target_enemy, type_key, asset_manager, data_manager):
        super().__init__()
        self.asset_manager = asset_manager
        self.data_manager = data_manager # Store data manager
        self.x, self.y = start_pos
        self.target = target_enemy
        self.type_key = type_key

        # Load data using passed data_manager
        data = self.data_manager.get_projectile_data(type_key)
        if not data:
            print(f"Error: No data found for projectile type '{type_key}'")
            return

        # Set attributes from data
        self.speed = data.get("speed", 200)
        self.damage = data.get("damage", 10)
        # Specific attributes like splash radius handled by subclasses or checked here
        self.splash_radius = data.get("splash_radius", 0) # Default 0 if not defined

        # Load image using data
        image_path = data.get("image", "default_projectile.png")
        scale_ratio = data.get("scale_ratio", 0.3)
        fallback_size_ratio = data.get("fallback_size_ratio", 0.2)
        fallback_color_name = data.get("fallback_color", "YELLOW")
        fallback_size = int(config.TILE_SIZE * fallback_size_ratio)
        fallback_color = config.COLOR_MAP.get(fallback_color_name, config.GREY)
        self.load_and_position_image(asset_manager, image_path, fallback_size, fallback_color)

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
        self.rect.center = (self.x, self.y)

    def update(self, dt, enemies):
        self.move(dt)

    def load_and_position_image(self, asset_manager, image_path, fallback_size, fallback_color):
        self.image, self.rect = asset_manager.load_image(image_path)
        # Use self.data_manager
        data = self.data_manager.get_projectile_data(self.type_key)
        scale_ratio = data.get("scale_ratio", 0.3) if data else 0.3
        target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))

        if self.image is None:
            print(f"Using fallback for {image_path}")
            self.image = pygame.Surface([fallback_size, fallback_size])
            self.image.fill(fallback_color)
            # Scale fallback
            self.image = pygame.transform.smoothscale(self.image, target_size)
            self.rect = self.image.get_rect()
        else:
            # Scale loaded image
            self.image = pygame.transform.smoothscale(self.image, target_size)
            self.rect = self.image.get_rect()

        self.rect.center = (self.x, self.y)

    def on_hit(self, target_enemy, enemies_group, effects_group):
        """Handles the projectile hitting a target. Subclasses must implement.

        Args:
            target_enemy: The primary enemy hit by the projectile.
            enemies_group: The sprite group containing all active enemies.
            effects_group: The sprite group for visual effects.

        Returns:
            bool: True if the projectile should be destroyed after the hit, False otherwise.
        """
        raise NotImplementedError("Projectile subclasses must implement on_hit")


# --- Tower Class (now inherits from BaseTower) ---
class Tower(BaseTower):

    def __init__(self, grid_x, grid_y, asset_manager, data_manager):
        # Pass the type key for this tower
        super().__init__(grid_x, grid_y, type_key="Basic", asset_manager=asset_manager, data_manager=data_manager)
        # Base __init__ now handles loading data and setting attributes

    # Implement the specific shooting action
    def shoot(self, projectiles):
        if self.target:
            # Pass data_manager when creating projectile
            projectile = Projectile(self.rect.center, self.target, type_key="Basic", asset_manager=self.asset_manager, data_manager=self.data_manager)
            projectiles.add(projectile)
            # Use self.data_manager
            tower_data = self.data_manager.get_tower_data(self.type_key)
            if tower_data and tower_data.get("shoot_sound"):
                 shoot_sound_file = tower_data["shoot_sound"]
                 sound = self.asset_manager.load_sound(shoot_sound_file)
                 self.asset_manager.play_sound(sound)


# --- Projectile Class (now inherits from BaseProjectile) ---
class Projectile(BaseProjectile):

    def __init__(self, start_pos, target_enemy, type_key="Basic", asset_manager=None, data_manager=None):
        super().__init__(start_pos, target_enemy, type_key, asset_manager, data_manager)
        # Base __init__ handles loading data

    def on_hit(self, target_enemy, enemies_group, effects_group):
        # Play hit sound
        proj_data = self.data_manager.get_projectile_data(self.type_key)
        if proj_data and proj_data.get("hit_sound"):
             hit_sound = self.asset_manager.load_sound(proj_data["hit_sound"])
             self.asset_manager.play_sound(hit_sound)

        # Apply direct damage
        if target_enemy.alive(): # Check if target still alive before damaging
            target_enemy.take_damage(self.damage)

        # Basic projectile is always destroyed on hit
        return True


# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):

    def __init__(self, path, type_key="Goblin", asset_manager=None, data_manager=None): # Default to Goblin now
        super().__init__()
        self.asset_manager = asset_manager
        self.data_manager = data_manager # Store data manager
        self.path = path
        self.path_index = 0
        self.x, self.y = self.path[0]
        self.type_key = type_key

        # Load data for this enemy type using passed data_manager
        data = self.data_manager.get_enemy_data(type_key) if self.data_manager else None
        if not data:
            print(f"Error: No data found for enemy type '{type_key}'")
            # Set defaults or raise error
            self.speed = 50
            self.health = 50
            self.max_health = 50
            self.reward = 5
            image_path = None # Indicate no static image
            animation_data = None
            scale_ratio = 0.6
            fallback_color_name = "RED"
            self.is_flying = False # Load flying flag
        else:
            # Set attributes from data
            self.speed = data.get("speed", 50)
            self.base_speed = self.speed
            self.health = data.get("health", 50)
            self.max_health = self.health
            # Keep reward attribute, might be used by specific projectiles
            self.reward = data.get("reward", 5)
            image_path = data.get("image")
            animation_data = data.get("animation") # Get animation data
            scale_ratio = data.get("scale_ratio", 0.6) # Load scale ratio
            fallback_color_name = data.get("fallback_color", "RED")
            self.is_flying = data.get("is_flying", False) # Load flying flag

        # List to hold active modifiers
        self.modifiers = []

        # --- Animation or Static Image Loading ---
        self.animation_frames = []
        self.current_frame_index = 0
        self.last_frame_update = pygame.time.get_ticks()
        self.animation_speed = 150 # Default, will be overridden by data

        if animation_data and isinstance(animation_data.get("frames"), list):
            self.animation_speed = animation_data.get("speed", 150)
            target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))
            for frame_filename in animation_data["frames"]:
                # Unpack the tuple here
                image_surface, _ = self.asset_manager.load_image(frame_filename)
                if image_surface: # Check the surface, not the tuple
                    # Scale the actual image surface
                    scaled_frame = pygame.transform.smoothscale(image_surface, target_size)
                    self.animation_frames.append(scaled_frame)
            if not self.animation_frames:
                 self._create_fallback_image(self.asset_manager, fallback_color_name, fallback_size_ratio, scale_ratio)
            else:
                 self.image = self.animation_frames[0]
                 self.rect = self.image.get_rect()

        elif image_path:
            # Load static image
            # Use scale_ratio from data for target size
            target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))
            self.image = self.asset_manager.load_image(image_path)
            if self.image is None:
                 # Need to pass fallback_size_ratio as well
                 self._create_fallback_image(self.asset_manager, fallback_color_name, fallback_size_ratio, scale_ratio)
            else:
                 # Scale static image
                 self.image = pygame.transform.smoothscale(self.image, target_size)
                 self.rect = self.image.get_rect() # Get new rect after scaling

        else:
             # No animation and no static image -> Use fallback
             print(f"Warning: No image or animation defined for {type_key}. Using fallback.")
             # Need to pass fallback_size_ratio as well
             self._create_fallback_image(self.asset_manager, fallback_color_name, fallback_size_ratio, scale_ratio)

        self.rect.center = (self.x, self.y)

        # Path target logic remains same
        if len(self.path) > 1:
             self.target_x, self.target_y = self.path[1]
        else:
             print(f"Warning: Enemy path for {self.type_key} too short.")
             self.target_x, self.target_y = self.x, self.y

    def _create_fallback_image(self, asset_manager, fallback_color_name, fallback_size_ratio, scale_ratio):
        """Helper to create and scale the fallback colored square."""
        # Calculate target size using the scale_ratio intended for the final image
        target_size = (int(config.TILE_SIZE * scale_ratio), int(config.TILE_SIZE * scale_ratio))

        # Create initial surface using fallback ratio
        actual_fallback_size = int(config.TILE_SIZE * fallback_size_ratio)
        fallback_color = config.COLOR_MAP.get(fallback_color_name, config.GREY)
        initial_surface = pygame.Surface([actual_fallback_size, actual_fallback_size])
        initial_surface.fill(fallback_color)

        # Scale fallback image to the target size
        self.image = pygame.transform.smoothscale(initial_surface, target_size)
        self.rect = self.image.get_rect()

    def _animate(self):
        """Handles cycling through animation frames."""
        if not self.animation_frames: # Don't animate if no frames (static image or fallback)
            return

        now = pygame.time.get_ticks()
        if now - self.last_frame_update > self.animation_speed:
            self.last_frame_update = now
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
            # Important: Preserve center when changing image
            center = self.rect.center
            self.image = self.animation_frames[self.current_frame_index]
            self.rect = self.image.get_rect()
            self.rect.center = center

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

    def add_modifier(self, new_modifier):
        """Adds a modifier to the enemy, replacing existing of same type."""
        # Simple replacement logic for now
        # Check if a modifier of the same type already exists
        existing_modifier = None
        for i, mod in enumerate(self.modifiers):
            if isinstance(mod, type(new_modifier)):
                # Remove existing modifier effect before replacing
                mod.remove() # This will also remove it from the list via super().remove()
                # We might need to break here if remove() modified the list during iteration
                # Let's re-find it after potential removal
                found_after_remove = False
                for j, check_mod in enumerate(self.modifiers):
                     if isinstance(check_mod, type(new_modifier)):
                          # Should not happen if remove worked correctly
                          print("Warning: Old modifier not removed correctly?")
                          del self.modifiers[j]
                          found_after_remove = True
                          break
                break # Exit outer loop once type is found and handled

        # Add and apply the new modifier
        self.modifiers.append(new_modifier)
        new_modifier.apply(self) # Apply effect immediately

    def remove_modifier(self, modifier_to_remove):
        """Removes a specific modifier instance."""
        if modifier_to_remove in self.modifiers:
             self.modifiers.remove(modifier_to_remove)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

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
        # Start with the base image (or current animation frame)
        image_to_draw = self.image

        # Apply visual effects from modifiers
        for mod in self.modifiers:
            image_to_draw = mod.apply_visuals(image_to_draw)

        # Draw the (potentially modified) image
        surface.blit(image_to_draw, self.rect)
        # Draw health bar on top
        self.draw_health_bar(surface)

    def update(self, dt):
        # Update modifiers and remove expired ones
        # Iterate over a copy of the list because remove_modifier modifies it
        for mod in self.modifiers[:]:
            mod.update(dt)

        self._animate()
        reached_end = self.move(dt)
        return reached_end

# --- Cannon Tower Class ---
class CannonTower(BaseTower):

    def __init__(self, grid_x, grid_y, asset_manager, data_manager):
        # Pass the type key for this tower
        super().__init__(grid_x, grid_y, type_key="Cannon", asset_manager=asset_manager, data_manager=data_manager)

    # Implement the specific shooting action
    def shoot(self, projectiles):
        if self.target:
            # "Cannon" tower uses "Cannon" projectile
            projectile = CannonProjectile(self.rect.center, self.target, type_key="Cannon", asset_manager=self.asset_manager, data_manager=self.data_manager)
            projectiles.add(projectile)
            # Get sound filename from data
            tower_data = self.data_manager.get_tower_data(self.type_key)
            if tower_data and tower_data.get("shoot_sound"):
                 shoot_sound_file = tower_data["shoot_sound"]
                 sound = self.asset_manager.load_sound(shoot_sound_file)
                 self.asset_manager.play_sound(sound)


# --- Cannon Projectile Class ---
class CannonProjectile(BaseProjectile):

    def __init__(self, start_pos, target_enemy, type_key="Cannon", asset_manager=None, data_manager=None):
        super().__init__(start_pos, target_enemy, type_key, asset_manager, data_manager)

    def on_hit(self, target_enemy, enemies_group, effects_group):
        impact_pos = self.rect.center
        proj_data = self.data_manager.get_projectile_data(self.type_key)

        # Play hit sound
        if proj_data and proj_data.get("hit_sound"):
             hit_sound = self.asset_manager.load_sound(proj_data["hit_sound"])
             self.asset_manager.play_sound(hit_sound)

        # Apply direct damage
        if target_enemy.alive():
            target_enemy.take_damage(self.damage)

        # Apply splash damage
        if self.splash_radius > 0:
            for enemy in enemies_group.sprites():
                # Check if alive AND not the primary target (to avoid double damage from splash)
                if enemy.alive() and enemy is not target_enemy:
                    dist = math.hypot(impact_pos[0] - enemy.rect.centerx, impact_pos[1] - enemy.rect.centery)
                    if dist <= self.splash_radius:
                        enemy.take_damage(self.damage) # Apply splash damage

        # Create visual splash effect
        if proj_data and proj_data.get("splash_image"):
            splash_image_path = proj_data["splash_image"]
            target_diameter = int(self.splash_radius * 2)
            effect_size = (target_diameter, target_diameter)
            effect = Effect(impact_pos, splash_image_path, 200, self.asset_manager, self.data_manager, target_size=effect_size)
            effects_group.add(effect)

        # Cannon projectile is always destroyed on hit
        return True


# --- Ice Tower Class ---
class IceTower(BaseTower):
    def __init__(self, grid_x, grid_y, asset_manager, data_manager):
        super().__init__(grid_x, grid_y, type_key="Ice", asset_manager=asset_manager, data_manager=data_manager)

    def shoot(self, projectiles):
        if self.target:
            projectile = IceProjectile(self.rect.center, self.target, type_key="Ice", asset_manager=self.asset_manager, data_manager=self.data_manager)
            projectiles.add(projectile)
            # Play sound (fetched from data in base class or specific sound here)
            tower_data = self.data_manager.get_tower_data(self.type_key)
            if tower_data and tower_data.get("shoot_sound"):
                 shoot_sound_file = tower_data["shoot_sound"]
                 sound = self.asset_manager.load_sound(shoot_sound_file)
                 self.asset_manager.play_sound(sound)


# --- Ice Projectile Class ---
class IceProjectile(BaseProjectile):
    def __init__(self, start_pos, target_enemy, type_key="Ice", asset_manager=None, data_manager=None):
        super().__init__(start_pos, target_enemy, type_key, asset_manager, data_manager)
        data = self.data_manager.get_projectile_data(type_key)
        self.slow_factor = data.get("slow_factor", 1.0)
        self.slow_duration = data.get("slow_duration", 0)
        # BaseProjectile loads splash_radius, accessible as self.splash_radius

    def on_hit(self, target_enemy, enemies_group, effects_group):
        impact_pos = self.rect.center
        proj_data = self.data_manager.get_projectile_data(self.type_key)

        # Play hit sound
        if proj_data and proj_data.get("hit_sound"):
             hit_sound = self.asset_manager.load_sound(proj_data["hit_sound"])
             self.asset_manager.play_sound(hit_sound)

        # Apply direct damage
        if target_enemy.alive():
            target_enemy.take_damage(self.damage)

        # Apply splash slow effect
        if self.splash_radius > 0:
            for enemy in enemies_group.sprites():
                if enemy.alive(): # Slow applies even to primary target again
                    dist = math.hypot(impact_pos[0] - enemy.rect.centerx, impact_pos[1] - enemy.rect.centery)
                    if dist <= self.splash_radius:
                        slow_mod = SlowModifier(self.slow_factor, self.slow_duration)
                        enemy.add_modifier(slow_mod)

        # Ice projectile is always destroyed on hit
        return True


# --- Visual Effect Class ---
class Effect(pygame.sprite.Sprite):
    """A sprite for temporary visual effects like explosions."""
    def __init__(self, pos, image_path, duration_ms, asset_manager, data_manager, target_size=None):
        super().__init__()
        self.asset_manager = asset_manager
        self.data_manager = data_manager
        # Unpack the tuple from load_image
        image_surface, _ = asset_manager.load_image(image_path)
        self.image = image_surface # Assign the surface to self.image

        if not self.image:
            print(f"Warning: Failed to load effect image {image_path}. Effect won't display.")
            self.kill()
            return

        # Get initial rect from loaded surface before potential scaling
        self.rect = self.image.get_rect()

        if target_size:
            try:
                # Scale the surface stored in self.image
                self.image = pygame.transform.smoothscale(self.image.copy(), target_size)
                self.rect = self.image.get_rect() # Update rect after scaling
            except ValueError as e:
                print(f"Error scaling effect image {image_path} to {target_size}: {e}")

        self.rect.center = pos
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration_ms

    def update(self, dt):
        # Remove the effect after its duration expires
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill() 

class GoldMine(BaseTower):
    def __init__(self, grid_x, grid_y, asset_manager, data_manager):
        super().__init__(grid_x, grid_y, type_key="GoldMine", asset_manager=asset_manager, data_manager=data_manager)

    def shoot(self, projectiles):
        # Gold mine doesn't shoot
        pass 

    def on_click(self, game_state):
        """Called when the gold mine is clicked."""
        if self.click_gold > 0:
            game_state.game.player_money += self.click_gold
            print(f"Collected {self.click_gold} gold!")
            # Potentially add a sound effect here
            # Play click animation
            self.trigger_click_animation()
            return True # Indicate click was handled
        return False 

# --- Bounty Hunter Tower Class ---
class BountyHunterTower(BaseTower):
    def __init__(self, grid_x, grid_y, asset_manager, data_manager):
        super().__init__(grid_x, grid_y, type_key="BountyHunter", asset_manager=asset_manager, data_manager=data_manager)

    def shoot(self, projectiles):
        if self.target:
            projectile = CoinShotProjectile(self.rect.center, self.target, type_key="CoinShot", asset_manager=self.asset_manager, data_manager=self.data_manager)
            projectiles.add(projectile)
            tower_data = self.data_manager.get_tower_data(self.type_key)
            if tower_data and tower_data.get("shoot_sound"):
                 sound = self.asset_manager.load_sound(tower_data["shoot_sound"])
                 self.asset_manager.play_sound(sound)


# --- Coin Shot Projectile Class ---
class CoinShotProjectile(BaseProjectile):
    def __init__(self, start_pos, target_enemy, type_key="CoinShot", asset_manager=None, data_manager=None):
        super().__init__(start_pos, target_enemy, type_key, asset_manager, data_manager)
        proj_data = self.data_manager.get_projectile_data(type_key)
        self.awards_bounty = proj_data.get("awards_bounty_on_kill", False)

    def on_hit(self, target_enemy, enemies_group, effects_group):
        # Play hit sound
        proj_data = self.data_manager.get_projectile_data(self.type_key)
        if proj_data and proj_data.get("hit_sound"):
             sound = self.asset_manager.load_sound(proj_data["hit_sound"])
             self.asset_manager.play_sound(sound)

        bounty_awarded = False
        if target_enemy.alive():
            target_enemy.take_damage(self.damage)
            # Check if this projectile killed the enemy AND awards bounty
            if not target_enemy.alive() and self.awards_bounty:
                 # Award the enemy's base reward value
                 # Need access to game state / player money... this is tricky.
                 # We'll have to handle this reward in the main loop check for now.
                 # Mark the enemy as killed by bounty shot?
                 if hasattr(target_enemy, 'reward') and target_enemy.reward > 0:
                      target_enemy._killed_by_bounty = True # Add flag
                      print(f"Enemy killed by bounty shot! Reward pending.") # Debug

        return True # Destroy projectile 