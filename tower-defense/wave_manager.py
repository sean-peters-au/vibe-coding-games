# wave_manager.py
import pygame
import os
import json
import game_data_manager
import config
from entities import Enemy

class WaveManager:
    def __init__(self, data_manager, asset_manager, waves_filepath="data/waves.json"):
        self.data_manager = data_manager # Store DataManager
        self.asset_manager = asset_manager
        # Load waves using DataManager
        self.waves = data_manager.get_wave_definitions()
        # Sort waves just in case (DataManager might already do this)
        self.waves.sort(key=lambda w: w.get('wave', 0))
        print(f"WaveManager initialized with {len(self.waves)} waves.")

        # Initialize wave number based on debug setting (or 0)
        self.current_wave_number = config.DEBUG_STARTING_WAVE - 1
        self.wave_active = False
        self.wave_data = None # Data for the currently active wave
        self.spawn_groups = [] # List of groups remaining to spawn in current wave
        self.current_group_index = 0
        self.enemies_spawned_in_group = 0
        self.last_spawn_time = 0
        self.total_enemies_in_wave = 0
        self.enemies_spawned_this_wave = 0
        # Get enemy class map from data_manager
        self.enemy_class_map = self.data_manager.enemy_classes
        self.between_waves_timer = 0.0 # Timer for delay between waves
        self.waiting_for_next_wave = False # Flag indicating delay is active

    def start_next_wave(self):
        """Starts the next available wave."""
        # Look for the wave number *after* the current one
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
        """Handles spawning and inter-wave delay timing."""
        # Handle inter-wave delay
        if self.waiting_for_next_wave:
            self.between_waves_timer -= dt
            if self.between_waves_timer <= 0:
                self.waiting_for_next_wave = False
                self.start_next_wave() # Automatically start next wave
            else:
                return # Still waiting, don't spawn

        # Spawning logic (only runs if wave active and not waiting)
        if not self.wave_active or not self.spawn_groups:
            return

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
                # Spawning logic uses self.enemy_class_map which is now set correctly
                EnemyClass = self.enemy_class_map.get(enemy_type)
                if EnemyClass:
                    enemy = EnemyClass(game_map.get_path(), type_key=enemy_type, asset_manager=self.asset_manager, data_manager=self.data_manager)
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
         print(f"Wave {self.current_wave_number} ended. Starting delay...")
         # Start the timer for the delay before the next wave
         self.between_waves_timer = config.INTER_WAVE_DELAY
         self.waiting_for_next_wave = True

    def get_wave_definitions(self):
        return self.waves

    def get_current_wave_reward(self):
        """Returns the reward amount for the currently completed wave."""
        if self.wave_data:
            return self.wave_data.get("reward", 0)
        # Find the wave definition for the current number if wave_data is already cleared
        for wave_def in self.waves:
             if wave_def.get("wave") == self.current_wave_number:
                  return wave_def.get("reward", 0)
        return 0 # Default if not found

# Remove old global functions and variable 