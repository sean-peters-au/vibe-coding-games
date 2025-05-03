import pygame
import config
import random

class GameMap:
    # Accept asset_manager
    def __init__(self, grid_width, grid_height, asset_manager):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_size = config.TILE_SIZE
        self.asset_manager = asset_manager
        self.grid = [[1] * grid_width for _ in range(grid_height)] # Start all buildable
        self.path_coords = [] # List of (x,y) grid coords
        self.pixel_path = [] # List of (x,y) pixel coords (center of tile)

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

        # Generate the initial path
        self.regenerate_path()

    def _generate_random_path(self):
        """Generates a list of (x,y) grid coordinates for a random path."""
        # Start at a random row in the first column, avoiding row 0
        start_y = random.randint(1, self.grid_height - 2)
        current_x, current_y = 0, start_y
        path_coords = [(current_x, current_y)] # Start the path list
        visited_coords = set(path_coords) # Keep track to avoid simple loops

        while current_x < self.grid_width - 1:
            possible_moves = []
            # Prioritize right
            if current_x + 1 < self.grid_width:
                possible_moves.extend(['right'] * 5)
            # Check bounds and avoid row 0
            if current_y - 1 >= 1: possible_moves.append('up')
            if current_y + 1 < self.grid_height: possible_moves.append('down')

            # --- Find a valid next step (not revisiting immediately) ---
            next_x, next_y = -1, -1
            valid_moves_found = False
            shuffled_moves = random.sample(possible_moves, len(possible_moves))

            for move in shuffled_moves:
                temp_x, temp_y = current_x, current_y
                if move == 'right': temp_x += 1
                elif move == 'up': temp_y -= 1
                elif move == 'down': temp_y += 1
                
                # Check bounds and ensure not immediately revisiting
                if 0 <= temp_x < self.grid_width and 1 <= temp_y < self.grid_height and (temp_x, temp_y) not in visited_coords:
                    next_x, next_y = temp_x, temp_y
                    valid_moves_found = True
                    break # Found a valid move
            
            if valid_moves_found:
                current_x, current_y = next_x, next_y
                path_coords.append((current_x, current_y))
                visited_coords.add((current_x, current_y))
            else:
                # If stuck (no valid non-visited moves), try forcing right even if visited
                print("Warning: Path generation got potentially stuck, forcing right.")
                next_x = current_x + 1
                if next_x < self.grid_width:
                    current_x = next_x
                    path_coords.append((current_x, current_y))
                    visited_coords.add((current_x, current_y))
                else:
                    print("Error: Path generation failed to reach end after forcing right.")
                    return None # Indicate failure

        return path_coords

    def regenerate_path(self, towers_group=None, game_state=None):
        """Generates a new random path and updates the grid, handling tower conflicts."""
        print("Map: Regenerating path...")
        new_path_coords = self._generate_random_path()

        if not new_path_coords:
             print("Path generation failed, keeping old path.")
             return # Don't change anything if generation failed

        # Reset the grid to all buildable first
        self.grid = [[1] * self.grid_width for _ in range(self.grid_height)]

        # Auto-sell towers clashing with the new path
        towers_to_sell = []
        new_path_set = set(new_path_coords)
        if towers_group and game_state: # Check if necessary objects were passed
             for tower in towers_group:
                  if (tower.grid_x, tower.grid_y) in new_path_set:
                       towers_to_sell.append(tower)
             
             for tower in towers_to_sell:
                  print(f"Path conflict: Auto-selling tower {tower.type_key} at ({tower.grid_x}, {tower.grid_y})")
                  refund_amount = int(tower.cost * 1.0) # 100% refund for auto-sell
                  game_state.game.player_money += refund_amount
                  # Don't need to call self.sell_tower as we are resetting the grid anyway
                  tower.kill()
                  # Play sound?
                  sell_sound = tower.asset_manager.load_sound(config.SELL_SOUND)
                  tower.asset_manager.play_sound(sell_sound)

        # Now apply the new path to the grid
        self.path_coords = new_path_coords
        for x, y in self.path_coords:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.grid[y][x] = 0 # Mark as path
            else:
                 print(f"Warning: Generated path coord ({x},{y}) out of bounds.")

        # Re-apply remaining (non-sold) tower locations to the grid
        if towers_group:
             for tower in towers_group:
                  if 0 <= tower.grid_x < self.grid_width and 0 <= tower.grid_y < self.grid_height:
                       # Check if the tower's location is NOT part of the new path before marking
                       if self.grid[tower.grid_y][tower.grid_x] != 0:
                            self.grid[tower.grid_y][tower.grid_x] = 2 # Mark as tower placed
                       else:
                            # This should ideally not happen if auto-sell worked
                            print(f"Warning: Tower {tower.type_key} at ({tower.grid_x}, {tower.grid_y}) survived auto-sell but is on path.")

        # Convert grid path to pixel path
        self.pixel_path = []
        for x, y in self.path_coords:
            pixel_x = x * self.tile_size + self.tile_size // 2
            pixel_y = y * self.tile_size + self.tile_size // 2
            self.pixel_path.append((pixel_x, pixel_y))

        if not self.pixel_path:
             print("Error: Regenerated path resulted in empty pixel path! Using fallback.")
             # Implement fallback path creation here (e.g., straight line)
             fallback_y = self.grid_height // 2
             self.path_coords = []
             self.pixel_path = []
             for x in range(self.grid_width):
                  if 0 <= x < self.grid_width and 0 <= fallback_y < self.grid_height:
                       self.grid[fallback_y][x] = 0
                       self.path_coords.append((x, fallback_y))
                       self.pixel_path.append((x * self.tile_size + self.tile_size // 2, fallback_y * self.tile_size + self.tile_size // 2))

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

    def sell_tower(self, grid_x, grid_y):
        """Marks a grid cell as buildable again."""
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
             # Only allow selling if a tower is actually there (grid value 2)
             if self.grid[grid_y][grid_x] == 2:
                  self.grid[grid_y][grid_x] = 1 # Set back to buildable
                  print(f"Map: Sold tower at ({grid_x}, {grid_y})")
                  return True
             else:
                  print(f"Map: Attempted to sell at ({grid_x}, {grid_y}), but no tower found (value={self.grid[grid_y][grid_x]}).")
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