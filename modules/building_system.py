import math # For ceil in cost/time calculation
from typing import Dict, Any, List, Optional, Tuple
from telegram import constants # Required for parse_mode in build_menu, build_choice
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # For build_menu, build_choice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes # For setup_building_system
from telegram.helpers import escape_markdown # For MarkdownV2 escaping
from datetime import datetime, timedelta

from modules.sheets_helper import client

__all__ = [
    "build_menu",
    "build_choice",
    "confirm_build",
    "cancel_build",
    "show_building_info",
    "start_upgrade_worker",
    "view_queue"
]

# Mapping from BUILDING_CONFIG keys to sheet field names
_BUILDING_KEY_TO_FIELD = {
    "town_hall": "base_level",
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
    "town_hall": {
        "key": "town_hall",
        "name": "Town Hall",
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
            "food_production_per_level": 10,
            "capacity_increase_per_level": {
                "wood": 1000,    # +1000 wood capacity per level
                "stone": 1000,   # +1000 stone capacity per level
                "food": 2000,    # +2000 food capacity per level (higher since it's the Farm)
                "gold": 500,     # +500 gold capacity per level (lower since gold is more valuable)
                "energy": 200    # +200 energy capacity per level
            },
            "power_bonus_per_level": 50
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
        "base_costs": {"wood": 90, "stone": 80, "food": 50, "gold": 35, "energy": 20},
        "base_time": 25, # minutes
        "cost_multiplier": 1.19,
        "time_multiplier": 1.26,
        "effects": {
            "vehicle_training_time_reduction_per_level": 0.05,
            "power_bonus_per_level": 75,
            "unlocks": {
                "destroyer": 8,
                "cruiser": 12,
                "battleship": 16,
                "carrier": 20
            }
        },
        "unlock_requirements": {}
    },
    "jail": {
        "key": "jail",
        "name": "Jail",
        "emoji": "🚔",
        "max_level": 20,
        "base_costs": {"wood": 70, "stone": 60, "food": 40, "gold": 30, "energy": 15},
        "base_time": 20, # minutes
        "cost_multiplier": 1.17,
        "time_multiplier": 1.23,
        "effects": {
            "capacity_increase_per_level": 5,
            "power_bonus_per_level": 75
        },
        "unlock_requirements": {}
    }
}

# Helper functions
def get_building_config(key: str) -> Optional[Dict[str, Any]]:
    """Retrieves the configuration for a specific building."""
    return BUILDING_CONFIG.get(key)

def calculate_upgrade_cost(player_data: Dict[str, Any], building_key: str) -> Dict[str, int]:
    """
    Calculates the upgrade cost for the next level of a building.
    Cost: base_costs * (cost_multiplier ** current_level)
    """
    config = get_building_config(building_key)
    if not config:
        return {}

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        return {}

    current_level = player_data.get(field_name, 1)
    if current_level >= config["max_level"]:
        return {}

    costs = {}
    for resource, base_cost in config["base_costs"].items():
        costs[resource] = math.ceil(base_cost * (config["cost_multiplier"] ** current_level))
    return costs

def calculate_upgrade_time(player_data: Dict[str, Any], building_key: str) -> int:
    """
    Calculates the upgrade time for the next level of a building.
    Time: base_time * (time_multiplier ** current_level)
    """
    config = get_building_config(building_key)
    if not config:
        return 0

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        return 0

    current_level = player_data.get(field_name, 1)
    if current_level >= config["max_level"]:
        return 0

    # Apply Town Hall upgrade time reduction
    town_hall_level = player_data.get("base_level", 1)
    time_reduction = 1 - (0.05 * town_hall_level)  # 5% reduction per level

    base_time = config["base_time"]
    time_multiplier = config["time_multiplier"]
    return math.ceil(base_time * (time_multiplier ** current_level) * time_reduction)

def apply_building_effects(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies all building effects to the player's data.
    Returns a dictionary of calculated effects.
    """
    effects = {
        "wood_production_per_hour": 0,
        "stone_production_per_hour": 0,
        "food_production_per_hour": 0,
        "gold_production_per_hour": 0,
        "energy_production_per_hour": 0,
        "wood_capacity": 1000,
        "stone_capacity": 1000,
        "food_capacity": 2000,
        "gold_capacity": 1000,
        "energy_capacity": 200,
        "power": 0
    }

    # Apply effects from each building
    for building_key, config in BUILDING_CONFIG.items():
        field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
        if not field_name:
            continue

        level = player_data.get(field_name, 1)
        if level < 1:
            continue

        # Apply production effects
        if "wood_production_per_level" in config["effects"]:
            effects["wood_production_per_hour"] += config["effects"]["wood_production_per_level"] * level
        if "stone_production_per_level" in config["effects"]:
            effects["stone_production_per_hour"] += config["effects"]["stone_production_per_level"] * level
        if "food_production_per_level" in config["effects"]:
            effects["food_production_per_hour"] += config["effects"]["food_production_per_level"] * level
        if "gold_production_per_level" in config["effects"]:
            effects["gold_production_per_hour"] += config["effects"]["gold_production_per_level"] * level
        if "energy_production_per_level" in config["effects"]:
            effects["energy_production_per_hour"] += config["effects"]["energy_production_per_level"] * level

        # Apply capacity effects
        if "capacity_increase_per_level" in config["effects"]:
            for resource, increase in config["effects"]["capacity_increase_per_level"].items():
                capacity_key = f"{resource}_capacity"
                if capacity_key in effects:
                    effects[capacity_key] += increase * level

        # Apply power bonus
        if "power_bonus_per_level" in config["effects"]:
            effects["power"] += config["effects"]["power_bonus_per_level"] * level

    return effects

async def build_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the building menu with available buildings and their levels."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.message.reply_text(
            "❌ You aren't registered yet\. Send /start to begin\.",
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return

    # Get current building levels
    buildings = {}
    for building_key, field_name in _BUILDING_KEY_TO_FIELD.items():
        buildings[building_key] = player_data.get(field_name, 1)

    # Build the message
    msg = "*🏗️ Building Menu*\n\n"
    msg += "*Current Buildings:*\n"

    # Group buildings by type
    resource_buildings = ["lumber_house", "mine", "farm", "gold_mine", "power_plant"]
    military_buildings = ["barracks", "workshop"]
    support_buildings = ["town_hall", "research_lab", "hospital", "jail"]

    # Add resource buildings
    msg += "\n*Resource Buildings:*\n"
    for key in resource_buildings:
        config = BUILDING_CONFIG[key]
        level = buildings[key]
        msg += f"{config['emoji']} {config['name']}: Level {level}\n"

    # Add military buildings
    msg += "\n*Military Buildings:*\n"
    for key in military_buildings:
        config = BUILDING_CONFIG[key]
        level = buildings[key]
        msg += f"{config['emoji']} {config['name']}: Level {level}\n"

    # Add support buildings
    msg += "\n*Support Buildings:*\n"
    for key in support_buildings:
        config = BUILDING_CONFIG[key]
        level = buildings[key]
        msg += f"{config['emoji']} {config['name']}: Level {level}\n"

    # Create keyboard
    keyboard = []
    for key in resource_buildings + military_buildings + support_buildings:
        config = BUILDING_CONFIG[key]
        level = buildings[key]
        if level < config["max_level"]:
            keyboard.append([InlineKeyboardButton(
                f"{config['emoji']} {config['name']} (Level {level})",
                callback_data=f"BUILD_{key}"
            )])

    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")])

    # Send or edit message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )

async def build_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the selection of a building to upgrade."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.callback_query.answer("You aren't registered yet. Send /start to begin.")
        return

    # Extract building key from callback data
    building_key = update.callback_query.data.split("_")[1]
    config = get_building_config(building_key)
    if not config:
        await update.callback_query.answer("Invalid building selection.")
        return

    # Get current level
    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await update.callback_query.answer("Invalid building configuration.")
        return

    current_level = player_data.get(field_name, 1)
    if current_level >= config["max_level"]:
        await update.callback_query.answer("This building is already at maximum level!")
        return

    # Calculate upgrade cost and time
    cost = calculate_upgrade_cost(player_data, building_key)
    time = calculate_upgrade_time(player_data, building_key)

    # Build the message
    msg = f"*{config['emoji']} {config['name']} Upgrade*\n\n"
    msg += f"Current Level: {current_level}\n"
    msg += f"Next Level: {current_level + 1}\n\n"
    msg += "*Upgrade Cost:*\n"
    for resource, amount in cost.items():
        msg += f"{resource.title()}: {amount}\n"
    msg += f"\nUpgrade Time: {time} minutes"

    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM_{building_key}"),
            InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_BUILD")
        ]
    ]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def confirm_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the confirmation of a building upgrade."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.callback_query.answer("You aren't registered yet. Send /start to begin.")
        return

    # Extract building key from callback data
    building_key = update.callback_query.data.split("_")[1]
    config = get_building_config(building_key)
    if not config:
        await update.callback_query.answer("Invalid building selection.")
        return

    # Get current level
    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await update.callback_query.answer("Invalid building configuration.")
        return

    current_level = player_data.get(field_name, 1)
    if current_level >= config["max_level"]:
        await update.callback_query.answer("This building is already at maximum level!")
        return

    # Calculate upgrade cost and time
    cost = calculate_upgrade_cost(player_data, building_key)
    time = calculate_upgrade_time(player_data, building_key)

    # Check if player can afford the upgrade
    if not can_afford(user_id, cost):
        await update.callback_query.answer("You don't have enough resources!")
        return

    # Deduct resources
    if not deduct_resources(user_id, cost):
        await update.callback_query.answer("Failed to deduct resources. Please try again.")
        return

    # Add upgrade to pending upgrades
    upgrade_info = {
        "user_id": user_id,
        "building_key": building_key,
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(minutes=time)).isoformat(),
        "cost": cost
    }

    # Update player data with pending upgrade
    player_data["pending_upgrade"] = upgrade_info
    if not client.update_player_data(user_id, player_data):
        await update.callback_query.answer("Failed to start upgrade. Please try again.")
        return

    # Send confirmation message
    msg = f"✅ *{config['emoji']} {config['name']} upgrade started!*\n\n"
    msg += f"Current Level: {current_level}\n"
    msg += f"Next Level: {current_level + 1}\n"
    msg += f"Time Remaining: {time} minutes"

    keyboard = [[InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def cancel_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the cancellation of a building upgrade."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.callback_query.answer("You aren't registered yet. Send /start to begin.")
        return

    # Remove pending upgrade
    if "pending_upgrade" in player_data:
        del player_data["pending_upgrade"]
        client.update_player_data(user_id, player_data)

    # Return to build menu
    await build_menu(update, context)

def get_player_buildings(user_id: int) -> Dict[str, int]:
    """Gets the current building levels for a player."""
    player_data = client.get_player_data(user_id)
    if not player_data:
        return {}

    buildings = {}
    for building_key, field_name in _BUILDING_KEY_TO_FIELD.items():
        buildings[building_key] = player_data.get(field_name, 1)
    return buildings

def calculate_upgrade(building_key: str, current_level: int) -> Dict[str, Any]:
    """Calculates the upgrade information for a building."""
    config = get_building_config(building_key)
    if not config:
        return {}

    if current_level >= config["max_level"]:
        return {}

    return {
        "cost": config["base_costs"],
        "time": config["base_time"],
        "effects": config["effects"]
    }

def can_afford(user_id: int, cost: Dict[str, int]) -> bool:
    """Checks if a player can afford a cost."""
    player_data = client.get_player_data(user_id)
    if not player_data:
        return False

    resources = player_data.get("resources", {})
    for resource, amount in cost.items():
        if resources.get(resource, 0) < amount:
            return False
    return True

def deduct_resources(user_id: int, cost: Dict[str, int]) -> bool:
    """Deducts resources from a player."""
    player_data = client.get_player_data(user_id)
    if not player_data:
        return False

    resources = player_data.get("resources", {})
    for resource, amount in cost.items():
        if resources.get(resource, 0) < amount:
            return False
        resources[resource] -= amount

    player_data["resources"] = resources
    return client.update_player_data(user_id, player_data)

async def start_upgrade_worker(context: ContextTypes.DEFAULT_TYPE):
    """Starts the upgrade worker job."""
    context.job_queue.run_repeating(_process_upgrades, interval=60, first=0)

async def _process_upgrades(context: ContextTypes.DEFAULT_TYPE):
    """Processes pending upgrades."""
    all_players = client.list_all_players()
    now = datetime.now()

    for player in all_players:
        user_id = player.get("user_id")
        if not user_id:
            continue

        pending_upgrade = player.get("pending_upgrade")
        if not pending_upgrade:
            continue

        end_time = datetime.fromisoformat(pending_upgrade["end_time"])
        if now >= end_time:
            # Complete the upgrade
            building_key = pending_upgrade["building_key"]
            field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
            if not field_name:
                continue

            # Update building level
            player[field_name] = player.get(field_name, 1) + 1
            del player["pending_upgrade"]

            # Update player data
            client.update_player_data(user_id, player)

def get_upgrade_info(user_id: int, building_key: str) -> Optional[Dict[str, Any]]:
    """Gets the upgrade information for a building."""
    player_data = client.get_player_data(user_id)
    if not player_data:
        return None

    config = get_building_config(building_key)
    if not config:
        return None

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        return None

    current_level = player_data.get(field_name, 1)
    if current_level >= config["max_level"]:
        return None

    return {
        "current_level": current_level,
        "next_level": current_level + 1,
        "cost": calculate_upgrade_cost(player_data, building_key),
        "time": calculate_upgrade_time(player_data, building_key),
        "effects": config["effects"]
    }

def get_ongoing_upgrade(user_id: int) -> Optional[Dict[str, Any]]:
    """Gets the ongoing upgrade for a player."""
    player_data = client.get_player_data(user_id)
    if not player_data:
        return None

    return player_data.get("pending_upgrade")

async def show_building_info(update: Update, context: ContextTypes.DEFAULT_TYPE, building_key: str) -> None:
    """Shows detailed information about a building."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.callback_query.answer("You aren't registered yet. Send /start to begin.")
        return

    config = get_building_config(building_key)
    if not config:
        await update.callback_query.answer("Invalid building selection.")
        return

    # Get current level
    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await update.callback_query.answer("Invalid building configuration.")
        return

    current_level = player_data.get(field_name, 1)

    # Build the message
    msg = f"*{config['emoji']} {config['name']} Information*\n\n"
    msg += f"Current Level: {current_level}\n"
    msg += f"Maximum Level: {config['max_level']}\n\n"

    # Add effects information
    msg += "*Effects:*\n"
    for effect, value in config["effects"].items():
        if isinstance(value, dict):
            msg += f"\n{effect.title()}:\n"
            for sub_effect, sub_value in value.items():
                msg += f"- {sub_effect}: {sub_value}\n"
        else:
            msg += f"- {effect}: {value}\n"

    # Add upgrade information if not at max level
    if current_level < config["max_level"]:
        cost = calculate_upgrade_cost(player_data, building_key)
        time = calculate_upgrade_time(player_data, building_key)

        msg += "\n*Next Level Upgrade:*\n"
        msg += "Cost:\n"
        for resource, amount in cost.items():
            msg += f"- {resource.title()}: {amount}\n"
        msg += f"Time: {time} minutes"

    # Create keyboard
    keyboard = [[InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def view_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the current upgrade queue."""
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    player_data = client.get_player_data(user_id)
    if not player_data:
        await update.callback_query.answer("You aren't registered yet. Send /start to begin.")
        return

    pending_upgrade = player_data.get("pending_upgrade")
    if not pending_upgrade:
        await update.callback_query.answer("No upgrades in progress.")
        return

    # Get building config
    building_key = pending_upgrade["building_key"]
    config = get_building_config(building_key)
    if not config:
        await update.callback_query.answer("Invalid upgrade information.")
        return

    # Calculate time remaining
    end_time = datetime.fromisoformat(pending_upgrade["end_time"])
    now = datetime.now()
    time_remaining = end_time - now
    minutes_remaining = int(time_remaining.total_seconds() / 60)

    # Build the message
    msg = "*🏗️ Current Upgrade*\n\n"
    msg += f"Building: {config['emoji']} {config['name']}\n"
    msg += f"Time Remaining: {minutes_remaining} minutes"

    # Create keyboard
    keyboard = [[InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    ) 