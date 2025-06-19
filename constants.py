 # constants.py

# --- Google Sheet Configuration ---
# These are the exact headers for the 'Players' worksheet in your Google Sheet.
# The bot will create these automatically.
SHEET_COLUMN_HEADERS = [
    'user_id', 'commander_name', 'base_level', 'xp', 'power', 'diamonds',
    'wood', 'stone', 'iron', 'food', 'energy',
    'wood_storage_cap', 'stone_storage_cap', 'iron_storage_cap', 'food_storage_cap',
    'wood_prod_rate', 'stone_prod_rate', 'iron_prod_rate', 'food_prod_rate',
    'army_strategy_points', 'prod_strategy_points',
    'vip_tier', 'vip_expiry', 'created_at', 'last_seen'
]

# --- Player Data Fields (for consistency) ---
FIELD_USER_ID = 'user_id'
FIELD_COMMANDER_NAME = 'commander_name'
# ... you can add more fields here as we use them ...

# --- Initial Player Stats ---
INITIAL_PLAYER_STATS = {
    'base_level': 1,
    'xp': 0,
    'power': 50,
    'diamonds': 5,
    'wood': 500,
    'stone': 500,
    'iron': 250,
    'food': 1000,
    'energy': 100,
    'wood_storage_cap': 1000,
    'stone_storage_cap': 1000,
    'iron_storage_cap': 500,
    'food_storage_cap': 2000,
    'wood_prod_rate': 60,  # Per hour
    'stone_prod_rate': 60, # Per hour
    'iron_prod_rate': 30,  # Per hour
    'food_prod_rate': 100, # Per hour
    'army_strategy_points': 5,
    'prod_strategy_points': 5,
    'vip_tier': 'none',
    'vip_expiry': 'null'
}

# --- Main Menu Keyboard Buttons ---
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