import pygame
import config
from entities import Tower, CannonTower, IceTower

class Button:
    """Represents a clickable button in the UI panel."""
    ICON_SIZE = 40 # Reduced from 48
    PADDING = 8 # Reduced from 10

    def __init__(self, y, tower_key, icon_path, name, cost, fallback_color_name, asset_manager):
        self.tower_key = tower_key # Store the key
        self.name = name
        self.cost = cost
        self.icon_path = icon_path
        self.fallback_color_name = fallback_color_name # Store the name
        self.asset_manager = asset_manager # Store it

        # Button area rectangle
        self.width = config.UI_PANEL_WIDTH - 2 * self.PADDING
        self.height = self.ICON_SIZE + 4 * self.PADDING # Make button taller to fit text
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH + self.PADDING,
                               y,
                               self.width,
                               self.height)

        # Load icon using asset_manager, unpack the tuple
        icon_surface, icon_rect_from_load = asset_manager.load_image(icon_path)

        # Use the loaded surface (or create fallback)
        if icon_surface is None:
            # Fallback: Create colored square icon
            self.icon_image = pygame.Surface([self.ICON_SIZE, self.ICON_SIZE])
            fallback_color = config.COLOR_MAP.get(self.fallback_color_name, config.GREY)
            self.icon_image.fill(fallback_color)
            # Scale fallback icon (already ICON_SIZE, maybe redundant but safe)
            self.icon_image = pygame.transform.smoothscale(self.icon_image, (self.ICON_SIZE, self.ICON_SIZE))
        else:
            # Scale loaded icon if needed
            try:
                self.icon_image = pygame.transform.smoothscale(icon_surface.copy(), (self.ICON_SIZE, self.ICON_SIZE))
            except ValueError as e:
                 print(f"Error scaling button icon {icon_path}: {e}")
                 # Fallback to unscaled if scaling fails?
                 self.icon_image = icon_surface # Use unscaled original

        # Position icon within the button rect (slightly higher)
        # Get rect from the final self.icon_image
        self.icon_rect = self.icon_image.get_rect(center=(self.rect.centerx, self.rect.top + self.ICON_SIZE // 2 + self.PADDING))

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

        # Position text below icon, within button bounds
        name_rect = name_text.get_rect(center=(self.rect.centerx, self.icon_rect.bottom + self.PADDING * 1.5))
        cost_rect = cost_text.get_rect(center=(self.rect.centerx, name_rect.bottom + self.PADDING))

        surface.blit(name_text, name_rect)
        surface.blit(cost_text, cost_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class UIPanel:
    """Manages all UI elements, including status bar, buttons, prompts."""
    def __init__(self, data_manager, start_y, font, asset_manager):
        self.rect = pygame.Rect(config.GAME_AREA_WIDTH, 0,
                               config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT)
        self.font = font
        self.buttons = []
        self.selected_tower_key = None
        self.data_manager = data_manager
        self.asset_manager = asset_manager

        # --- Load Status Icons ---
        self.status_font = pygame.font.SysFont(None, 28) # Font for status bar
        self.prompt_font = pygame.font.SysFont(None, 24) # Font for prompts
        icon_size = (24, 24)
        self.heart_icon = self._load_scaled_icon(config.HEART_ICON, icon_size)
        self.coin_icon = self._load_scaled_icon(config.COIN_ICON, icon_size)
        self.next_wave_icon = self._load_scaled_icon(config.NEXT_WAVE_ICON, icon_size)

        # --- Define Tower Buttons from Data ---
        button_y = start_y
        # Get tower data using DataManager
        tower_data = self.data_manager.get_all_tower_data()
        for tower_key, data in tower_data.items():
            button = Button(button_y,
                            tower_key,
                            data.get("icon", "default_icon.png"),
                            data.get("name", "Unknown Tower"),
                            data.get("cost", 9999),
                            data.get("fallback_color", "GREY"),
                            asset_manager # Pass asset_manager to Button
                           )
            self.buttons.append(button)
            button_y += button.height + Button.PADDING

        # Set initial selection (key)
        if self.buttons:
             self.selected_tower_key = self.buttons[0].tower_key # Store key

    def _load_scaled_icon(self, icon_path, size):
        """Loads and scales an icon using the AssetManager."""
        image, _ = self.asset_manager.load_image(icon_path)
        if image:
            try:
                return pygame.transform.smoothscale(image.copy(), size)
            except ValueError as e:
                print(f"UI Panel Error scaling icon {icon_path}: {e}")
        return None

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

    def draw(self, surface, health, money, wave_num, is_wave_active):
        # Draw Tower Selection Panel Background (Optional)
        # pygame.draw.rect(surface, config.UI_BG_COLOR, self.rect)

        # Draw Tower Buttons
        for button in self.buttons:
            is_selected = (self.selected_tower_key == button.tower_key)
            # Pass the general UI font (self.font) to buttons
            button.draw(surface, self.font, selected=is_selected)

        # Draw Status Bar
        self._draw_status_bar(surface, health, money, wave_num)

        # Draw Wave Prompt
        if not is_wave_active and health > 0:
            self._draw_wave_prompt(surface)

    def _draw_status_bar(self, surface, health, money, wave):
        """Draws the top status bar with icons and text."""
        bar_height = 40
        # Draw only over the game area, not the selection panel
        bar_rect = pygame.Rect(0, 0, config.GAME_AREA_WIDTH, bar_height)
        pygame.draw.rect(surface, config.STATUS_BAR_BG_COLOR, bar_rect)

        padding = 10
        icon_text_padding = 5
        current_x = padding

        # Health
        if self.heart_icon:
            surface.blit(self.heart_icon, (current_x, (bar_height - self.heart_icon.get_height()) // 2))
            current_x += self.heart_icon.get_width() + icon_text_padding
        health_text = self.status_font.render(f"{health}", True, config.WHITE)
        health_rect = health_text.get_rect(midleft=(current_x, bar_height // 2))
        surface.blit(health_text, health_rect)
        current_x += health_rect.width + padding * 2

        # Money
        if self.coin_icon:
            surface.blit(self.coin_icon, (current_x, (bar_height - self.coin_icon.get_height()) // 2))
            current_x += self.coin_icon.get_width() + icon_text_padding
        money_text = self.status_font.render(f"{money}", True, config.WHITE)
        money_rect = money_text.get_rect(midleft=(current_x, bar_height // 2))
        surface.blit(money_text, money_rect)
        current_x += money_rect.width + padding * 2

        # Wave
        wave_text = self.status_font.render(f"Wave: {wave}", True, config.WHITE)
        wave_rect = wave_text.get_rect(midright=(config.GAME_AREA_WIDTH - padding, bar_height // 2))
        surface.blit(wave_text, wave_rect)

    def _draw_wave_prompt(self, surface):
        """Draws the prompt to start the next wave."""
        prompt_y = config.SCREEN_HEIGHT - 30
        prompt_text = self.prompt_font.render("Next Wave (SPACE)", True, config.WHITE)
        prompt_rect = prompt_text.get_rect(center=(config.GAME_AREA_WIDTH // 2, prompt_y))

        if self.next_wave_icon:
            icon_rect = self.next_wave_icon.get_rect(midright=(prompt_rect.left - 5, prompt_y))
            surface.blit(self.next_wave_icon, icon_rect)
            surface.blit(prompt_text, prompt_rect)
        else:
            surface.blit(prompt_text, prompt_rect) 