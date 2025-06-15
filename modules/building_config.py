# Mapping from BUILDING_CONFIG keys to sheet field names
_BUILDING_KEY_TO_FIELD = {
    "base": "base_level",
    "lumber_house": "lumber_house_level",
    "mine": "mine_level", # Stone production
    "farm": "warehouse_level", # Food production (called Farm in doc, Warehouse in sheet/code)
    "gold_mine": "mine_level", # Gold production (shares mine_level with stone production currently)
    "power_plant": "power_plant_level",
    "barracks": "barracks_level",
    "research_lab": "research_lab_level",
    "hospital": "hospital_level",
    "workshop": "workshop_level",
    "jail": "jail_level",
}

# Mapping from sheet field names to BUILDING_CONFIG keys for display in build_menu
_FIELD_TO_BUILDING_KEY = {v: k for k, v in _BUILDING_KEY_TO_FIELD.items()}

BUILDING_CONFIG = {
    "base": {
        "key": "base",
        "name": "Base",
        "emoji": "🏠",
        "max_level": 20,
        "base_costs": {"wood": 100, "stone": 80, "food": 50, "gold": 20, "energy": 10},
        "base_time": 30, # minutes
        "cost_multiplier": 1.15,
        "time_multiplier": 1.2,
        "effects": {
            "upgrade_time_reduction_per_level": 0.05, # 5% reduction per level
            "build_slots_unlock_levels": [5, 10, 15, 20],
            "power_bonus_per_level": 100
        },
        "unlock_requirements": {}
    },
    "lumber_house": {
        "key": "lumber_house",
        "name": "Lumber House",
        "emoji": "🪓",
        "max_level": 20,
        "base_costs": {"wood": 50, "stone": 30, "food": 10, "gold": 5, "energy": 2},
        "base_time": 10, # minutes
        "cost_multiplier": 1.12,
        "time_multiplier": 1.18,
        "effects": {
            "wood_production_per_level": 10,
            "power_bonus_per_level": 50
        },
        "unlock_requirements": {}
    },
    "mine": { # This is for Quarry (stone) and Gold Mine (gold) as they share 'mine_level'
        "key": "mine", # Will be used for both "Quarry" and "Gold Mine" conceptual buildings
        "name": "Mine",
        "emoji": "⛏️",
        "max_level": 20,
        "base_costs": {"wood": 40, "stone": 60, "food": 10, "gold": 8, "energy": 3},
        "base_time": 10, # minutes
        "cost_multiplier": 1.12,
        "time_multiplier": 1.18,
        "effects": {
            "stone_production_per_level": 10,
            "power_bonus_per_level": 50
        },
        "unlock_requirements": {}
    },
    "farm": { # This is for Farm (food) as it maps to 'warehouse_level'
        "key": "farm",
        "name": "Farm",
        "emoji": "🧺",
        "max_level": 20,
        "base_costs": {"wood": 30, "stone": 20, "food": 50, "gold": 4, "energy": 1},
        "base_time": 10, # minutes
        "cost_multiplier": 1.12,
        "time_multiplier": 1.18,
        "effects": {
            "food_production_per_level": 10
        },
        "unlock_requirements": {}
    },
    "gold_mine": { # Separate conceptual building, but maps to 'mine_level'
        "key": "gold_mine",
        "name": "Gold Mine",
        "emoji": "💰", # using gold emoji for Gold Mine
        "max_level": 20,
        "base_costs": {"wood": 60, "stone": 50, "food": 20, "gold": 100, "energy": 5},
        "base_time": 15, # minutes
        "cost_multiplier": 1.14,
        "time_multiplier": 1.2,
        "effects": {
            "gold_production_per_level": 5
        },
        "unlock_requirements": {}
    },
    "power_plant": {
        "key": "power_plant",
        "name": "Power Plant",
        "emoji": "🔋",
        "max_level": 20,
        "base_costs": {"wood": 70, "stone": 70, "food": 30, "gold": 30, "energy": 10},
        "base_time": 20, # minutes
        "cost_multiplier": 1.13,
        "time_multiplier": 1.19,
        "effects": {
            "energy_production_per_level": 5,
            "power_bonus_per_level": 100
        },
        "unlock_requirements": {}
    },
    "barracks": {
        "key": "barracks",
        "name": "Barracks",
        "emoji": "🪖",
        "max_level": 20,
        "base_costs": {"wood": 80, "stone": 60, "food": 40, "gold": 25, "energy": 15},
        "base_time": 20, # minutes
        "cost_multiplier": 1.18,
        "time_multiplier": 1.25,
        "effects": {
            "infantry_training_time_reduction_per_level": 0.05,
            "power_bonus_per_level": 75,
            "unlocks": {
                "artillery": 5,
                "tank": 10,
                "helicopter": 15,
                "jet": 20
            }
        },
        "unlock_requirements": {}
    },
    "research_lab": {
        "key": "research_lab",
        "name": "Research Lab",
        "emoji": "🧪",
        "max_level": 20,
        "base_costs": {"wood": 75, "stone": 75, "food": 50, "gold": 40, "energy": 20},
        "base_time": 25, # minutes
        "cost_multiplier": 1.17,
        "time_multiplier": 1.24,
        "effects": {
            "research_time_reduction_per_level": 0.05,
            "power_bonus_per_level": 75,
            "unlocks": {
                "tech_tiers": [5, 10, 15, 20]
            }
        },
        "unlock_requirements": {}
    },
    "hospital": {
        "key": "hospital",
        "name": "Hospital",
        "emoji": "🏥",
        "max_level": 20,
        "base_costs": {"wood": 60, "stone": 50, "food": 30, "gold": 20, "energy": 10},
        "base_time": 15, # minutes
        "cost_multiplier": 1.16,
        "time_multiplier": 1.22,
        "effects": {
            "healing_time_reduction_per_level": 0.05,
            "capacity_increase_per_level": 10,
            "power_bonus_per_level": 75
        },
        "unlock_requirements": {}
    },
    "workshop": {
        "key": "workshop",
        "name": "Workshop",
        "emoji": "🔧",
        "max_level": 20,
        "base_costs": {"wood": 65, "stone": 55, "food": 35, "gold": 30, "energy": 12},
        "base_time": 18, # minutes
        "cost_multiplier": 1.17,
        "time_multiplier": 1.23,
        "effects": {
            "upgrade_cost_reduction_per_level": 0.05,
            "power_bonus_per_level": 75
        },
        "unlock_requirements": {}
    },
    "jail": {
        "key": "jail",
        "name": "Jail",
        "emoji": "🔒",
        "max_level": 20,
        "base_costs": {"wood": 70, "stone": 80, "food": 40, "gold": 35, "energy": 15},
        "base_time": 20, # minutes
        "cost_multiplier": 1.19,
        "time_multiplier": 1.26,
        "effects": {
            "prisoner_capacity_per_level": 5,
            "escape_chance_reduction_per_level": 0.05,
            "power_bonus_per_level": 75
        },
        "unlock_requirements": {}
    }
}

__all__ = ["BUILDING_CONFIG", "_BUILDING_KEY_TO_FIELD", "_FIELD_TO_BUILDING_KEY"] 