import pygame
import config
# from entities import load_image # Removed

class GameMap:
    # Accept asset_manager
    def __init__(self, grid_width, grid_height, asset_manager):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_size = config.TILE_SIZE
        self.asset_manager = asset_manager

        # Load tile images using asset_manager, unpack the tuple
        grass_image, _ = asset_manager.load_image(config.GRASS_TILE)
        dirt_image, _ = asset_manager.load_image(config.DIRT_TILE)
        
        # Work with the loaded images (surfaces)
        self.grass_tile = grass_image 
        self.dirt_tile = dirt_image

        if not self.grass_tile:
            print("Warning: Grass tile failed to load, using fallback color.")
            self.grass_tile = pygame.Surface([self.tile_size, self.tile_size])
            self.grass_tile.fill(config.COLOR_MAP.get("DARK_GREEN", (0,100,0))) # Use COLOR_MAP
        if not self.dirt_tile:
            print("Warning: Dirt tile failed to load, using fallback color.") # Added warning
            self.dirt_tile = pygame.Surface([self.tile_size, self.tile_size])
            self.dirt_tile.fill(config.COLOR_MAP.get("BROWN", (165,42,42))) # Use COLOR_MAP

        # Ensure tiles are scaled to TILE_SIZE if needed
        # Scale the surfaces directly
        try:
            self.grass_tile = pygame.transform.smoothscale(self.grass_tile, (self.tile_size, self.tile_size))
            self.dirt_tile = pygame.transform.smoothscale(self.dirt_tile, (self.tile_size, self.tile_size))
        except ValueError as e:
            print(f"Error scaling map tiles: {e}")
            # Handle error - maybe revert to unscaled or basic fallback?
            # For now, the fallback surfaces above are already the right size.

        # 0 = path, 1 = buildable, 2 = tower placed
        self.grid = [[1] * grid_width for _ in range(grid_height)] # Default all buildable

        # Define a simple path (list of grid coordinates) - ADJUSTED FOR 16x12 GRID
        self.path_coords = [
            (0, 5), (1, 5), (2, 5), (3, 5), (3, 4), (3, 3),
            (4, 3), (5, 3), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
            (7, 7), (8, 7), (9, 7), (10, 7), (11, 7), (11, 8), (11, 9),
            (12, 9), (13, 9), (14, 9), (15, 9) # Ends at right edge, row 9
            # Old path went up to x=19, which is now out of bounds
        ]
        # Convert path grid coords to pixel coords (center of tile)
        self.pixel_path = []
        for x, y in self.path_coords:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.grid[y][x] = 0 # Mark path tiles
                pixel_x = x * self.tile_size + self.tile_size // 2
                pixel_y = y * self.tile_size + self.tile_size // 2
                self.pixel_path.append((pixel_x, pixel_y))
            else:
                print(f"Warning: Path coordinate ({x},{y}) is outside the grid bounds.")

        if not self.pixel_path:
             print("Error: No valid path coordinates found!")
             # Add fallback path or raise an error
             self.pixel_path = [(self.tile_size // 2, self.grid_height // 2 * self.tile_size + self.tile_size // 2)] # Default to middle left start


    def get_path(self):
        return self.pixel_path

    def is_buildable(self, grid_x, grid_y):
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.grid[grid_y][grid_x] == 1 # 1 means buildable
        return False

    def place_tower(self, grid_x, grid_y):
        if self.is_buildable(grid_x, grid_y):
            self.grid[grid_y][grid_x] = 2 # Mark as tower placed
            return True
        return False

    def draw(self, surface):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                tile_type = self.grid[y][x]
                # Determine which tile image to draw
                if tile_type == 0: # Path
                    tile_image = self.dirt_tile
                else: # Buildable grass (or tower placed - draw grass underneath)
                    tile_image = self.grass_tile

                # Blit the tile image
                surface.blit(tile_image, (x * self.tile_size, y * self.tile_size))

                # Optional: Draw grid lines over the tiles
                # rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                # pygame.draw.rect(surface, config.BLACK, rect, 1) 