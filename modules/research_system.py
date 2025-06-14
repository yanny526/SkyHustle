from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.helpers import escape_markdown

from modules.sheets_helper import get_player_data, update_player_data, deduct_resources, can_afford, record_active_research, fetch_active_research, clear_active_research, apply_research_effects, add_player_effect
from modules.base_ui import escape_markdown_v2

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ResearchEntry:
    id: str
    name: str
    description: str
    costs: Dict[str, int]
    duration: int  # in seconds
    effects: Dict[str, Any]

RESEARCH_CATALOG = {
    "adv_mining": ResearchEntry(
        id="adv_mining",
        name="🔬 Advanced Mining",
        description="Boosts stone & gold output by 10%—accelerate your empire's growth.",
        costs={"resources_stone": 500, "resources_gold": 300, "resources_energy": 50},
        duration=3600,  # 1 hour
        effects={"mine_output_pct": 10}
    ),
    "infantry_tactics": ResearchEntry(
        id="infantry_tactics",
        name="⚔️ Infantry Tactics",
        description="Enhances infantry attack by 15%—crush your foes with superior strategy.",
        costs={"resources_gold": 600, "resources_wood": 400, "resources_food": 200},
        duration=7200,  # 2 hours
        effects={"infantry_attack_pct": 15}
    ),
    "energy_efficiency": ResearchEntry(
        id="energy_efficiency",
        name="⚡ Energy Efficiency",
        description="Reduces energy consumption for all activities by 20%—power your empire sustainably.",
        costs={"resources_energy": 700, "resources_stone": 300},
        duration=5400,  # 1.5 hours
        effects={"energy_consumption_pct_reduction": 20}
    ),
    "fortified_walls": ResearchEntry(
        id="fortified_walls",
        name="🛡️ Fortified Walls",
        description="Increases base defense by 15%—protect your stronghold from raids.",
        costs={"resources_stone": 800, "resources_wood": 500},
        duration=10800, # 3 hours
        effects={"base_defense_pct": 15}
    ),
    "market_optimization": ResearchEntry(
        id="market_optimization",
        name="💰 Market Optimization",
        description="Improves Black Market trading efficiency by 10%—maximize your profits.",
        costs={"resources_gold": 400, "resources_food": 300, "resources_energy": 100},
        duration=2700, # 45 minutes
        effects={"market_efficiency_pct": 10}
    )
}

# 2. Core Functions in modules/research_system.py
def start_research(player_id: int, research_id: str) -> bool:
    """Check resources, deduct costs, record start time + ID in Sheets."""
    player_data = get_player_data(player_id)
    if not player_data:
        logger.warning(f"start_research: Player {player_id} not found.")
        return False

    if player_data.get("research_id"):
        logger.info(f"start_research: Player {player_id} already has active research.")
        return False # Already has active research

    research_info = RESEARCH_CATALOG.get(research_id)
    if not research_info:
        logger.warning(f"start_research: Research ID {research_id} not found in catalog.")
        return False

    # Check resources
    can_afford = True
    for resource, cost in research_info.costs.items():
        if player_data.get(resource, 0) < cost:
            can_afford = False
            break

    if not can_afford:
        logger.info(f"start_research: Player {player_id} cannot afford {research_info.name}.")
        return False

    # Deduct costs
    if not deduct_resources(player_id, research_info.costs):
        logger.error(f"Failed to deduct resources for player {player_id} for research {research_id}.")
        return False

    # Record research in player data
    now_utc = datetime.now(timezone.utc)
    finish_at = now_utc + timedelta(seconds=research_info.duration)

    record_active_research(player_id, research_id, now_utc, finish_at, research_info.name)
    logger.info(f"start_research: Player {player_id} successfully started research {research_info.name}.")
    return True

def get_active_research(player_id: int) -> Optional[ResearchEntry]:
    """Fetch ongoing research from Sheets; return its name and remaining time."""
    active_research_data = fetch_active_research_data(player_id)
    if active_research_data:
        research_id = active_research_data["research_id"]
        research_name_display = active_research_data["research_name_display"]
        finish_at = active_research_data["research_finish_at"]

        if research_id in RESEARCH_CATALOG:
            research_info = RESEARCH_CATALOG[research_id]
            now_utc = datetime.now(timezone.utc)
            if finish_at > now_utc:
                # Research is still ongoing
                # Return the full ResearchEntry object for consistency
                return ResearchEntry(id=research_id,
                                     name=research_name_display or research_info.name,
                                     description=research_info.description,
                                     costs=research_info.costs,
                                     duration=research_info.duration,
                                     effects=research_info.effects)
            else:
                # Research is finished but not yet completed/cleared
                logger.info(f"Research {research_id} for player {player_id} is finished but not yet processed.")
                # Return the full ResearchEntry object even if finished, so complete_research can process it.
                return ResearchEntry(id=research_id,
                                     name=research_name_display or research_info.name,
                                     description=research_info.description,
                                     costs=research_info.costs,
                                     duration=research_info.duration,
                                     effects=research_info.effects)
        else:
            logger.warning(f"Active research ID {research_id} for player {player_id} not found in catalog.")
            return None
    return None

def complete_research(player_id: int) -> None:
    """When a research ends, apply its effects to the player's stats, clear the entry, and log completion."""
    active_research = get_active_research(player_id)
    if active_research:
        now_utc = datetime.now(timezone.utc)
        if active_research.id in RESEARCH_CATALOG and active_research.end_timestamp <= now_utc:
            research_info = RESEARCH_CATALOG[active_research.id]

            # Apply effects
            apply_research_effects(player_id, research_info.effects)

            # Clear the active research entry
            clear_active_research(player_id)
            logger.info(f"Research '{research_info.name}' completed and effects applied for player {player_id}.")
        elif active_research.end_timestamp > now_utc:
            logger.info(f"Research '{active_research.name}' for player {player_id} is not yet due for completion.")
        else:
            logger.warning(f"Active research ID {active_research.id} for player {player_id} not found in catalog or invalid state.")
    else:
        logger.info(f"No active research to complete for player {player_id}.")

# Telegram Handlers

async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /research command, displaying available research and active research status."""
    user_id = update.effective_user.id
    player_data = get_player_data(user_id)

    if not player_data:
        await update.message.reply_text("Welcome, new player! Please use /start to begin your adventure.")
        return

    message_parts = ["*🔬 Available Research*\n"]
    keyboard = []

    for r_id, r_info in RESEARCH_CATALOG.items():
        cost_str_parts = []
        for res, amount in r_info.costs.items():
            emoji = ""
            if "gold" in res: emoji = "💰"
            elif "wood" in res: emoji = "🪵"
            elif "stone" in res: emoji = "🪨"
            elif "food" in res: emoji = "🍖"
            elif "energy" in res: emoji = "⚡"
            cost_str_parts.append(f"{emoji}{amount}")
        cost_str = "  ".join(cost_str_parts)

        duration_hours, remainder = divmod(r_info.duration, 3600)
        duration_minutes, _ = divmod(remainder, 60)
        duration_str = f"{int(duration_hours)}h {int(duration_minutes)}m"

        message_parts.append(f"\n*{escape_markdown_v2(r_info.name)}*\n")
        message_parts.append(f"   – Cost: {escape_markdown_v2(cost_str)}\n")
        message_parts.append(f"   – Time: \_{escape_markdown_v2(duration_str)}\_\n")
        message_parts.append(f"   – Effect: \"{escape_markdown_v2(r_info.description)}\"\n")

        keyboard.append([InlineKeyboardButton(f"{r_info.name} – Start", callback_data=f"start_research:{r_id}")])
    
    # Add active research status at the bottom
    active_research = get_active_research(user_id)
    if active_research:
        time_remaining_seconds = (active_research.finish_at - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if time_remaining_seconds > 0:
            hours, remainder = divmod(int(time_remaining_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            message_parts.append(f"\n_Active Research: {escape_markdown_v2(active_research.name)} — {escape_markdown_v2(time_str)} remaining_\n")
        else:
            message_parts.append(f"\n_Active Research: {escape_markdown_v2(active_research.name)} — Completed \(type /research again to apply\)_\n")
    else:
        message_parts.append(f"\n_Active Research: None_\n")


    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="base")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "".join(message_parts),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def handle_research_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callbacks from the research menu."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    action, research_id = data.split(":")

    if action == "start_research":
        if start_research(user_id, research_id):
            await query.edit_message_text(
                f"🔬 You have started *{escape_markdown_v2(RESEARCH_CATALOG[research_id].name)}*\! It will be completed at {escape_markdown_v2(get_active_research(user_id).finish_at.strftime('%H:%M UTC'))}\.",
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        else:
            await query.edit_message_text(
                f"😔 You do not have enough resources to start *{escape_markdown_v2(RESEARCH_CATALOG[research_id].name)}* or another research is already active\.",
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
    # Other research-related actions can be added here

def setup_research_system(app: Application) -> None:
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CallbackQueryHandler(handle_research_callback, pattern="^start_research:")) 