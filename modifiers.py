# modifiers.py
import pygame # For timing

class Modifier:
    """Base class for status effects applied to entities."""
    def __init__(self, duration=None):
        self.duration = duration # None for permanent, > 0 for timed
        self.start_time = pygame.time.get_ticks() if duration else None
        self.target = None # The entity this modifier is attached to
        self.is_expired = False

    def apply(self, target):
        """Apply the modifier's initial effect to the target."""
        self.target = target
        # Subclasses implement specific stat changes here

    def update(self, dt):
        """Update modifier state, typically checking duration."""
        if self.duration is not None and not self.is_expired:
            if pygame.time.get_ticks() - self.start_time >= self.duration * 1000:
                self.is_expired = True
                self.remove()

    def remove(self):
        """Remove the modifier's effect from the target."""
        # Subclasses implement specific stat restoration here
        if self.target:
            self.target.remove_modifier(self)
            # print(f"Removing {self.__class__.__name__} from {self.target}") # Debug

    # Optional: Methods for stacking behavior if needed

class SlowModifier(Modifier):
    """Applies a speed reduction."""
    def __init__(self, slow_factor, duration):
        super().__init__(duration)
        self.slow_factor = slow_factor
        self.original_speed = None

    def apply(self, target):
        super().apply(target)
        if hasattr(target, 'speed') and hasattr(target, 'base_speed'):
            # Store original speed only if not already slowed by this type?
            # For simplicity now, always store base_speed
            self.original_speed = target.base_speed
            target.speed = target.base_speed * self.slow_factor
            # print(f"Applied SlowModifier: Speed -> {target.speed}") # Debug
        else:
            print(f"Warning: Target {target} lacks 'speed' or 'base_speed' for SlowModifier.")
            self.is_expired = True # Cannot apply, mark as expired

    def remove(self):
        if self.target and hasattr(self.target, 'speed') and hasattr(self.target, 'base_speed'):
            # Only restore speed if no other SlowModifiers are active?
            # More complex logic needed for stacking/multiple sources.
            # Simplest: Restore to base speed. If another slow is added,
            # it will recalculate from base speed.
            self.target.speed = self.target.base_speed
            # print(f"Removed SlowModifier: Speed -> {self.target.speed}") # Debug
        super().remove() # Call base remove to detach from target 