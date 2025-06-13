import unittest
import math
from unittest.mock import MagicMock

# Assuming modules.building_system is in sys.path or accessible
from modules.building_system import (
    BUILDING_CONFIG,
    get_building_config,
    calculate_upgrade_cost,
    calculate_upgrade_time,
    apply_building_effects,
    _BUILDING_KEY_TO_FIELD
)

class TestBuildingSystem(unittest.TestCase):

    def setUp(self):
        # Mock player data for testing purposes
        self.player_data = {
            "user_id": 12345,
            "game_name": "TestPlayer",
            "base_level": 1,
            "lumber_house_level": 1,
            "mine_level": 1,
            "warehouse_level": 1, # maps to farm
            "gold_mine_level": 1, # conceptually distinct from mine_level for stone
            "power_plant_level": 1,
            "barracks_level": 1,
            "research_lab_level": 1,
            "hospital_level": 1,
            "workshop_level": 1,
            "jail_level": 1,
            "resources_wood": 10000,
            "resources_stone": 10000,
            "resources_food": 10000,
            "resources_gold": 10000,
            "resources_energy": 10000,
        }

    def test_get_building_config(self):
        config = get_building_config("town_hall")
        self.assertIsNotNone(config)
        self.assertEqual(config["name"], "Town Hall")

        non_existent_config = get_building_config("non_existent")
        self.assertIsNone(non_existent_config)

    def test_calculate_sawmill_upgrade_cost(self):
        # Test Sawmill (lumber_house) upgrade cost at level 1 to 2
        initial_level = 1
        self.player_data["lumber_house_level"] = initial_level
        
        sawmill_config = get_building_config("lumber_house")
        expected_wood_cost = math.ceil(sawmill_config["base_costs"]["wood"] * (sawmill_config["cost_multiplier"] ** initial_level))
        expected_stone_cost = math.ceil(sawmill_config["base_costs"]["stone"] * (sawmill_config["cost_multiplier"] ** initial_level))

        costs = calculate_upgrade_cost(self.player_data, "lumber_house")
        self.assertEqual(costs["wood"], expected_wood_cost)
        self.assertEqual(costs["stone"], expected_stone_cost)

        # Test Sawmill upgrade cost at level 5 to 6
        level_five = 5
        self.player_data["lumber_house_level"] = level_five
        expected_wood_cost_lvl5 = math.ceil(sawmill_config["base_costs"]["wood"] * (sawmill_config["cost_multiplier"] ** level_five))
        expected_stone_cost_lvl5 = math.ceil(sawmill_config["base_costs"]["stone"] * (sawmill_config["cost_multiplier"] ** level_five))

        costs_lvl5 = calculate_upgrade_cost(self.player_data, "lumber_house")
        self.assertEqual(costs_lvl5["wood"], expected_wood_cost_lvl5)
        self.assertEqual(costs_lvl5["stone"], expected_stone_cost_lvl5)

    def test_calculate_barracks_upgrade_time(self):
        # Test Barracks upgrade time at level 1 to 2 (without Town Hall effect)
        initial_level = 1
        self.player_data["barracks_level"] = initial_level
        self.player_data["base_level"] = 1 # Town Hall level is 1

        barracks_config = get_building_config("barracks")
        expected_time = math.ceil(barracks_config["base_time"] * (barracks_config["time_multiplier"] ** initial_level))

        time = calculate_upgrade_time(self.player_data, "barracks")
        self.assertEqual(time, expected_time)

        # Test Barracks upgrade time at level 5 to 6 (with Town Hall effect)
        level_five = 5
        self.player_data["barracks_level"] = level_five
        self.player_data["base_level"] = 5 # Town Hall level is 5

        th_config = get_building_config("town_hall")
        th_reduction_per_level = th_config["effects"]["upgrade_time_reduction_per_level"]
        total_th_reduction = self.player_data["base_level"] * th_reduction_per_level
        total_th_reduction = min(total_th_reduction, 0.90) # Apply cap

        expected_time_lvl5_raw = barracks_config["base_time"] * (barracks_config["time_multiplier"] ** level_five)
        expected_time_lvl5_reduced = expected_time_lvl5_raw * (1 - total_th_reduction)

        time_lvl5 = calculate_upgrade_time(self.player_data, "barracks")
        self.assertEqual(time_lvl5, math.ceil(expected_time_lvl5_reduced))

    def test_apply_sawmill_effects(self):
        # Test Sawmill effects at level 1
        self.player_data["lumber_house_level"] = 1
        effects = apply_building_effects(self.player_data)
        self.assertEqual(effects["wood_production_per_hour"], 10)

        # Test Sawmill effects at level 5
        self.player_data["lumber_house_level"] = 5
        effects_lvl5 = apply_building_effects(self.player_data)
        self.assertEqual(effects_lvl5["wood_production_per_hour"], 50)

    def test_apply_barracks_effects(self):
        # Test Barracks effects at level 1
        self.player_data["barracks_level"] = 1
        effects = apply_building_effects(self.player_data)
        self.assertEqual(effects["infantry_training_time_reduction"], 0.05) # 5%
        self.assertNotIn("artillery", effects["unlocked_units"])
        self.assertNotIn("tank", effects["unlocked_units"])

        # Test Barracks effects at level 5 (unlocks artillery)
        self.player_data["barracks_level"] = 5
        effects_lvl5 = apply_building_effects(self.player_data)
        self.assertEqual(effects_lvl5["infantry_training_time_reduction"], 0.25) # 5% * 5 = 25%
        self.assertIn("artillery", effects_lvl5["unlocked_units"])
        self.assertNotIn("tank", effects_lvl5["unlocked_units"])

        # Test Barracks effects at level 10 (unlocks tank)
        self.player_data["barracks_level"] = 10
        effects_lvl10 = apply_building_effects(self.player_data)
        self.assertEqual(effects_lvl10["infantry_training_time_reduction"], 0.50) # 5% * 10 = 50%
        self.assertIn("artillery", effects_lvl10["unlocked_units"])
        self.assertIn("tank", effects_lvl10["unlocked_units"])

if __name__ == '__main__':
    unittest.main() 