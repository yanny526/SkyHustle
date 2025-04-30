# tech_tree_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    get_building_level,
    get_tech_upgrades,
    save_tech_upgrade,
)
from utils.ui_helpers import render_status_panel

# ── Tech Definitions ─────────────────────────────────────────────────────────
TECH_TREE = {
    "mining_efficiency": {
        "title": "⛏️ Mining Efficiency",
        "desc": "Boost metal, fuel, and crystal mining rates by 10% per level.",
        "max_level": 5,
        "requirements": {"research_lab": 1},
        "base_cost": {"metal": 500, "crystal": 300},
        "time_min": 10,
    },
    "unit_training_speed": {
        "title": "🏃‍♂️ Rapid Training",
        "desc": "Reduce training time by 8% per level.",
        "max_level": 5,
        "requirements": {"barracks": 2},
        "base_cost": {"metal": 700, "fuel": 500},
        "time_min": 15,
    },
    "drone_navigation": {
        "title": "🛰️ Drone Navigation AI",
        "desc": "Speed up drone missions by 12% per level.",
        "max_level": 3,
        "requirements": {"drone_hangar": 1},
        "base_cost": {"metal": 600, "crystal": 500},
        "time_min": 12,
    },
}
# tech_tree_system.py (Part 2 of X)

def calculate_tech_cost(tech_id: str, level: int) -> dict:
    """Returns scaled cost for a given tech level."""
    base = TECH_TREE[tech_id]["base_cost"]
    return {k: int(v * (1.6 ** (level - 1))) for k, v in base.items()}

def get_player_tech_level(player_id: str, tech_id: str) -> int:
    """Get player's current tech level for a given tech ID."""
    upgrades = get_tech_upgrades(player_id)
    return upgrades.get(tech_id, 0)

async def list_techs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the list of available techs to upgrade."""
    pid = str(update.effective_user.id)
    markup = []
    lines = ["<b>🧪 Available Techs</b>\n"]

    for tech_id, info in TECH_TREE.items():
        level = get_player_tech_level(pid, tech_id)
        title = f"{info['title']} Lv {level}/{info['max_level']}"
        markup.append([InlineKeyboardButton(title, callback_data=f"TECH:{tech_id}")])
    
    await update.message.reply_text(
        "\nSelect a tech to view or upgrade.",
        reply_markup=InlineKeyboardMarkup(markup),
        parse_mode=ParseMode.HTML,
    )

async def tech_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display details and upgrade button for a specific tech."""
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    tech_id = query.data.split(":", 1)[1]

    data = TECH_TREE[tech_id]
    current_level = get_player_tech_level(pid, tech_id)
    next_level = current_level + 1

    if current_level >= data["max_level"]:
        return await query.edit_message_text(
            f"✅ {data['title']} is fully upgraded!\n\n"
            f"{data['desc']}",
            parse_mode=ParseMode.HTML
        )
    # Build upgrade details
    cost = calculate_tech_cost(tech_id, next_level)
    cost_str = " | ".join(f"{k.title()}: {v}" for k, v in cost.items())
    effect_desc = data["desc"]

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔼 Upgrade to Lv {next_level}", callback_data=f"UPGRADE_TECH:{tech_id}")],
        [InlineKeyboardButton("« Back to Tech List", callback_data="TECH_LIST")]
    ])

    await query.edit_message_text(
        f"<b>{data['title']}</b>\n"
        f"Level: {current_level}/{data['max_level']}\n"
        f"{effect_desc}\n\n"
        f"Cost: {cost_str}",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

async def tech_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to tech list."""
    query = update.callback_query
    await query.answer()
    context.args = []  # Clear arguments
    await list_techs(update, context)

async def upgrade_tech_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tech upgrade process."""
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    tech_id = query.data.split(":", 1)[1]
    data = TECH_TREE[tech_id]

    current_level = get_player_tech_level(pid, tech_id)
    next_level = current_level + 1

    if next_level > data["max_level"]:
        return await query.edit_message_text(
            f"⚠️ {data['title']} is already at max level.",
            parse_mode=ParseMode.HTML
        )

    cost = calculate_tech_cost(tech_id, next_level)
    resources = load_resources(pid)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            return await query.edit_message_text(
                f"❌ Not enough {res.title()} to upgrade {data['title']}.\n"
                f"Required: {amt} {res.title()}, You have: {resources.get(res, 0)}",
                parse_mode=ParseMode.HTML
            )

    # Deduct resources
    for res, amt in cost.items():
        resources[res] -= amt
    save_resources(pid, resources)

    # Save new tech level
    save_player_tech(pid, tech_id, next_level)

    await query.edit_message_text(
        f"✅ <b>{data['title']} upgraded to Level {next_level}!</b>",
        parse_mode=ParseMode.HTML
    )

# ── Registration for Handlers (to be used in main.py) ─────────────────────────

def register_tech_handlers(app):
    from telegram.ext import CommandHandler, CallbackQueryHandler

    app.add_handler(CommandHandler("tech", list_techs))
    app.add_handler(CallbackQueryHandler(show_tech_detail, pattern="^TECH_DETAIL:"))
    app.add_handler(CallbackQueryHandler(upgrade_tech_callback, pattern="^UPGRADE_TECH:"))
    app.add_handler(CallbackQueryHandler(tech_list_callback, pattern="^TECH_LIST$"))

