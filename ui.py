import pygame
import config
from entities import Tower, CannonTower, load_image # Need entity classes for info

class Button:
    """Represents a clickable button in the UI panel."""
    ICON_SIZE = 48 # Size of the tower icon
    PADDING = 10 # Padding around elements

    def __init__(self, y, tower_class, icon_path, name, cost):
        self.tower_class = tower_class
        self.name = name
        self.cost = cost
        self.icon_path = icon_path

        # Button area rectangle
        self.width = config.UI_PANEL_WIDTH - 2 * self.PADDING
        self.height = self.ICON_SIZE + 2 * self.PADDING # Height based on icon + padding
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH + self.PADDING,
                               y,
                               self.width,
                               self.height)

        # Load icon (with fallback color)
        self.icon_image, _ = load_image(icon_path) # Use existing loader
        if self.icon_image is None:
             # Fallback: Create colored square icon
             self.icon_image = pygame.Surface([self.ICON_SIZE, self.ICON_SIZE])
             # Use tower's fallback color if available, else default grey
             fallback_color = getattr(tower_class, 'FALLBACK_COLOR', config.GREY)
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
    def __init__(self, start_y, font):
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH, 0,
                               config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT)
        self.font = font
        self.buttons = []
        self.selected_tower_type = None

        # --- Define Tower Buttons --- Add more tower types here later
        button_y = start_y
        tower_types = [
            (Tower, config.TOWER_ICON, "Basic Tower"),
            (CannonTower, config.CANNON_TOWER_ICON, "Cannon")
            # Add more tuples like (YourTowerClass, config.YOUR_ICON, "Your Name")
        ]

        for tower_class, icon_path, name in tower_types:
            button = Button(button_y,
                            tower_class,
                            icon_path,
                            name,
                            tower_class.COST) # Get cost directly from class
            self.buttons.append(button)
            button_y += button.height + Button.PADDING # Space out buttons

        # Set initial selection (optional)
        if self.buttons:
             self.selected_tower_type = self.buttons[0].tower_class

    def handle_click(self, pos):
        # Check if click is within the panel area
        if not self.rect.collidepoint(pos):
            return False # Click was outside panel

        clicked_button = False
        for button in self.buttons:
            if button.is_clicked(pos):
                self.selected_tower_type = button.tower_class
                print(f"Selected {self.selected_tower_type.__name__}")
                clicked_button = True
                break # Only select one button per click
        return clicked_button # Return True if a button was clicked

    def get_selected_tower(self):
        return self.selected_tower_type

    def draw(self, surface):
        # Draw panel background (optional, could just rely on buttons)
        # pygame.draw.rect(surface, config.UI_BG_COLOR, self.rect)

        # Draw buttons
        for button in self.buttons:
            is_selected = (self.selected_tower_type == button.tower_class)
            button.draw(surface, self.font, selected=is_selected) 