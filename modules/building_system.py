import math # For ceil in cost/time calculation
from typing import Dict, Any, List, Optional
from telegram import constants # Required for parse_mode in build_menu, build_choice
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # For build_menu, build_choice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes # For setup_building_system
from telegram.helpers import escape_markdown # For MarkdownV2 escaping

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
            "build_slots_unlock_levels": [5, 10, 15]
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
            "wood_production_per_level": 10
        },
        "unlock_requirements": {}
    },
    "mine": { # This is for Quarry (stone) and Gold Mine (gold) as they share 'mine_level'
        "key": "mine", # Will be used for both "Quarry" and "Gold Mine" conceptual buildings
        "name": "Mine (Stone)",
        "emoji": "⛏️",
        "max_level": 20,
        "base_costs": {"wood": 40, "stone": 60, "food": 10, "gold": 8, "energy": 3},
        "base_time": 10, # minutes
        "cost_multiplier": 1.12,
        "time_multiplier": 1.18,
        "effects": {
            "stone_production_per_level": 10 # This is Quarry's effect
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
            "energy_production_per_level": 5
        },
        "unlock_requirements": {}
    },
    "barracks": {
        "key": "barracks",
        "name": "Barracks",
        "emoji": "🪖",
        "max_level": 10,
        "base_costs": {"wood": 80, "stone": 60, "food": 40, "gold": 25, "energy": 15},
        "base_time": 20, # minutes
        "cost_multiplier": 1.18,
        "time_multiplier": 1.25,
        "effects": {
            "infantry_training_time_reduction_per_level": 0.05,
            "unlocks": {"artillery": 5, "tank": 10}
        },
        "unlock_requirements": {}
    },
    "research_lab": {
        "key": "research_lab",
        "name": "Research Lab",
        "emoji": "🧪",
        "max_level": 10,
        "base_costs": {"wood": 75, "stone": 75, "food": 50, "gold": 40, "energy": 20},
        "base_time": 25, # minutes
        "cost_multiplier": 1.17,
        "time_multiplier": 1.24,
        "effects": {
            "research_time_reduction_per_level": 0.05,
            "unlocks": {"tech_tiers": "per doc"} # Placeholder for now as doc doesn't specify tiers
        },
        "unlock_requirements": {}
    },
    "hospital": {
        "key": "hospital",
        "name": "Hospital",
        "emoji": "🏥",
        "max_level": 10,
        "base_costs": {"wood": 60, "stone": 50, "food": 30, "gold": 20, "energy": 10},
        "base_time": 15, # minutes
        "cost_multiplier": 1.16,
        "time_multiplier": 1.22,
        "effects": {
            "healing_time_reduction_per_level": 0.05,
            "capacity_increase_per_level": 10
        },
        "unlock_requirements": {}
    },
    "workshop": {
        "key": "workshop",
        "name": "Workshop",
        "emoji": "🔧",
        "max_level": 10,
        "base_costs": {"wood": 90, "stone": 80, "food": 50, "gold": 35, "energy": 20},
        "base_time": 25, # minutes
        "cost_multiplier": 1.19,
        "time_multiplier": 1.26,
        "effects": {
            "vehicle_training_time_reduction_per_level": 0.05,
            "unlocks": {"destroyer": 8}
        },
        "unlock_requirements": {}
    },
    "jail": {
        "key": "jail",
        "name": "Jail",
        "emoji": "🚔",
        "max_level": 10,
        "base_costs": {"wood": 70, "stone": 60, "food": 40, "gold": 30, "energy": 15},
        "base_time": 20, # minutes
        "cost_multiplier": 1.17,
        "time_multiplier": 1.23,
        "effects": {}, # No effects specified in doc
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
    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        if update.message:
            await update.message.reply_text("❌ You aren't registered yet\. Send /start to begin\.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ You aren't registered yet\. Send /start to begin\.")
        return

    msg_lines = ["⚒️ *[BUILD MENU]*", "Choose a building to upgrade:", ""]

    keyboard_buttons = []
    # Sort buildings by their display name for consistent order
    sorted_building_keys = sorted(BUILDING_CONFIG.keys(), key=lambda k: BUILDING_CONFIG[k]["name"])

    for building_key in sorted_building_keys:
        config = BUILDING_CONFIG[building_key]
        field_name = _BUILDING_KEY_TO_FIELD.get(building_key)
        if not field_name:
            continue
        
        current_level = int(data.get(field_name, 1))
        
        msg_lines.append(f"{config['emoji']} {escape_markdown(config['name'])}: Lv {escape_markdown(str(current_level))}")
        
        # Add button for upgrade if not max level
        if current_level < config['max_level']:
            keyboard_buttons.append(
                [InlineKeyboardButton(f"{config['emoji']} {escape_markdown(config['name'])}", callback_data=f"BUILD_{building_key}")]
            )
        else:
            # Indicate max level
            keyboard_buttons.append(
                [InlineKeyboardButton(f"✅ {escape_markdown(config['name'])} \(Max Level\)", callback_data=f"INFO_{building_key}")]
            ) # Using INFO_ to avoid triggering build_choice for maxed buildings

    msg_lines.append("\n🏠 Back to Base") # Add backslash for newline
    keyboard_buttons.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")])

    msg = "\n".join(msg_lines) # Use \n for internal joins, Telegram will handle the newlines.
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    if update.message:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2, # Use MARKDOWN_V2
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2, # Use MARKDOWN_V2
        )


async def build_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if current_level >= config["max_level"]:
        await query.edit_message_text(f"✅ {escape_markdown(config['name'])} is already at max level \({escape_markdown(str(config['max_level']))}\)\.")
        return

    next_level = current_level + 1

    # Calculate costs and time using helper functions
    costs = calculate_upgrade_cost(data, building_key)
    time_mins = calculate_upgrade_time(data, building_key)

    # Format costs
    cost_display = []
    for resource, amount in costs.items():
        # Add emojis for resources. Assuming resource keys match.
        emoji_map = {"wood": "🪵", "stone": "🪨", "food": "🥖", "gold": "💰", "energy": "⚡"}
        cost_display.append(f"{emoji_map.get(resource, '')} {escape_markdown(str(amount))}") # Escape amount
    
    cost_str = " ".join(cost_display)

    # Determine next level effects
    effects_lines = []
    if building_key == "town_hall":
        reduction = (next_level * config["effects"]["upgrade_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces all upgrade times by {escape_markdown(f'{reduction:.0f}%')}") # Escape %
        if next_level in config["effects"]["build_slots_unlock_levels"]:
            effects_lines.append("Unlocks new build slot")
    elif "wood_production_per_level" in config["effects"] or \
         "stone_production_per_level" in config["effects"] or \
         "food_production_per_level" in config["effects"] or \
         "gold_production_per_level" in config["effects"] or \
         "energy_production_per_level" in config["effects"]:
        for effect_type, value in config["effects"].items():
            if "_production_per_level" in effect_type:
                resource_name = effect_type.replace("_production_per_level", "").replace("_", " ").capitalize()
                effects_lines.append(f"\+{escape_markdown(str(value))} {escape_markdown(resource_name)}/hr") # Escape + and / 
    elif building_key == "barracks":
        reduction = (next_level * config["effects"]["infantry_training_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces infantry training time by {escape_markdown(f'{reduction:.0f}%')}")
        for unit, level in config["effects"]["unlocks"].items():
            if next_level == level:
                effects_lines.append(f"Unlocks {escape_markdown(unit)}")
    elif building_key == "research_lab":
        reduction = (next_level * config["effects"]["research_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces research time by {escape_markdown(f'{reduction:.0f}%')}")
        if "tech_tiers" in config["effects"]["unlocks"] and next_level in config["effects"]["unlocks"]["tech_tiers"]:
            effects_lines.append(f"Unlocks Tech Tier {escape_markdown(str(next_level))}")
    elif building_key == "hospital":
        reduction = (next_level * config["effects"]["healing_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces healing time by {escape_markdown(f'{reduction:.0f}%')}")
        effects_lines.append(f"\+{escape_markdown(str(config['effects']['capacity_increase_per_level']))} Hospital capacity") # Escape + 
    elif building_key == "workshop":
        reduction = (next_level * config["effects"]["vehicle_training_time_reduction_per_level"]) * 100
        effects_lines.append(f"Reduces vehicle training time by {escape_markdown(f'{reduction:.0f}%')}")
        for unit, level in config["effects"]["unlocks"].items():
            if next_level == level:
                effects_lines.append(f"Unlocks {escape_markdown(unit)}")
    
    effects_str = "\n".join([f"• {line}" for line in effects_lines]) if effects_lines else "No specific effects for next level\." # Escape . and newlines


    # Build the message
    msg = "\n".join([
        f"{config['emoji']} *{escape_markdown(config['name'])}: Level {escape_markdown(str(current_level))} → {escape_markdown(str(next_level))}*",
        "\-\-\- ", # Escape hyphens for markdown
        f"💰 Cost: {cost_str}",
        f"⏱️ Time: {escape_markdown(str(time_mins))}m",
        "\-\-\- ", # Escape hyphens for markdown
        "*Next Level Effects:*",
        effects_str
    ])

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM_{building_key}"),
            InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_BUILD"),
        ],
    ]

    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN_V2, # Use MARKDOWN_V2
    )

async def confirm_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if current_level >= config["max_level"]:
        await query.edit_message_text(f"✅ {escape_markdown(config['name'])} is already at max level \({escape_markdown(str(config['max_level']))}\)\.")
        return

    costs = calculate_upgrade_cost(data, building_key)
    time_mins = calculate_upgrade_time(data, building_key) # This is for timer/display, not for deduction logic here.

    # Check if player has enough resources
    player_resources = {
        "wood": int(data.get("resources_wood", 0)),
        "stone": int(data.get("resources_stone", 0)),
        "food": int(data.get("resources_food", 0)),
        "gold": int(data.get("resources_gold", 0)),
        "energy": int(data.get("resources_energy", 0)),
    }

    not_enough_resources = []
    for resource, cost in costs.items():
        if player_resources.get(resource, 0) < cost:
            not_enough_resources.append(resource.capitalize())

    if not_enough_resources:
        await query.edit_message_text(f"❌ Not enough resources: {escape_markdown(', '.join(not_enough_resources))}\.") # Escape comma and dot
        return

    # Deduct resources
    for resource, cost in costs.items():
        update_player_data(user.id, f"resources_{resource}", player_resources[resource] - cost)

    # Increment building level
    update_player_data(user.id, field_name, current_level + 1)

    # Confirm message
    msg = "\n".join([
        "✔️ Upgrade started\!", # Escape !
        f"🕒 Complete in {escape_markdown(str(time_mins))} minutes\." # Escape .
    ])

    await query.edit_message_text(msg, parse_mode=constants.ParseMode.MARKDOWN_V2)

async def cancel_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Build cancelled\.", parse_mode=constants.ParseMode.MARKDOWN_V2) # Escape .

def setup_building_system(app: Application) -> None:
    """Register building system handlers."""
    app.add_handler(CommandHandler("build", build_menu))

    # now also catch the inline "⚒️ Build" button
    app.add_handler(CallbackQueryHandler(build_menu, pattern="^BUILD_MENU$"))

    app.add_handler(CallbackQueryHandler(build_choice, pattern="^BUILD_"))
    app.add_handler(CallbackQueryHandler(confirm_build, pattern="^CONFIRM_"))
    app.add_handler(CallbackQueryHandler(cancel_build, pattern="^CANCEL_BUILD$")) 