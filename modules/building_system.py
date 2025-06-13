import math # For ceil in cost/time calculation
from typing import Dict, Any, List, Optional
from telegram import constants # Required for parse_mode in build_menu, build_choice
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # For build_menu, build_choice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes # For setup_building_system
from telegram.helpers import escape_markdown # For MarkdownV2 escaping
from datetime import datetime, timedelta

from modules.sheets_helper import get_player_data, update_player_data

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

    current_level = int(player_data.get(field_name, 1))

    costs = {}
    for resource, base_cost in config["base_costs"].items():
        calculated_cost = base_cost * (config["cost_multiplier"] ** (current_level))
        costs[resource] = math.ceil(calculated_cost)
    return costs

def calculate_upgrade_time(player_data: Dict[str, Any], building_key: str) -> int:
    """
    Calculates the upgrade time for the next level of a building.
    Time: base_time * (time_multiplier ** current_level)
    Then applies Town Hall reduction.
    """
    config = get_building_config(building_key)
    if not config:
        return 0

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        return 0

    current_level = int(player_data.get(field_name, 1))
    town_hall_level = int(player_data.get(_BUILDING_KEY_TO_FIELD["town_hall"], 1))

    base_time = config["base_time"]
    calculated_time = base_time * (config["time_multiplier"] ** (current_level))
    
    # Apply Town Hall upgrade time reduction
    th_config = get_building_config("town_hall")
    if th_config and "upgrade_time_reduction_per_level" in th_config["effects"]:
        reduction_per_level = th_config["effects"]["upgrade_time_reduction_per_level"]
        total_reduction = town_hall_level * reduction_per_level
        # Cap reduction at a reasonable max, e.g., 90% to avoid negative/zero times
        total_reduction = min(total_reduction, 0.90)
        calculated_time *= (1 - total_reduction)

    return math.ceil(calculated_time)

def apply_building_effects(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the cumulative effects of all buildings based on their current levels.
    This function returns the calculated effects. Other modules need to be updated
    to utilize these calculated effects (e.g., for resource production rates,
    training time reductions, etc.).
    """
    calculated_effects: Dict[str, Any] = {
        "wood_production_per_hour": 0,
        "stone_production_per_hour": 0,
        "food_production_per_hour": 0,
        "gold_production_per_hour": 0,
        "energy_production_per_hour": 0,
        "total_upgrade_time_reduction": 0,
        "infantry_training_time_reduction": 0,
        "vehicle_training_time_reduction": 0,
        "research_time_reduction": 0,
        "healing_time_reduction": 0,
        "hospital_capacity_increase": 0,
        "unlocked_units": [],
        "unlocked_tech_tiers": [],
        "unlocked_build_slots": 0,
    }

    for building_key, config in BUILDING_CONFIG.items():
        field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
        if not field_name:
            continue
        current_level = int(player_data.get(field_name, 1))

        # Apply production effects
        if "wood_production_per_level" in config["effects"]:
            calculated_effects["wood_production_per_hour"] += config["effects"]["wood_production_per_level"] * current_level
        if "stone_production_per_level" in config["effects"]:
            calculated_effects["stone_production_per_hour"] += config["effects"]["stone_production_per_level"] * current_level
        if "food_production_per_level" in config["effects"]:
            calculated_effects["food_production_per_hour"] += config["effects"]["food_production_per_level"] * current_level
        if "gold_production_per_level" in config["effects"]:
            calculated_effects["gold_production_per_hour"] += config["effects"]["gold_production_per_level"] * current_level
        if "energy_production_per_level" in config["effects"]:
            calculated_effects["energy_production_per_hour"] += config["effects"]["energy_production_per_level"] * current_level

        # Apply time reduction effects
        if "upgrade_time_reduction_per_level" in config["effects"] and building_key == "town_hall":
            # Town Hall affects all upgrade times
            calculated_effects["total_upgrade_time_reduction"] = min(current_level * config["effects"]["upgrade_time_reduction_per_level"], 0.90) # Cap at 90%
        if "infantry_training_time_reduction_per_level" in config["effects"] and building_key == "barracks":
            calculated_effects["infantry_training_time_reduction"] = min(current_level * config["effects"]["infantry_training_time_reduction_per_level"], 0.90)
        if "vehicle_training_time_reduction_per_level" in config["effects"] and building_key == "workshop":
            calculated_effects["vehicle_training_time_reduction"] = min(current_level * config["effects"]["vehicle_training_time_reduction_per_level"], 0.90)
        if "research_time_reduction_per_level" in config["effects"] and building_key == "research_lab":
            calculated_effects["research_time_reduction"] = min(current_level * config["effects"]["research_time_reduction_per_level"], 0.90)
        if "healing_time_reduction_per_level" in config["effects"] and building_key == "hospital":
            calculated_effects["healing_time_reduction"] = min(current_level * config["effects"]["healing_time_reduction_per_level"], 0.90)

        # Apply capacity increase
        if "capacity_increase_per_level" in config["effects"] and building_key == "hospital":
            calculated_effects["hospital_capacity_increase"] += current_level * config["effects"]["capacity_increase_per_level"]

        # Apply unlocks
        if "unlocks" in config["effects"]:
            for unlock_type, unlock_level in config["effects"]["unlocks"].items():
                if current_level >= unlock_level:
                    if unlock_type == "artillery" or unlock_type == "tank" or unlock_type == "destroyer":
                        calculated_effects["unlocked_units"].append(unlock_type)
                    elif unlock_type == "tech_tiers":
                        # Placeholder for tech tiers, add specific tiers if document provided
                        calculated_effects["unlocked_tech_tiers"].append(f"Tier {unlock_level}") # Assuming unlock_level refers to tiers
        
        # Build slots unlock for Town Hall
        if building_key == "town_hall" and "build_slots_unlock_levels" in config["effects"]:
            for slot_level in config["effects"]["build_slots_unlock_levels"]:
                if current_level >= slot_level:
                    calculated_effects["unlocked_build_slots"] += 1
    
    return calculated_effects


async def build_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the building menu with current levels and upgrade options."""
    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        if update.message:
            await update.message.reply_text("❌ You aren't registered yet\. Send /start to begin\.")
        elif update.callback_query:
            await update.callback_query.answer("❌ You aren't registered yet\. Send /start to begin\.")
        return

    # Check for ongoing upgrades
    ongoing = get_ongoing_upgrade(user.id)
    if ongoing:
        msg = (
            f"⏳ You already have an upgrade in progress:\n"
            f"{ongoing['emoji']} {ongoing['building']} to Level {ongoing['next_level']}\n"
            f"⏱️ {ongoing['remaining']} remaining"
        )
        keyboard = [[InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]]
        
        if update.message:
            await update.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        return

    # Get current building levels
    buildings = get_player_buildings(user.id)
    
    # Build message lines and keyboard buttons
    msg_lines = ["🏗 *Building Menu*"]
    keyboard_buttons = []
    
    for building_key, config in BUILDING_CONFIG.items():
        current_level = buildings.get(building_key, 1)
        max_level = config["max_level"]
        
        # Add building info line
        msg_lines.append(f"\n{config['emoji']} *{escape_markdown(config['name'])}* — Level {current_level}/{max_level}")
        
        if current_level < max_level:
            # Calculate upgrade info
            upgrade_info = get_upgrade_info(building_key, current_level)
            if upgrade_info:
                # Format costs
                cost_display = []
                for resource, amount in upgrade_info["cost"].items():
                    emoji_map = {"wood": "🪵", "stone": "🪨", "food": "🥖", "gold": "💰", "energy": "⚡"}
                    cost_display.append(f"{emoji_map.get(resource, '')} {amount}")
                cost_str = " / ".join(cost_display)
                
                # Add upgrade info
                minutes = upgrade_info["duration"] // 60
                msg_lines.append(f"➡️ Upgrade cost: {cost_str}, time: {minutes}m")
                
                # Add buttons
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"⚒️ Upgrade {config['name']}", 
                        callback_data=f"BUILD_{building_key}"
                    ),
                    InlineKeyboardButton(
                        "📊 Info", 
                        callback_data=f"INFO_{building_key}"
                    )
                ])
        else:
            # Building is at max level
            keyboard_buttons.append([
                InlineKeyboardButton(
                    f"✅ {escape_markdown(config['name'])} \\(Max Level\\)", 
                    callback_data=f"INFO_{building_key}"
                )
            ])

    # Add back button
    msg_lines.append("\n🏠 Back to Base")
    keyboard_buttons.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")])

    # Build message and keyboard
    msg = "\n".join(msg_lines)
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    # Send or edit message
    if update.message:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def build_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the building upgrade choice and shows upgrade details."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ You aren't registered yet\. Send /start to begin\.")
        return

    # Extract building key from callback data
    building_key = query.data.replace("BUILD_", "")
    config = get_building_config(building_key)
    if not config:
        await query.edit_message_text("❌ Invalid building selected\.")
        return

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await query.edit_message_text("❌ Building mapping not found\.")
        return

    current_level = int(data.get(field_name, 1))
    upgrade_info = calculate_upgrade(building_key, current_level)
    
    if not upgrade_info:
        await query.edit_message_text(f"✅ {escape_markdown(config['name'])} is already at max level \\({escape_markdown(str(config['max_level']))}\\)\.")
        return

    # Format costs with emojis
    cost_display = []
    for resource, amount in upgrade_info["cost"].items():
        emoji_map = {"wood": "🪵", "stone": "🪨", "food": "🥖", "gold": "💰", "energy": "⚡"}
        cost_display.append(f"{emoji_map.get(resource, '')} {escape_markdown(str(amount))}")
    cost_str = " / ".join(cost_display)

    # Format duration
    minutes = upgrade_info["duration"] // 60
    hours = minutes // 60
    minutes = minutes % 60
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Build the message
    msg_lines = [
        f"{config['emoji']} *{escape_markdown(config['name'])}: Level {current_level} → {upgrade_info['next_level']}*",
        "\-\-\-",
        f"💰 Cost: {cost_str}",
        f"⏱️ Time: {duration_str}",
        "\-\-\-",
        "*Next Level Effects:*"
    ]

    # Add effects based on building type
    effects_lines = []
    if building_key == "town_hall":
        reduction = (upgrade_info["next_level"] * config["effects"]["upgrade_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces all upgrade times by {escape_markdown(f'{reduction:.0f}%')}")
        if upgrade_info["next_level"] in config["effects"]["build_slots_unlock_levels"]:
            effects_lines.append("Unlocks new build slot")
    elif "wood_production_per_level" in config["effects"]:
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['wood_production_per_level']))} Wood/hr")
    elif "stone_production_per_level" in config["effects"]:
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['stone_production_per_level']))} Stone/hr")
    elif "food_production_per_level" in config["effects"]:
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['food_production_per_level']))} Food/hr")
    elif "gold_production_per_level" in config["effects"]:
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['gold_production_per_level']))} Gold/hr")
    elif "energy_production_per_level" in config["effects"]:
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['energy_production_per_level']))} Energy/hr")
    elif building_key == "barracks":
        reduction = (upgrade_info["next_level"] * config["effects"]["infantry_training_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces infantry training time by {escape_markdown(f'{reduction:.0f}%')}")
        for unit, level in config["effects"]["unlocks"].items():
            if upgrade_info["next_level"] == level:
                effects_lines.append(f"Unlocks {escape_markdown(unit)}")
    elif building_key == "research_lab":
        reduction = (upgrade_info["next_level"] * config["effects"]["research_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces research time by {escape_markdown(f'{reduction:.0f}%')}")
        if "tech_tiers" in config["effects"]["unlocks"] and upgrade_info["next_level"] in config["effects"]["unlocks"]["tech_tiers"]:
            effects_lines.append(f"Unlocks Tech Tier {escape_markdown(str(upgrade_info['next_level']))}")
    elif building_key == "hospital":
        reduction = (upgrade_info["next_level"] * config["effects"]["healing_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces healing time by {escape_markdown(f'{reduction:.0f}%')}")
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['capacity_increase_per_level']))} Hospital capacity")
    elif building_key == "workshop":
        reduction = (upgrade_info["next_level"] * config["effects"]["vehicle_training_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces vehicle training time by {escape_markdown(f'{reduction:.0f}%')}")
        for unit, level in config["effects"]["unlocks"].items():
            if upgrade_info["next_level"] == level:
                effects_lines.append(f"Unlocks {escape_markdown(unit)}")

    if effects_lines:
        msg_lines.extend([f"• {line}" for line in effects_lines])
    else:
        msg_lines.append("No specific effects for next level\.")

    # Build keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM_{building_key}"),
            InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_BUILD"),
        ],
    ]

    await query.edit_message_text(
        "\n".join(msg_lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def confirm_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the confirmation of a building upgrade."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ You aren't registered yet\. Send /start to begin\.")
        return

    # Extract building key and recalculate costs/time
    building_key = query.data.replace("CONFIRM_", "")
    config = get_building_config(building_key)
    if not config:
        await query.edit_message_text("❌ Invalid building selected\.")
        return

    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await query.edit_message_text("❌ Building mapping not found\.")
        return

    current_level = int(data.get(field_name, 1))
    upgrade_info = get_upgrade_info(building_key, current_level)
    
    if not upgrade_info:
        await query.edit_message_text(f"✅ {escape_markdown(config['name'])} is already at max level \\({escape_markdown(str(config['max_level']))}\\)\.")
        return

    # Check if player has enough resources
    if not can_afford(user.id, upgrade_info["cost"]):
        await query.edit_message_text("❌ Not enough resources\.")
        return

    # Deduct resources and set timer
    deduct_resources(user.id, upgrade_info["cost"])
    end_time = datetime.utcnow() + timedelta(seconds=upgrade_info["duration"])
    timer_field = f"timers_{building_key}_level"
    update_player_data(user.id, timer_field, end_time.isoformat() + "Z")

    # Format duration for display
    hours = upgrade_info["duration"] // 3600
    minutes = (upgrade_info["duration"] % 3600) // 60
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Format end time for display
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M UTC")

    # Confirm message
    msg = "\n".join([
        "⏳ *Upgrade started\!*",
        f"🚧 Level {upgrade_info['next_level']} in progress…",
        f"🕒 Completion: {end_time_str}",
        "\n🏠 Back to Base"
    ])

    keyboard = [
        [
            InlineKeyboardButton("🏗 View Build Queue", callback_data="BUILD_MENU"),
            InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")
        ]
    ]
    
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def cancel_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Build cancelled\.", parse_mode=constants.ParseMode.MARKDOWN_V2) # Escape .

def get_player_buildings(user_id: int) -> Dict[str, int]:
    """Fetches all current building levels for a player."""
    data = get_player_data(user_id)
    if not data:
        return {}
    
    buildings = {}
    for building_key, field_name in _BUILDING_KEY_TO_FIELD.items():
        level = int(data.get(field_name, 1))
        buildings[building_key] = level
    return buildings

def calculate_upgrade(building_key: str, current_level: int) -> Dict[str, Any]:
    """Calculates upgrade details for a building."""
    config = get_building_config(building_key)
    if not config:
        return None
    
    if current_level >= config["max_level"]:
        return None
    
    next_level = current_level + 1
    costs = {}
    for resource, base_cost in config["base_costs"].items():
        costs[resource] = math.ceil(base_cost * (config["cost_multiplier"] ** current_level))
    
    duration = math.ceil(config["base_time"] * (config["time_multiplier"] ** current_level))
    
    return {
        "cost": costs,
        "duration": duration * 60,  # Convert to seconds
        "next_level": next_level
    }

def can_afford(user_id: int, cost: Dict[str, int]) -> bool:
    """Checks if a player can afford the upgrade cost."""
    data = get_player_data(user_id)
    if not data:
        return False
    
    for resource, amount in cost.items():
        current = int(data.get(f"resources_{resource}", 0))
        if current < amount:
            return False
    return True

def deduct_resources(user_id: int, cost: Dict[str, int]) -> None:
    """Deducts resources from a player's inventory."""
    data = get_player_data(user_id)
    if not data:
        return
    
    for resource, amount in cost.items():
        current = int(data.get(f"resources_{resource}", 0))
        update_player_data(user_id, f"resources_{resource}", current - amount)

async def start_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, building_key: str) -> None:
    """Starts a building upgrade."""
    user = update.effective_user
    if not user:
        return
    
    data = get_player_data(user.id)
    if not data:
        await update.callback_query.answer("❌ You aren't registered yet. Send /start to begin.")
        return
    
    field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
    if not field_name:
        await update.callback_query.answer("❌ Invalid building selected.")
        return
    
    current_level = int(data.get(field_name, 1))
    upgrade_info = calculate_upgrade(building_key, current_level)
    
    if not upgrade_info:
        await update.callback_query.answer("🏗 Already at max level!")
        return
    
    if not can_afford(user.id, upgrade_info["cost"]):
        await update.callback_query.answer("❌ Not enough resources!")
        return
    
    # Deduct resources and set timer
    deduct_resources(user.id, upgrade_info["cost"])
    end_time = datetime.utcnow() + timedelta(seconds=upgrade_info["duration"])
    timer_field = f"timers_{building_key}_level"
    update_player_data(user.id, timer_field, end_time.isoformat() + "Z")
    
    # Format duration for display
    hours = upgrade_info["duration"] // 3600
    minutes = (upgrade_info["duration"] % 3600) // 60
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    config = get_building_config(building_key)
    await update.callback_query.answer(
        f"⚙️ Upgrading {config['emoji']} {config['name']} to Level {upgrade_info['next_level']}!\n⏱ ETA: {duration_str}"
    )

async def complete_upgrades_for(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Completes any pending upgrades for a player."""
    data = get_player_data(user_id)
    if not data:
        return
    
    now = datetime.utcnow()
    completed_upgrades = []
    
    for building_key, field_name in _BUILDING_KEY_TO_FIELD.items():
        timer_field = f"timers_{building_key}_level"
        timer_str = data.get(timer_field)
        
        if not timer_str:
            continue
        
        try:
            end_time = datetime.fromisoformat(timer_str.replace("Z", "+00:00"))
            if end_time <= now:
                # Upgrade is complete
                current_level = int(data.get(field_name, 1))
                new_level = current_level + 1
                update_player_data(user_id, field_name, new_level)
                update_player_data(user_id, timer_field, None)  # Clear timer
                
                config = get_building_config(building_key)
                completed_upgrades.append(f"✅ {config['emoji']} {config['name']} upgraded to Level {new_level}!")
        except (ValueError, TypeError):
            continue
    
    if completed_upgrades:
        # Send notification about completed upgrades
        message = "Base stats updated:\n" + "\n".join(completed_upgrades)
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception:
            pass  # Ignore if we can't send the message

def setup_building_system(app: Application) -> None:
    """Sets up the building system handlers and scheduler."""
    # Add handlers
    app.add_handler(CommandHandler("build", build_menu))
    app.add_handler(CallbackQueryHandler(build_menu, pattern="^BUILD_MENU$"))
    app.add_handler(CallbackQueryHandler(build_choice, pattern="^BUILD_[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(confirm_build, pattern="^CONFIRM_[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(cancel_build, pattern="^CANCEL_BUILD$"))
    app.add_handler(CallbackQueryHandler(show_building_info, pattern="^INFO_[a-z_]+$"))
    
    # Add scheduler job to check for completed upgrades
    app.job_queue.run_repeating(
        lambda context: complete_upgrades_for(context.user_data.get('user_id'), context),
        interval=60,  # Check every minute
        first=10  # Start after 10 seconds
    )

def get_upgrade_info(building_key: str, current_level: int) -> Optional[Dict[str, Any]]:
    """Gets detailed upgrade information for a building."""
    config = get_building_config(building_key)
    if not config or current_level >= config["max_level"]:
        return None
    
    next_level = current_level + 1
    
    # Calculate costs
    costs = {}
    for resource, base_cost in config["base_costs"].items():
        costs[resource] = math.ceil(base_cost * (config["cost_multiplier"] ** current_level))
    
    # Calculate duration
    duration = math.ceil(config["base_time"] * (config["time_multiplier"] ** current_level))
    
    # Calculate benefits
    benefits = []
    if "wood_production_per_level" in config["effects"]:
        current_output = config["effects"]["wood_production_per_level"] * current_level
        next_output = config["effects"]["wood_production_per_level"] * next_level
        benefits.append(f"🪵 {current_output}/hr → {next_output}/hr")
    elif "stone_production_per_level" in config["effects"]:
        current_output = config["effects"]["stone_production_per_level"] * current_level
        next_output = config["effects"]["stone_production_per_level"] * next_level
        benefits.append(f"🪨 {current_output}/hr → {next_output}/hr")
    elif "food_production_per_level" in config["effects"]:
        current_output = config["effects"]["food_production_per_level"] * current_level
        next_output = config["effects"]["food_production_per_level"] * next_level
        benefits.append(f"🥖 {current_output}/hr → {next_output}/hr")
    elif "gold_production_per_level" in config["effects"]:
        current_output = config["effects"]["gold_production_per_level"] * current_level
        next_output = config["effects"]["gold_production_per_level"] * next_level
        benefits.append(f"💰 {current_output}/hr → {next_output}/hr")
    elif "energy_production_per_level" in config["effects"]:
        current_output = config["effects"]["energy_production_per_level"] * current_level
        next_output = config["effects"]["energy_production_per_level"] * next_level
        benefits.append(f"⚡ {current_output}/hr → {next_output}/hr")
    
    # Add percentage-based effects
    if "upgrade_time_reduction_per_level" in config["effects"]:
        current_reduction = config["effects"]["upgrade_time_reduction_per_level"] * current_level * 100
        next_reduction = config["effects"]["upgrade_time_reduction_per_level"] * next_level * 100
        benefits.append(f"⏱️ Upgrade time -{current_reduction:.0f}% → -{next_reduction:.0f}%")
    if "infantry_training_time_reduction_per_level" in config["effects"]:
        current_reduction = config["effects"]["infantry_training_time_reduction_per_level"] * current_level * 100
        next_reduction = config["effects"]["infantry_training_time_reduction_per_level"] * next_level * 100
        benefits.append(f"🪖 Training time -{current_reduction:.0f}% → -{next_reduction:.0f}%")
    if "research_time_reduction_per_level" in config["effects"]:
        current_reduction = config["effects"]["research_time_reduction_per_level"] * current_level * 100
        next_reduction = config["effects"]["research_time_reduction_per_level"] * next_level * 100
        benefits.append(f"🧪 Research time -{current_reduction:.0f}% → -{next_reduction:.0f}%")
    if "healing_time_reduction_per_level" in config["effects"]:
        current_reduction = config["effects"]["healing_time_reduction_per_level"] * current_level * 100
        next_reduction = config["effects"]["healing_time_reduction_per_level"] * next_level * 100
        benefits.append(f"🏥 Healing time -{current_reduction:.0f}% → -{next_reduction:.0f}%")
    if "vehicle_training_time_reduction_per_level" in config["effects"]:
        current_reduction = config["effects"]["vehicle_training_time_reduction_per_level"] * current_level * 100
        next_reduction = config["effects"]["vehicle_training_time_reduction_per_level"] * next_level * 100
        benefits.append(f"🔧 Vehicle training -{current_reduction:.0f}% → -{next_reduction:.0f}%")
    
    # Add capacity increases
    if "capacity_increase_per_level" in config["effects"]:
        current_capacity = config["effects"]["capacity_increase_per_level"] * current_level
        next_capacity = config["effects"]["capacity_increase_per_level"] * next_level
        benefits.append(f"📦 Capacity {current_capacity} → {next_capacity}")
    
    # Add unlocks
    if "unlocks" in config["effects"]:
        for unit, level in config["effects"]["unlocks"].items():
            if next_level == level:
                benefits.append(f"🔓 Unlocks {unit}")
    
    return {
        "cost": costs,
        "duration": duration * 60,  # Convert to seconds
        "next_level": next_level,
        "benefits": benefits
    }

def get_ongoing_upgrade(user_id: int) -> Optional[Dict[str, Any]]:
    """Gets information about any ongoing upgrade for a player."""
    data = get_player_data(user_id)
    if not data:
        return None
    
    now = datetime.utcnow()
    
    for building_key, field_name in _BUILDING_KEY_TO_FIELD.items():
        timer_field = f"timers_{building_key}_level"
        timer_str = data.get(timer_field)
        
        if not timer_str:
            continue
        
        try:
            end_time = datetime.fromisoformat(timer_str.replace("Z", "+00:00"))
            if end_time > now:
                config = get_building_config(building_key)
                current_level = int(data.get(field_name, 1))
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                
                return {
                    "building": config["name"],
                    "emoji": config["emoji"],
                    "current_level": current_level,
                    "next_level": current_level + 1,
                    "remaining": time_str,
                    "end_time": end_time
                }
        except (ValueError, TypeError):
            continue
    
    return None

async def show_building_info(update: Update, context: ContextTypes.DEFAULT_TYPE, building_key: str) -> None:
    """Shows detailed information about a building's levels and effects."""
    query = update.callback_query
    await query.answer()
    
    config = get_building_config(building_key)
    if not config:
        await query.edit_message_text("❌ Invalid building selected\.")
        return
    
    # Build level table
    table_lines = []
    for level in range(1, config["max_level"] + 1):
        upgrade_info = get_upgrade_info(building_key, level - 1)
        if not upgrade_info:
            continue
        
        # Format costs
        cost_display = []
        for resource, amount in upgrade_info["cost"].items():
            emoji_map = {"wood": "🪵", "stone": "🪨", "food": "🥖", "gold": "💰", "energy": "⚡"}
            cost_display.append(f"{emoji_map.get(resource, '')} {amount}")
        cost_str = " / ".join(cost_display)
        
        # Format duration
        minutes = upgrade_info["duration"] // 60
        hours = minutes // 60
        minutes = minutes % 60
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Format benefits
        benefits_str = " | ".join(upgrade_info["benefits"])
        
        table_lines.append(f"*Level {level}*")
        table_lines.append(f"Cost: {cost_str}")
        table_lines.append(f"Time: {duration_str}")
        table_lines.append(f"Effects: {benefits_str}")
        table_lines.append("")
    
    # Build message
    msg_lines = [
        f"{config['emoji']} *{escape_markdown(config['name'])}*",
        "Building Information:",
        "\-\-\-",
        *table_lines,
        "\-\-\-",
        "🏠 Back to Base"
    ]
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")]]
    
    await query.edit_message_text(
        "\n".join(msg_lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    ) 