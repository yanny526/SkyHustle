# store_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import save_resources, load_resources
from utils.ui_helpers import render_status_panel

STORE_ITEMS = {
    "metal_pack": {
        "name": "Metal Pack",
        "desc": "Gain 1000 Metal instantly.",
        "cost": {"credits": 100},
        "reward": {"metal": 1000}
    },
    "fuel_pack": {
        "name": "Fuel Pack",
        "desc": "Gain 500 Fuel instantly.",
        "cost": {"credits": 80},
        "reward": {"fuel": 500}
    },
    "crystal_pack": {
        "name": "Crystal Pack",
        "desc": "Gain 200 Crystal instantly.",
        "cost": {"credits": 120},
        "reward": {"crystal": 200}
    },
    "combo_pack": {
        "name": "Combo Pack",
        "desc": "Get a mix of all basic resources.",
        "cost": {"credits": 250},
        "reward": {"metal": 500, "fuel": 250, "crystal": 100}
    },
}

def _make_store_markup():
    buttons = []
    for key, item in STORE_ITEMS.items():
        label = f"{item['name']} — {item['cost']['credits']}💳"
        buttons.append([InlineKeyboardButton(label, callback_data=f"STORE_BUY:{key}")])
    return InlineKeyboardMarkup(buttons)
# store_system.py (Part 2 of X)

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the store UI."""
    player_id = str(update.effective_user.id)
    text = (
        "🛒 <b>Resource Store</b>\n"
        "Spend credits to get resources instantly.\n\n"
        "Tap a pack below to purchase:"
    )
    markup = _make_store_markup()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles store purchase interactions."""
    query = update.callback_query
    await query.answer()
    player_id = str(query.from_user.id)

    key = query.data.split(":", 1)[1]
    if key not in STORE_ITEMS:
        return await query.edit_message_text("❌ Invalid item selected.")

    item = STORE_ITEMS[key]
    user_resources = load_resources(player_id)
    price = item["cost"]

    # Check for enough credits
    for res, amt in price.items():
        if user_resources.get(res, 0) < amt:
            return await query.edit_message_text(
                f"❌ Not enough {res.title()} to buy {item['name']}."
            )

    # Deduct cost
    for res, amt in price.items():
        user_resources[res] -= amt

    # Add rewards
    for res, amt in item["reward"].items():
        user_resources[res] = user_resources.get(res, 0) + amt

    save_resources(player_id, user_resources)

    await query.edit_message_text(
        f"✅ Purchased <b>{item['name']}</b>!\n\n" + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )
# store_system.py (Part 3 of X)

# ── Black Market Items ─────────────────────────────────────────────────────────
BLACKMARKET = {
    "scout_drone": {
        "name": "Infinity Scout Drone",
        "desc": "🔍 One-time scout that reveals ALL enemy assets.",
        "cost": {"credits": 500},
        "type": "perishable",
    },
    "revive_kit": {
        "name": "Universal Revive Kit",
        "desc": "⚕️ Revives all damaged troops and buildings (except premium items).",
        "cost": {"credits": 1000},
        "type": "consumable",
    },
    "hazmat_drone": {
        "name": "Hazmat Recon Drone",
        "desc": "☢️ Allows scans into Radiation Zones.",
        "cost": {"credits": 700},
        "type": "perishable",
    },
    "emp_device": {
        "name": "EMP Field Device",
        "desc": "💥 Disables opponent defenses for 5 minutes.",
        "cost": {"credits": 800},
        "type": "perishable",
    },
    "advanced_shield": {
        "name": "Advanced Shield",
        "desc": "🛡️ Auto-blocks the first attack every 24h.",
        "cost": {"credits": 1200},
        "type": "reusable",
    },
}

def _make_blackmarket_markup():
    buttons = []
    for key, item in BLACKMARKET.items():
        label = f"{item['name']} ({item['cost']['credits']}💳)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"BMBUY:{key}")])
    return InlineKeyboardMarkup(buttons)

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the Black Market UI."""
    text = (
        "🕵️ <b>Black Market</b>\n"
        "Rare & powerful items. Some are one-time use.\n\n"
        "Tap below to purchase:"
    )
    markup = _make_blackmarket_markup()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
# store_system.py (Part 4 of X)

from utils.google_sheets import save_player_purchase

async def bmbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles a Black Market item purchase."""
    pid = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /bmbuy [item_id]")

    item_id = context.args[0].lower()
    item = BLACKMARKET.get(item_id)
    if not item:
        return await update.message.reply_text("❌ Invalid item ID.")

    credits = load_resources(pid).get("credits", 0)
    price = item["cost"]["credits"]
    if credits < price:
        return await update.message.reply_text("❌ Not enough credits.")

    # Deduct credits
    resources = load_resources(pid)
    resources["credits"] -= price
    save_resources(pid, resources)

    # Log purchase
    save_player_purchase(pid, item_id, price)

    await update.message.reply_text(
        f"✅ Purchased <b>{item['name']}</b>!\n{item['desc']}",
        parse_mode=ParseMode.HTML,
    )
