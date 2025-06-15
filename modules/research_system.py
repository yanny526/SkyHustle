from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode

from modules.sheets_helper import (
    get_player_data,
    update_player_data,
    get_player_buildings,
)

# Research categories
RESEARCH_CATEGORIES = ["Economy", "Military", "Tech", "Special"]

# Research configuration
RESEARCH_CATALOG = {
    "advanced_mining": {
        "id": "advanced_mining",
        "category": "Economy",
        "name": "Advanced Mining",
        "description": "Increases mine yield by 5% per level.",
        "max_level": 5,
        "base_costs": {
            "wood": 100,
            "stone": 50,
            "food": 25,
            "gold": 0,
            "energy": 10,
            "rp": 20
        },
        "base_time": 5400,  # 1h 30m in seconds
        "cost_multiplier": 1.15,
        "time_multiplier": 1.2,
        "effects": {
            "mine_yield_bonus_per_level": 0.05  # 5% per level
        },
        "prerequisites": {
            "research_lab_level": 1
        }
    },
    "reinforced_walls": {
        "id": "reinforced_walls",
        "category": "Military",
        "name": "Reinforced Walls",
        "description": "Increases base defense by 10% per level.",
        "max_level": 3,
        "base_costs": {
            "wood": 75,
            "stone": 200,
            "food": 0,
            "gold": 50,
            "energy": 15,
            "rp": 30
        },
        "base_time": 7200,  # 2h in seconds
        "cost_multiplier": 1.2,
        "time_multiplier": 1.25,
        "effects": {
            "base_defense_bonus_per_level": 0.10  # 10% per level
        },
        "prerequisites": {
            "base_level": 2
        }
    }
}

def get_research_info(research_id: str) -> Optional[Dict[str, Any]]:
    """Get research configuration by ID."""
    return RESEARCH_CATALOG.get(research_id)

def calculate_research_cost(research_id: str, current_level: int) -> Dict[str, int]:
    """Calculate costs for a research level upgrade."""
    research = get_research_info(research_id)
    if not research:
        return {}
    
    costs = {}
    for resource, base_cost in research["base_costs"].items():
        costs[f"resources_{resource}"] = int(base_cost * (research["cost_multiplier"] ** current_level))
    
    return costs

def calculate_research_time(research_id: str, current_level: int) -> int:
    """Calculate time in seconds for a research level upgrade."""
    research = get_research_info(research_id)
    if not research:
        return 0
    
    return int(research["base_time"] * (research["time_multiplier"] ** current_level))

def can_start_research(player_data: Dict[str, Any], research_id: str) -> Tuple[bool, str]:
    """Check if player can start a research project."""
    research = get_research_info(research_id)
    if not research:
        return False, "Invalid research project"
    
    # Check if max level reached
    current_level = player_data.get(f"research_{research_id}_level", 0)
    if current_level >= research["max_level"]:
        return False, "Maximum level reached"
    
    # Check prerequisites
    for prereq, required_level in research["prerequisites"].items():
        if player_data.get(prereq, 0) < required_level:
            return False, f"Requires {prereq.replace('_', ' ').title()} level {required_level}"
    
    # Check resource costs
    costs = calculate_research_cost(research_id, current_level)
    for resource, amount in costs.items():
        if player_data.get(resource, 0) < amount:
            return False, f"Not enough {resource.replace('resources_', '')}"
    
    # Check RP cost
    rp_cost = costs.get("resources_rp", 0)
    if player_data.get("research_balance", 0) < rp_cost:
        return False, "Not enough Research Points"
    
    return True, ""

def start_research(player_id: int, research_id: str) -> bool:
    """Start a research project for a player."""
    player_data = get_player_data(player_id)
    if not player_data:
        return False
    
    can_start, error_msg = can_start_research(player_data, research_id)
    if not can_start:
        return False
    
    # Calculate costs and time
    current_level = player_data.get(f"research_{research_id}_level", 0)
    costs = calculate_research_cost(research_id, current_level)
    duration = calculate_research_time(research_id, current_level)
    
    # Deduct resources
    for resource, amount in costs.items():
        current = player_data.get(resource, 0)
        update_player_data(player_id, resource, current - amount)
    
    # Set active research
    now = datetime.utcnow()
    finish_at = now + timedelta(seconds=duration)
    
    update_player_data(player_id, "active_research_id", research_id)
    update_player_data(player_id, "research_start", now.isoformat())
    update_player_data(player_id, "research_finish", finish_at.isoformat())
    
    return True

def complete_research(player_id: int) -> bool:
    """Complete an active research project."""
    player_data = get_player_data(player_id)
    if not player_data:
        return False
    
    research_id = player_data.get("active_research_id")
    if not research_id:
        return False
    
    finish_time = player_data.get("research_finish")
    if not finish_time:
        return False
    
    try:
        finish_at = datetime.fromisoformat(finish_time)
        if datetime.utcnow() < finish_at:
            return False
    except ValueError:
        return False
    
    # Increment research level
    current_level = player_data.get(f"research_{research_id}_level", 0)
    update_player_data(player_id, f"research_{research_id}_level", current_level + 1)
    
    # Clear active research
    update_player_data(player_id, "active_research_id", "")
    update_player_data(player_id, "research_start", "")
    update_player_data(player_id, "research_finish", "")
    
    return True

def get_active_research(player_id: int) -> Optional[Dict[str, Any]]:
    """Get information about player's active research."""
    player_data = get_player_data(player_id)
    if not player_data:
        return None
    
    research_id = player_data.get("active_research_id")
    if not research_id:
        return None
    
    research = get_research_info(research_id)
    if not research:
        return None
    
    start_time = player_data.get("research_start")
    finish_time = player_data.get("research_finish")
    if not start_time or not finish_time:
        return None
    
    try:
        start = datetime.fromisoformat(start_time)
        finish = datetime.fromisoformat(finish_time)
        now = datetime.utcnow()
        
        if now >= finish:
            return None
        
        progress = (now - start) / (finish - start)
        remaining = finish - now
        
        return {
            "research": research,
            "progress": progress,
            "remaining_seconds": int(remaining.total_seconds())
        }
    except ValueError:
        return None

async def research_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the research menu."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    player_data = get_player_data(query.from_user.id)
    if not player_data:
        await query.edit_message_text(
            "❌ You need to register first! Use /start to begin.",
            parse_mode=None
        )
        return
    
    # Build category buttons
    keyboard = []
    for category in RESEARCH_CATEGORIES:
        keyboard.append([
            InlineKeyboardButton(
                f"🔬 {category}",
                callback_data=f"RESEARCH_CAT_{category}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")
    ])
    
    # Show menu
    await query.edit_message_text(
        f"🔬 *Research Lab*\n\n"
        f"Research Points: `{player_data.get('research_balance', 0)}` / "
        f"`{player_data.get('capacity_research', 0)}`\n\n"
        f"Select a category to view available research:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def research_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show research projects in a category."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    category = query.data.split("_")[-1]
    if category not in RESEARCH_CATEGORIES:
        return
    
    player_data = get_player_data(query.from_user.id)
    if not player_data:
        return
    
    # Filter research by category
    research_list = [
        research for research in RESEARCH_CATALOG.values()
        if research["category"] == category
    ]
    
    # Build research cards
    keyboard = []
    for research in research_list:
        current_level = player_data.get(f"research_{research['id']}_level", 0)
        can_start, error_msg = can_start_research(player_data, research["id"])
        
        # Calculate costs for display
        costs = calculate_research_cost(research["id"], current_level)
        cost_text = []
        for resource, amount in costs.items():
            if amount > 0:
                emoji = {
                    "resources_wood": "🪵",
                    "resources_stone": "🪨",
                    "resources_food": "🍞",
                    "resources_gold": "💰",
                    "resources_energy": "⚡",
                    "resources_rp": "🔬"
                }.get(resource, "")
                cost_text.append(f"{emoji} {amount}")
        
        # Build button text
        if research["id"] == player_data.get("active_research_id"):
            button_text = "⏳ In Progress"
        elif can_start:
            button_text = "▶️ Start"
        else:
            button_text = "🔒 Locked"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{research['name']} (Lv {current_level}→{current_level + 1})",
                callback_data=f"RESEARCH_INFO_{research['id']}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"{' '.join(cost_text)} | {button_text}",
                callback_data=f"RESEARCH_START_{research['id']}" if can_start else "RESEARCH_LOCKED"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Categories", callback_data="RESEARCH_MENU")
    ])
    
    # Show research list
    await query.edit_message_text(
        f"🔬 *{category} Research*\n\n"
        f"Select a research project to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def research_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed information about a research project."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    research_id = query.data.split("_")[-1]
    research = get_research_info(research_id)
    if not research:
        return
    
    player_data = get_player_data(query.from_user.id)
    if not player_data:
        return
    
    current_level = player_data.get(f"research_{research_id}_level", 0)
    can_start, error_msg = can_start_research(player_data, research_id)
    
    # Calculate costs and time
    costs = calculate_research_cost(research_id, current_level)
    duration = calculate_research_time(research_id, current_level)
    
    # Format costs
    cost_text = []
    for resource, amount in costs.items():
        if amount > 0:
            emoji = {
                "resources_wood": "🪵",
                "resources_stone": "🪨",
                "resources_food": "🍞",
                "resources_gold": "💰",
                "resources_energy": "⚡",
                "resources_rp": "🔬"
            }.get(resource, "")
            cost_text.append(f"{emoji} {amount}")
    
    # Format prerequisites
    prereq_text = []
    for prereq, required_level in research["prerequisites"].items():
        current = player_data.get(prereq, 0)
        prereq_text.append(
            f"• {prereq.replace('_', ' ').title()} Level {current}/{required_level}"
        )
    
    # Build message
    message = (
        f"🔬 *{research['name']}*\n"
        f"Level {current_level} → {current_level + 1}\n\n"
        f"{research['description']}\n\n"
    )
    
    if prereq_text:
        message += "Prerequisites:\n" + "\n".join(prereq_text) + "\n\n"
    
    message += (
        f"Cost: {' '.join(cost_text)}\n"
        f"Time: {duration // 3600}h {(duration % 3600) // 60}m\n\n"
    )
    
    if research_id == player_data.get("active_research_id"):
        active = get_active_research(query.from_user.id)
        if active:
            progress = int(active["progress"] * 10)
            progress_bar = "█" * progress + "░" * (10 - progress)
            remaining = active["remaining_seconds"]
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            message += (
                f"Progress: [{progress_bar}] {hours}h {minutes}m remaining\n\n"
                "Buttons: [Cancel] [Speed Up]"
            )
    elif can_start:
        message += "Click 'Start' to begin research"
    else:
        message += f"🔒 {error_msg}"
    
    # Build keyboard
    keyboard = []
    if research_id == player_data.get("active_research_id"):
        keyboard.extend([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"RESEARCH_CANCEL_{research_id}")],
            [InlineKeyboardButton("⚡ Speed Up", callback_data=f"RESEARCH_SPEED_{research_id}")]
        ])
    elif can_start:
        keyboard.append([
            InlineKeyboardButton("▶️ Start Research", callback_data=f"RESEARCH_START_{research_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Back to List", callback_data=f"RESEARCH_CAT_{research['category']}")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def start_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle starting a research project."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    research_id = query.data.split("_")[-1]
    if start_research(query.from_user.id, research_id):
        research = get_research_info(research_id)
        duration = calculate_research_time(research_id, 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        
        await query.edit_message_text(
            f"✅ Research '{research['name']}' started!\n"
            f"Completes in {hours}h {minutes}m",
            parse_mode=None
        )
    else:
        await query.edit_message_text(
            "❌ Failed to start research. Please try again.",
            parse_mode=None
        )

async def cancel_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancelling a research project."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    research_id = query.data.split("_")[-1]
    player_data = get_player_data(query.from_user.id)
    
    if not player_data or player_data.get("active_research_id") != research_id:
        await query.edit_message_text(
            "❌ No active research to cancel.",
            parse_mode=None
        )
        return
    
    # Clear active research
    update_player_data(query.from_user.id, "active_research_id", "")
    update_player_data(query.from_user.id, "research_start", "")
    update_player_data(query.from_user.id, "research_finish", "")
    
    await query.edit_message_text(
        "✅ Research cancelled.",
        parse_mode=None
    )

async def speed_up_research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle speeding up a research project."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    
    await query.answer()
    
    research_id = query.data.split("_")[-1]
    player_data = get_player_data(query.from_user.id)
    
    if not player_data or player_data.get("active_research_id") != research_id:
        await query.edit_message_text(
            "❌ No active research to speed up.",
            parse_mode=None
        )
        return
    
    # TODO: Implement speed up logic using RP
    await query.edit_message_text(
        "❌ Speed up not implemented yet.",
        parse_mode=None
    )

def setup_research_system(app: Application) -> None:
    """Set up research system handlers."""
    app.add_handler(CallbackQueryHandler(research_menu, pattern="^RESEARCH_MENU$"))
    app.add_handler(CallbackQueryHandler(research_category, pattern="^RESEARCH_CAT_"))
    app.add_handler(CallbackQueryHandler(research_info, pattern="^RESEARCH_INFO_"))
    app.add_handler(CallbackQueryHandler(start_research_handler, pattern="^RESEARCH_START_"))
    app.add_handler(CallbackQueryHandler(cancel_research_handler, pattern="^RESEARCH_CANCEL_"))
    app.add_handler(CallbackQueryHandler(speed_up_research_handler, pattern="^RESEARCH_SPEED_")) 