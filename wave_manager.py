# wave_manager.py
import pygame
import os
import json
import game_data_manager
from entities import Enemy # Assuming Enemy class is sufficient for now

class WaveManager:
    def __init__(self, waves_filepath="data/waves.json", enemy_class_map=None):
        self.waves = self._load_waves(waves_filepath)
        self.current_wave_number = 0
        self.wave_active = False
        self.wave_data = None # Data for the currently active wave
        self.spawn_groups = [] # List of groups remaining to spawn in current wave
        self.current_group_index = 0
        self.enemies_spawned_in_group = 0
        self.last_spawn_time = 0
        self.total_enemies_in_wave = 0
        self.enemies_spawned_this_wave = 0
        self.enemy_class_map = enemy_class_map if enemy_class_map else {"Goblin": Enemy, "Ogre": Enemy}

    def _load_waves(self, filepath):
        """Loads wave definitions from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                waves = json.load(f)
                # Sort waves just in case they aren't ordered in the file
                waves.sort(key=lambda w: w.get('wave', 0))
                print(f"Loaded {len(waves)} waves from {filepath}")
                return waves
        except FileNotFoundError:
            print(f"Error: Wave data file not found: {filepath}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Could not decode wave data file: {filepath}")
            return []

    def start_next_wave(self):
        """Starts the next available wave."""
        next_wave_num = self.current_wave_number + 1
        wave_found = False
        for wave_def in self.waves:
            if wave_def.get("wave") == next_wave_num:
                self.wave_data = wave_def
                wave_found = True
                break

        if not wave_found:
            print(f"No definition found for wave {next_wave_num} or all waves completed.")
            # Potentially handle game win condition here
            return False # Indicate wave couldn't start

        print(f"Starting Wave {next_wave_num}")
        self.current_wave_number = next_wave_num
        self.wave_active = True
        # Deep copy might be safer if we modify group data during spawn
        self.spawn_groups = list(self.wave_data.get("enemies", [])) 
        self.current_group_index = 0
        self.enemies_spawned_in_group = 0
        self.enemies_spawned_this_wave = 0
        self.last_spawn_time = pygame.time.get_ticks() / 1000.0 # Start timer immediately
        
        # Calculate total enemies for this wave
        self.total_enemies_in_wave = sum(group.get("count", 0) for group in self.spawn_groups)
        print(f"Total enemies in wave {self.current_wave_number}: {self.total_enemies_in_wave}")

        return True # Wave started successfully

    def update(self, dt, game_map, enemies_group):
        """Handles enemy spawning logic for the active wave."""
        if not self.wave_active or not self.spawn_groups:
            return # Wave not active or no more groups to spawn

        current_time = pygame.time.get_ticks() / 1000.0

        # Check if we need to move to the next group
        if self.current_group_index >= len(self.spawn_groups):
            # All groups for this wave have been processed, but wait for enemies
            # We don't set wave_active=False here; main loop checks enemy count
            return 

        current_group = self.spawn_groups[self.current_group_index]
        enemy_type = current_group.get("type")
        count = current_group.get("count", 0)
        spawn_delay = current_group.get("spawn_delay", 1.0)

        # Check if enough time passed to spawn next enemy in this group
        if current_time - self.last_spawn_time >= spawn_delay:
            if self.enemies_spawned_in_group < count:
                # Spawn the enemy
                EnemyClass = self.enemy_class_map.get(enemy_type)
                if EnemyClass:
                    enemy = EnemyClass(game_map.get_path(), type_key=enemy_type)
                    enemies_group.add(enemy)
                    self.enemies_spawned_in_group += 1
                    self.enemies_spawned_this_wave += 1
                    self.last_spawn_time = current_time # Reset timer
                    # print(f"Spawned {enemy_type} ({self.enemies_spawned_in_group}/{count}) Group {self.current_group_index+1}/{len(self.spawn_groups)}") # Debug
                else:
                    print(f"Error: Class not found for enemy type '{enemy_type}'")
                    # Skip this enemy type or handle error
                    # For now, just move past this spawn attempt
                    self.last_spawn_time = current_time 

            # Check if current group is finished
            if self.enemies_spawned_in_group >= count:
                self.current_group_index += 1
                self.enemies_spawned_in_group = 0
                # Don't reset last_spawn_time here, allow delay before next group starts
                # print(f"Finished group {self.current_group_index}. Moving to next.")

    def is_wave_complete(self):
        """Checks if all enemies for the current wave have been spawned."""
        return self.enemies_spawned_this_wave >= self.total_enemies_in_wave

    def is_wave_active(self):
         return self.wave_active

    def end_wave(self):
         self.wave_active = False
         self.wave_data = None
         self.spawn_groups = []
         print(f"Wave {self.current_wave_number} ended.") 