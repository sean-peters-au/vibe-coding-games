# data_manager.py (formerly game_data_manager.py)
import json
import os

class DataManager:
    def __init__(self, data_dir="data"):
        self.towers = {}
        self.projectiles = {}
        self.enemies = {}
        self.waves = []
        self._load_all_data(data_dir)
        self._define_class_maps()

    def _load_all_data(self, data_dir):
        """Loads all JSON data files from the specified directory."""
        try:
            self.towers = self._load_json(os.path.join(data_dir, "towers.json"))
            self.projectiles = self._load_json(os.path.join(data_dir, "projectiles.json"))
            self.enemies = self._load_json(os.path.join(data_dir, "enemies.json"))
            self.waves = self._load_json(os.path.join(data_dir, "waves.json"), sort_key='wave')
            print("DataManager: All game data loaded successfully.")
        except FileNotFoundError as e:
            print(f"DataManager Error: {e}. Make sure JSON files exist in '{data_dir}'.")
            raise # Re-raise for Game class to handle
        except json.JSONDecodeError as e:
            print(f"DataManager Error decoding JSON data: {e}. Check JSON file formatting.")
            raise # Re-raise

    def _load_json(self, filepath, sort_key=None):
        """Helper to load a single JSON file."""
        print(f"DataManager: Loading {filepath}...")
        with open(filepath, 'r') as f:
            data = json.load(f)
            if sort_key and isinstance(data, list):
                data.sort(key=lambda item: item.get(sort_key, 0))
            return data

    def _define_class_maps(self):
        """Defines mappings from data keys (strings) to actual classes."""
        # Import entity classes here, just before they are needed
        from entities import (Enemy, Tower, Projectile, CannonTower, CannonProjectile,
                           IceTower, IceProjectile, GoldMine, BountyHunterTower, CoinShotProjectile)

        self.enemy_classes = {
            "Goblin": Enemy,
            "Ogre": Enemy,
            "Dragon": Enemy,
            "Runner": Enemy,
            "Brute": Enemy,
            "Digger": Enemy # Still uses base Enemy class for now
            # Add new enemy classes here (e.g., "Flyer": FlyingEnemy)
        }
        self.tower_classes = {
            "Basic": Tower,
            "Cannon": CannonTower,
            "Ice": IceTower,
            "GoldMine": GoldMine,
            "BountyHunter": BountyHunterTower
        }
        self.projectile_classes = {
            "Basic": Projectile,
            "Cannon": CannonProjectile,
            "Ice": IceProjectile,
            "CoinShot": CoinShotProjectile
            # Add new projectile classes here
        }
        print("DataManager: Class maps defined.")

    # --- Getter methods ---
    def get_tower_data(self, type_key):
        return self.towers.get(type_key)

    def get_projectile_data(self, type_key):
        return self.projectiles.get(type_key)

    def get_enemy_data(self, type_key):
        return self.enemies.get(type_key)
    
    def get_all_tower_data(self):
        return self.towers

    def get_wave_definitions(self):
        return self.waves

    # --- Class Map Getters ---
    def get_enemy_class(self, type_key):
        return self.enemy_classes.get(type_key)

    def get_tower_class(self, type_key):
        return self.tower_classes.get(type_key)

    def get_projectile_class(self, type_key):
        return self.projectile_classes.get(type_key)
