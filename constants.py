# constants.py
# System 5 Upgrade: Includes Research Lab, Technology data, and new DB columns.

from datetime import datetime, timedelta, timezone

# --- Google Sheet Configuration ---
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
    'building_warehouse_level', 'building_barracks_level', 'building_research_lab_level', # <-- NEW
    # Unit Counts
    'unit_infantry_count',
    # Queues
    'train_queue_item_id', 'train_queue_quantity', 'train_queue_finish_time',
    'build_queue_item_id', 'build_queue_finish_time',
    'research_queue_item_id', 'research_queue_finish_time', # <-- NEW
    # --- NEW: Research Unlocks ---
    'research_logistics_unlocked', 'research_weaponry_unlocked',
    # Combat State
    'shield_finish_time',
    'attack_queue_target_id', 'attack_queue_finish_time',
    'return_queue_army_data', 'return_queue_finish_time',
    # Timestamps
    'created_at', 'last_seen'
]

# --- Player Data Fields ---
FIELD_USER_ID = 'user_id'
FIELD_COMMANDER_NAME = 'commander_name'

# --- Initial Player Stats ---
INITIAL_PLAYER_STATS = {
    'base_level': 1, 'xp': 0, 'power': 50, 'diamonds': 5,
    'wood': 500, 'stone': 500, 'iron': 250, 'food': 1000, 'energy': 100,
    'wood_storage_cap': 1000, 'stone_storage_cap': 1000, 'iron_storage_cap': 500, 'food_storage_cap': 2000,
    'wood_prod_rate': 60, 'stone_prod_rate': 60, 'iron_prod_rate': 30, 'food_prod_rate': 100,
    'army_strategy_points': 5, 'prod_strategy_points': 5,
    'vip_tier': 'none', 'vip_expiry': 'null',
    'building_hq_level': 1, 'building_sawmill_level': 1, 'building_quarry_level': 1,
    'building_ironmine_level': 1, 'building_warehouse_level': 1, 'building_barracks_level': 0,
    'building_research_lab_level': 0, # Starts at level 0
    'unit_infantry_count': 0,
    'train_queue_item_id': '', 'train_queue_quantity': '', 'train_queue_finish_time': '',
    'build_queue_item_id': '', 'build_queue_finish_time': '',
    'research_queue_item_id': '', 'research_queue_finish_time': '',
    'research_logistics_unlocked': 'FALSE', 'research_weaponry_unlocked': 'FALSE', # Use strings for sheet compatibility
    'shield_finish_time': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    'attack_queue_target_id': '', 'attack_queue_finish_time': '',
    'return_queue_army_data': '', 'return_queue_finish_time': ''
}

# --- Main Menu Keyboard Buttons (Unchanged) ---
MENU_BASE = "🏠 Base"
MENU_BUILD = "⚒️ Build"
MENU_TRAIN = "🪖 Train"
MENU_RESEARCH = "🔬 Research"
MENU_ATTACK = "⚔️ Attack"
MENU_QUESTS = "🎖 Quests"
MENU_SHOP = "🛒 Shop"
MENU_PREMIUM = "💎 Premium"
MENU_MAP = "🌍 Map"
MENU_ALLIANCE = "👥 Alliance"

# --- BUILDING DATA BLUEPRINT ---
# Upgraded with the new Research Lab.
BUILDING_DATA = {
    'hq': {'id': 'building_hq_level', 'name': 'Command HQ', 'emoji': '🏛️', 'description': 'The heart of your base. Upgrading unlocks new buildings and features.', 'base_cost': {'wood': 100, 'stone': 100}, 'cost_multiplier': 2.5, 'base_time_seconds': 60, 'time_multiplier': 2, 'effects': {}},
    'barracks': {'id': 'building_barracks_level', 'name': 'Barracks', 'emoji': '🪖', 'description': 'Allows training of military units.', 'base_cost': {'wood': 200, 'stone': 100}, 'cost_multiplier': 2.0, 'base_time_seconds': 90, 'time_multiplier': 1.8, 'effects': {}},
    'research_lab': { # <-- NEW BUILDING
        'id': 'building_research_lab_level', 'name': 'Research Lab', 'emoji': '🔬',
        'description': 'Unlocks new technologies to enhance your empire.',
        'base_cost': {'wood': 300, 'stone': 400}, 'cost_multiplier': 2.2,
        'base_time_seconds': 120, 'time_multiplier': 1.9, 'effects': {}
    },
    'warehouse': {'id': 'building_warehouse_level', 'name': 'Warehouse', 'emoji': '📦', 'description': 'Increases resource storage capacity.', 'base_cost': {'wood': 200, 'stone': 150}, 'cost_multiplier': 2.2, 'base_time_seconds': 45, 'time_multiplier': 1.8, 'effects': {'type': 'storage', 'value_per_level': 500}},
    'sawmill': {'id': 'building_sawmill_level', 'name': 'Sawmill', 'emoji': '🌲', 'description': 'Produces Wood over time.', 'base_cost': {'wood': 50, 'stone': 100}, 'cost_multiplier': 1.8, 'base_time_seconds': 30, 'time_multiplier': 1.6, 'effects': {'type': 'production', 'resource': 'wood_prod_rate', 'value_per_level': 20}},
    'quarry': {'id': 'building_quarry_level', 'name': 'Stone Quarry', 'emoji': '🪨', 'description': 'Produces Stone over time.', 'base_cost': {'wood': 100, 'stone': 50}, 'cost_multiplier': 1.8, 'base_time_seconds': 30, 'time_multiplier': 1.6, 'effects': {'type': 'production', 'resource': 'stone_prod_rate', 'value_per_level': 20}},
    'ironmine': {'id': 'building_ironmine_level', 'name': 'Iron Mine', 'emoji': '🔩', 'description': 'Produces Iron over time.', 'base_cost': {'wood': 150, 'stone': 150}, 'cost_multiplier': 2.0, 'base_time_seconds': 40, 'time_multiplier': 1.7, 'effects': {'type': 'production', 'resource': 'iron_prod_rate', 'value_per_level': 10}}
}

# --- UNIT DATA BLUEPRINT (Unchanged) ---
UNIT_DATA = {
    'infantry': {'id': 'unit_infantry_count', 'name': 'Infantry', 'emoji': '🪖', 'description': 'Basic frontline soldiers.', 'stats': {'attack': 5, 'defense': 3, 'health': 10, 'power': 1}, 'cost': {'food': 50, 'iron': 10}, 'train_time_seconds': 20, 'required_barracks_level': 1}
}

# --- COMBAT CONFIGURATION BLUEPRINT (Unchanged) ---
COMBAT_CONFIG = {
    'energy_cost_per_attack': 10, 'base_travel_time_seconds': 300,
    'loot_percentage': 0.25, 'winner_casualty_percentage': 0.10, 'loser_casualty_percentage': 0.50
}

# --- NEW: RESEARCH DATA BLUEPRINT ---
# The architectural core of our technology system.
RESEARCH_DATA = {
    'logistics': {
        'id': 'research_logistics_unlocked',
        'name': 'Advanced Logistics',
        'emoji': '📈',
        'description': 'Permanently increases all non-food resource production by 10%.',
        'cost': {'wood': 1000, 'stone': 1000, 'iron': 500},
        'research_time_seconds': 600, # 10 minutes
        'required_lab_level': 1,
        'effects': [
            {'type': 'production_multiplier', 'resource': 'wood_prod_rate', 'multiplier': 1.10},
            {'type': 'production_multiplier', 'resource': 'stone_prod_rate', 'multiplier': 1.10},
            {'type': 'production_multiplier', 'resource': 'iron_prod_rate', 'multiplier': 1.10},
        ]
    },
    'weaponry': {
        'id': 'research_weaponry_unlocked',
        'name': 'Improved Weaponry',
        'emoji': '⚔️',
        'description': 'Permanently increases the attack power of all Infantry units by 2 points.',
        'cost': {'iron': 1500},
        'research_time_seconds': 900, # 15 minutes
        'required_lab_level': 2,
        'effects': [
            {'type': 'unit_stat_bonus', 'unit': 'infantry', 'stat': 'attack', 'bonus': 2},
        ]
    }
}