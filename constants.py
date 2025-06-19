# constants.py

# --- Google Sheet Configuration ---
# The database schema is now expanded to include building levels.
SHEET_COLUMN_HEADERS = [
    # Player Info
    'user_id', 'commander_name', 'base_level', 'xp', 'power', 'diamonds',
    # Resources
    'wood', 'stone', 'iron', 'food', 'energy',
    'wood_storage_cap', 'stone_storage_cap', 'iron_storage_cap', 'food_storage_cap',
    'wood_prod_rate', 'stone_prod_rate', 'iron_prod_rate', 'food_prod_rate',
    # Strategy & VIP
    'army_strategy_points', 'prod_strategy_points',
    'vip_tier', 'vip_expiry',
    # Building Levels
    'building_hq_level', 'building_sawmill_level', 'building_quarry_level', 'building_ironmine_level',
    'building_warehouse_level',
    # --- NEW: Build Queue ---
    'build_queue_item_id', 'build_queue_finish_time',
    # Timestamps
    'created_at', 'last_seen'
]

# --- Player Data Fields (for consistency) ---
FIELD_USER_ID = 'user_id'
FIELD_COMMANDER_NAME = 'commander_name'

# --- Initial Player Stats ---
# Now includes starting building levels.
INITIAL_PLAYER_STATS = {
    'base_level': 1, 'xp': 0, 'power': 50, 'diamonds': 5,
    'wood': 500, 'stone': 500, 'iron': 250, 'food': 1000, 'energy': 100,
    'wood_storage_cap': 1000, 'stone_storage_cap': 1000, 'iron_storage_cap': 500, 'food_storage_cap': 2000,
    'wood_prod_rate': 60, 'stone_prod_rate': 60, 'iron_prod_rate': 30, 'food_prod_rate': 100,
    'army_strategy_points': 5, 'prod_strategy_points': 5,
    'vip_tier': 'none', 'vip_expiry': 'null',
    # Every player starts with Level 1 of the essentials.
    'building_hq_level': 1, 'building_sawmill_level': 1, 'building_quarry_level': 1,
    'building_ironmine_level': 1, 'building_warehouse_level': 1
}

# --- Main Menu Keyboard Buttons ---
MENU_BASE = "🏠 Base"
MENU_BUILD = "⚒️ Build"
MENU_TRAIN = "🪖 Train"
# ... (the rest of the menu constants remain the same)
MENU_RESEARCH = "🔬 Research"
MENU_ATTACK = "⚔️ Attack"
MENU_QUESTS = "🎖 Quests"
MENU_SHOP = "🛒 Shop"
MENU_PREMIUM = "💎 Premium"
MENU_MAP = "🌍 Map"
MENU_ALLIANCE = "👥 Alliance"


# --- BUILDING DATA BLUEPRINT ---
# This is the architectural core of our construction system.
# Each building is defined as a dictionary, containing all its properties.
# This makes our game logic clean, scalable, and easy to balance.
BUILDING_DATA = {
    'hq': {
        'id': 'building_hq_level',
        'name': 'Command HQ',
        'emoji': '🏛️',
        'description': 'The heart of your base. Upgrading unlocks new buildings and features.',
        'base_cost': {'wood': 100, 'stone': 100},
        'cost_multiplier': 2.5,
        'base_time_seconds': 60,
        'time_multiplier': 2,
        'effects': {
            # HQ doesn't give direct production, but its level is a prerequisite for others.
        }
    },
    'warehouse': {
        'id': 'building_warehouse_level',
        'name': 'Warehouse',
        'emoji': '📦',
        'description': 'Increases the storage capacity for all your resources.',
        'base_cost': {'wood': 200, 'stone': 150},
        'cost_multiplier': 2.2,
        'base_time_seconds': 45,
        'time_multiplier': 1.8,
        'effects': {
            'type': 'storage',
            'value_per_level': 500 # Adds 500 to wood, stone, iron, and food caps per level.
        }
    },
    'sawmill': {
        'id': 'building_sawmill_level',
        'name': 'Sawmill',
        'emoji': '🌲',
        'description': 'Automatically produces Wood over time.',
        'base_cost': {'wood': 50, 'stone': 100},
        'cost_multiplier': 1.8,
        'base_time_seconds': 30,
        'time_multiplier': 1.6,
        'effects': {
            'type': 'production',
            'resource': 'wood_prod_rate',
            'value_per_level': 20 # Adds 20 to wood production rate per level.
        }
    },
    'quarry': {
        'id': 'building_quarry_level',
        'name': 'Stone Quarry',
        'emoji': '🪨',
        'description': 'Automatically produces Stone over time.',
        'base_cost': {'wood': 100, 'stone': 50},
        'cost_multiplier': 1.8,
        'base_time_seconds': 30,
        'time_multiplier': 1.6,
        'effects': {
            'type': 'production',
            'resource': 'stone_prod_rate',
            'value_per_level': 20 # Adds 20 to stone production rate per level.
        }
    },
    'ironmine': {
        'id': 'building_ironmine_level',
        'name': 'Iron Mine',
        'emoji': '🔩',
        'description': 'Automatically produces Iron over time.',
        'base_cost': {'wood': 150, 'stone': 150},
        'cost_multiplier': 2.0,
        'base_time_seconds': 40,
        'time_multiplier': 1.7,
        'effects': {
            'type': 'production',
            'resource': 'iron_prod_rate',
            'value_per_level': 10 # Adds 10 to iron production rate per level.
        }
    }
}