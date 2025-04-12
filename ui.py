import pygame
import config
from entities import Tower, CannonTower, IceTower, load_image # Need entity classes for info

class Button:
    """Represents a clickable button in the UI panel."""
    ICON_SIZE = 48 # Size of the tower icon
    PADDING = 10 # Padding around elements

    def __init__(self, y, tower_key, icon_path, name, cost, fallback_color_name):
        self.tower_key = tower_key # Store the key
        self.name = name
        self.cost = cost
        self.icon_path = icon_path
        self.fallback_color_name = fallback_color_name # Store the name

        # Button area rectangle
        self.width = config.UI_PANEL_WIDTH - 2 * self.PADDING
        self.height = self.ICON_SIZE + 2 * self.PADDING # Height based on icon + padding
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH + self.PADDING,
                               y,
                               self.width,
                               self.height)

        # Load icon (with fallback color)
        self.icon_image, _ = load_image(icon_path)
        if self.icon_image is None:
             # Fallback: Create colored square icon
             self.icon_image = pygame.Surface([self.ICON_SIZE, self.ICON_SIZE])
             # Use the passed fallback color name and COLOR_MAP
             fallback_color = config.COLOR_MAP.get(self.fallback_color_name, config.GREY)
             self.icon_image.fill(fallback_color)
        else:
             # Scale loaded icon if needed
             self.icon_image = pygame.transform.scale(self.icon_image, (self.ICON_SIZE, self.ICON_SIZE))

        # Position icon within the button rect
        self.icon_rect = self.icon_image.get_rect(center=(self.rect.centerx, self.rect.centery - self.PADDING // 2)) # Center icon slightly above center line

    def draw(self, surface, font, selected=False):
        # Draw button background
        pygame.draw.rect(surface, config.UI_BG_COLOR, self.rect)

        # Draw border (highlight if selected)
        border_color = config.UI_HIGHLIGHT_COLOR if selected else config.UI_BORDER_COLOR
        border_width = 2 if selected else 1
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw icon
        surface.blit(self.icon_image, self.icon_rect)

        # Draw tower name and cost text below icon
        name_text = font.render(f"{self.name}", True, config.WHITE)
        cost_text = font.render(f"Cost: {self.cost}", True, config.WHITE)

        name_rect = name_text.get_rect(center=(self.rect.centerx, self.icon_rect.bottom + self.PADDING))
        cost_rect = cost_text.get_rect(center=(self.rect.centerx, name_rect.bottom + self.PADDING // 2))

        surface.blit(name_text, name_rect)
        surface.blit(cost_text, cost_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class UIPanel:
    """Manages the UI panel on the right side."""
    def __init__(self, tower_data, start_y, font):
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH, 0,
                               config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT)
        self.font = font
        self.buttons = []
        self.selected_tower_key = None
        self.tower_class_map = { # Map name from data to actual class
            "Basic": Tower,
            "Cannon": CannonTower,
            "Ice": IceTower # Add Ice Tower mapping
            # Add future tower classes here
        }

        # --- Define Tower Buttons from Data ---
        button_y = start_y
        # Iterate through the loaded tower_data dictionary
        for tower_key, data in tower_data.items():
            tower_class = self.tower_class_map.get(tower_key) # Get class from map
            if not tower_class:
                print(f"Warning: No class found for tower key '{tower_key}' in tower_class_map.")
                continue

            button = Button(button_y,
                            tower_key, # Pass tower_key instead of class to Button
                            data.get("icon", "default_icon.png"), # Get icon path from data
                            data.get("name", "Unknown Tower"), # Get name from data
                            data.get("cost", 9999), # Get cost from data
                            data.get("fallback_color", "GREY") # Pass fallback color name
                           )
            self.buttons.append(button)
            button_y += button.height + Button.PADDING

        # Set initial selection (key)
        if self.buttons:
             self.selected_tower_key = self.buttons[0].tower_key # Store key

    def handle_click(self, pos):
        # Check if click is within the panel area
        if not self.rect.collidepoint(pos):
            return False # Click was outside panel

        clicked_button = False
        for button in self.buttons:
            if button.is_clicked(pos):
                self.selected_tower_key = button.tower_key # Store selected key
                print(f"Selected {self.selected_tower_key}")
                clicked_button = True
                break # Only select one button per click
        return clicked_button # Return True if a button was clicked

    def get_selected_tower_key(self):
        """Returns the string key of the selected tower type."""
        return self.selected_tower_key

    def draw(self, surface):
        # Draw panel background (optional, could just rely on buttons)
        # pygame.draw.rect(surface, config.UI_BG_COLOR, self.rect)

        # Draw buttons
        for button in self.buttons:
            # Check selection based on key
            is_selected = (self.selected_tower_key == button.tower_key)
            button.draw(surface, self.font, selected=is_selected) 