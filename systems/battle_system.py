# blackmarket_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    save_blackmarket_purchase,
)
from utils.ui_helpers import render_status_panel

# ── Static Black Market Items ──────────────────────────────────────────────
BLACK_MARKET_ITEMS = {
    "revive_all": {
        "name": "🧬 Full Revive Pack",
        "desc": "Revives all damaged units & buildings (excludes BM-only items).",
        "cost": 500,  # credits
        "type": "single_use",
    },
    "emp_device": {
        "name": "⚡ EMP Field Device",
        "desc": "Temporarily disables enemy defenses for 1h.",
        "cost": 300,
        "type": "single_use",
    },
    "infinity_scout": {
        "name": "🛰️ Infinity Scout Drone",
        "desc": "Reveals ALL enemy assets (including hidden ones).",
        "cost": 400,
        "type": "consumable",
    },
    "shield_boost": {
        "name": "🛡️ Advanced Shield",
        "desc": "Auto-blocks 1 incoming attack daily.",
        "cost": 250,
        "type": "passive_daily",
    },
    "hazmat_drone": {
        "name": "☣️ Hazmat Recon Drone",
        "desc": "Required to access radiation zones.",
        "cost": 350,
        "type": "unlock_zone",
    },
}

# ── View Available Black Market Items ───────────────────────────────────────
async def show_black_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    lines = ["<b>🛒 Black Market</b>", "Premium items available for Credits:\n"]
    buttons = []

    for key, item in BLACK_MARKET_ITEMS.items():
        lines.append(f"<b>{item['name']}</b>\n{item['desc']}\nCost: {item['cost']} Credits\n")
        buttons.append(
            [InlineKeyboardButton(f"Buy {item['name']}", callback_data=f"BMBUY:{key}")]
        )

    markup = InlineKeyboardMarkup(buttons)
    lines.append("\nUse /status to check your credits.")
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=markup
    )
# blackmarket_system.py (Part 2 of X)

# ── Handle Black Market Purchase ────────────────────────────────────────────
async def handle_blackmarket_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player_id = str(query.from_user.id)
    item_key = query.data.split(":", 1)[1]

    if item_key not in BLACK_MARKET_ITEMS:
        return await query.edit_message_text("❌ Invalid item.")

    item = BLACK_MARKET_ITEMS[item_key]
    resources = load_resources(player_id)
    credits = resources.get("credits", 0)

    if credits < item["cost"]:
        return await query.edit_message_text(
            f"❌ Not enough Credits to purchase {item['name']}.\nYou have {credits} Credits."
        )

    # Deduct credits and log the purchase
    resources["credits"] -= item["cost"]
    save_resources(player_id, resources)
    save_blackmarket_purchase(player_id, item_key, item["cost"])

    # Apply effect or confirm purchase
    effect_text = ""
    if item["type"] == "single_use":
        effect_text = "✅ Item will be used automatically when needed."
    elif item["type"] == "consumable":
        effect_text = "✅ You can now use this item manually."
    elif item["type"] == "passive_daily":
        effect_text = "✅ Passive benefit is now active daily."
    elif item["type"] == "unlock_zone":
        effect_text = "✅ You can now access radiation zones."

    await query.edit_message_text(
        f"🎉 Purchased: <b>{item['name']}</b>\n\n{item['desc']}\n\n{effect_text}",
        parse_mode=ParseMode.HTML
    )
# blackmarket_system.py (Part 3 of X)

# ── Admin Utility to Grant Items (Optional) ─────────────────────────────────
def admin_grant_item(player_id: str, item_key: str, quantity: int = 1):
    """
    Grants black market items to a player manually (for admin/dev testing).
    Could be extended to write to a custom sheet or inventory system.
    """
    for _ in range(quantity):
        save_blackmarket_purchase(player_id, item_key, 0)


# ── /bmbuy Command – Fallback purchase via command ──────────────────────────
async def bmbuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /bmbuy [item_id]\nUse /blackmarket to see items."
        )

    item_key = context.args[0]
    if item_key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    # Emulate same behavior as the callback version
    item = BLACK_MARKET_ITEMS[item_key]
    resources = load_resources(player_id)
    credits = resources.get("credits", 0)

    if credits < item["cost"]:
        return await update.message.reply_text(
            f"❌ Not enough Credits to purchase {item['name']}.\nYou have {credits} Credits."
        )

    # Deduct credits and log the purchase
    resources["credits"] -= item["cost"]
    save_resources(player_id, resources)
    save_blackmarket_purchase(player_id, item_key, item["cost"])

    await update.message.reply_text(
        f"✅ Purchased <b>{item['name']}</b> for {item['cost']} Credits.\n\n{item['desc']}",
        parse_mode=ParseMode.HTML
    )
# blackmarket_system.py (Part 4 of X)

# ── /use Item Command — Apply a consumable item ───────────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /use [item_id]")

    item_key = context.args[0]
    if item_key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    item = BLACK_MARKET_ITEMS[item_key]
    if not item.get("effect"):
        return await update.message.reply_text("❌ This item cannot be used directly.")

    # In real implementation: check player inventory and remove one instance
    # (We're not yet tracking quantity. This would need a new inventory sheet.)

    # Trigger the item's effect
    result = item["effect"](player_id)
    if result is not None:
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(f"✅ Used item: {item['name']}!")

# ── Utility: Check If Player Owns Item (future-proofed) ────────────────────────
def player_has_item(player_id: str, item_key: str) -> bool:
    """
    Stub for inventory tracking (currently unimplemented).
    Would check if player owns at least 1 of the item.
    """
    return True  # Placeholder for future inventory logic

# ── Cooldown / Perishables Framework Placeholder ───────────────────────────────
def apply_item_effect_with_rules(player_id: str, item_key: str) -> str:
    """
    Placeholder to manage perishable items, cooldowns, reusable effects, etc.
    Returns a user-facing message.
    """
    # Future logic for perishable items or one-use effect application
    return f"{BLACK_MARKET_ITEMS[item_key]['name']} used successfully."

# ── Register These in main.py ──────────────────────────────────────────────────
# From main.py:
# app.add_handler(CommandHandler("blackmarket", shop_system.blackmarket))
# app.add_handler(CallbackQueryHandler(shop_system.blackmarket_buy_callback, pattern="^BMBUY:"))
# app.add_handler(CommandHandler("bmbuy", shop_system.bmbuy_command))
# app.add_handler(CommandHandler("use", shop_system.use_item_command))
# blackmarket_system.py (Part 5 of X)

from utils.google_sheets import log_blackmarket_purchase

# ── Log Purchase for Auditing (Google Sheets) ───────────────────────────────────
def log_blackmarket_purchase(player_id: str, item_id: str, amount: int):
    """Saves purchase to the purchases worksheet."""
    from datetime import datetime
    try:
        from utils.google_sheets import purchases_ws
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        purchases_ws.append_row([player_id, item_id, amount, timestamp])
    except Exception as e:
        print(f"[ERROR] Logging Black Market purchase: {e}")

# ── Admin Utility: Give Player Item (For testing) ──────────────────────────────
async def give_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This would be admin-only in a real game
    player_id = str(update.effective_user.id)

    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /giveitem [player_id] [item_id]")

    target_id, item_key = context.args
    if item_key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    # Future: append to inventory system
    return await update.message.reply_text(f"✅ Gave item {item_key} to user {target_id} (not yet tracked).")

# ── Admin Utility: Wipe All Purchases (Optional) ───────────────────────────────
async def wipe_purchases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This would be admin-only
    try:
        from utils.google_sheets import purchases_ws
        purchases_ws.clear()
        purchases_ws.append_row(["player_id", "item_id", "amount", "timestamp"])
        await update.message.reply_text("✅ Purchase log wiped.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to wipe log: {e}")

# ── Register These in main.py as well ──────────────────────────────────────────
# app.add_handler(CommandHandler("giveitem", shop_system.give_item_command))
# app.add_handler(CommandHandler("wipepurchases", shop_system.wipe_purchases_command))
# blackmarket_system.py (Part 6 of X)

# ── Inventory System (In-Memory Only — Extend to Google Sheets Later) ───────────

# This is a simplified in-memory inventory for now.
# You will later save/load from Sheets.
player_inventories = {}

def add_to_inventory(player_id: str, item_key: str):
    if player_id not in player_inventories:
        player_inventories[player_id] = {}
    inventory = player_inventories[player_id]
    inventory[item_key] = inventory.get(item_key, 0) + 1

def use_item_from_inventory(player_id: str, item_key: str) -> bool:
    inventory = player_inventories.get(player_id, {})
    if inventory.get(item_key, 0) > 0:
        inventory[item_key] -= 1
        if inventory[item_key] == 0:
            del inventory[item_key]
        return True
    return False

def get_inventory(player_id: str) -> dict:
    return player_inventories.get(player_id, {})

# ── /inventory — Show Player Items ─────────────────────────────────────────────
async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    inventory = get_inventory(pid)

    if not inventory:
        return await update.message.reply_text("🎒 Your inventory is empty.")

    lines = [f"🎒 <b>Your Inventory</b>"]
    for key, qty in inventory.items():
        name = BLACK_MARKET_ITEMS[key]["name"]
        lines.append(f"• {name} ×{qty}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# ── /use [item_key] — Use an Item ──────────────────────────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /use [item_id]")

    key = context.args[0].lower()
    if key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    if not use_item_from_inventory(pid, key):
        return await update.message.reply_text("❌ You don't have this item.")

    # Apply item effect — just feedback for now
    await update.message.reply_text(f"✅ You used: {BLACK_MARKET_ITEMS[key]['name']}")

# ── Register These in main.py ──────────────────────────────────────────────────
# app.add_handler(CommandHandler("inventory", shop_system.inventory_command))
# app.add_handler(CommandHandler("use", shop_system.use_item_command))
# blackmarket_system.py (Part 7 of X)

import time

# ── Cooldown & Perishable Logic ───────────────────────────────────────────────

# In-memory cooldown tracking
item_cooldowns = {}  # Format: {player_id: {item_key: next_available_timestamp}}

# Items marked as perishable will be consumed after use
PERISHABLE_ITEMS = {"revive_all", "infinity_scout", "hazmat_drone", "emp_device"}

# Add cooldown to specific items (in seconds)
ITEM_COOLDOWN_SECONDS = {
    "emp_device": 3600,  # 1 hour cooldown
    "revive_all": 7200,  # 2 hours
}

def is_item_available(pid: str, item_key: str) -> bool:
    now = time.time()
    if pid not in item_cooldowns:
        return True
    next_time = item_cooldowns[pid].get(item_key, 0)
    return now >= next_time

def set_item_cooldown(pid: str, item_key: str):
    if pid not in item_cooldowns:
        item_cooldowns[pid] = {}
    item_cooldowns[pid][item_key] = time.time() + ITEM_COOLDOWN_SECONDS.get(item_key, 0)

# ── Updated use command with cooldowns & perishables ──────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /use [item_id]")

    key = context.args[0].lower()
    if key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    if not is_item_available(pid, key):
        remaining = int(item_cooldowns[pid][key] - time.time())
        mins = remaining // 60
        secs = remaining % 60
        return await update.message.reply_text(f"⏳ {BLACK_MARKET_ITEMS[key]['name']} is on cooldown ({mins}m {secs}s left).")

    # Apply item usage and deduct if perishable
    if not use_item_from_inventory(pid, key):
        return await update.message.reply_text("❌ You don't have this item.")

    # Apply effect (extend logic here)
    set_item_cooldown(pid, key) if key in ITEM_COOLDOWN_SECONDS else None

    return await update.message.reply_text(f"✅ Used {BLACK_MARKET_ITEMS[key]['name']}.")

# ── Admin Helper: Give Item (for dev use) ─────────────────────────────────────
async def give_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /giveitem [item_id]")

    key = context.args[0].lower()
    if key not in BLACK_MARKET_ITEMS:
        return await update.message.reply_text("❌ Invalid item ID.")

    add_to_inventory(pid, key)
    await update.message.reply_text(f"🧪 Given: {BLACK_MARKET_ITEMS[key]['name']}.")

# Register:
# app.add_handler(CommandHandler("giveitem", shop_system.give_item_command))

# blackmarket_system.py (Part 8 of X)

from utils.google_sheets import (
    load_inventory,
    save_inventory,
    load_item_cooldowns,
    save_item_cooldowns,
)

# ── Inventory Persistence ──────────────────────────────────────────────────────

def get_player_inventory(pid: str) -> dict:
    """
    Loads player's inventory as a dictionary {item_id: quantity}.
    """
    return load_inventory(pid)

def add_to_inventory(pid: str, item_id: str, amount: int = 1):
    inv = load_inventory(pid)
    inv[item_id] = inv.get(item_id, 0) + amount
    save_inventory(pid, inv)

def use_item_from_inventory(pid: str, item_id: str) -> bool:
    inv = load_inventory(pid)
    if inv.get(item_id, 0) > 0:
        inv[item_id] -= 1
        if inv[item_id] == 0:
            del inv[item_id]
        save_inventory(pid, inv)
        return True
    return False

# ── Cooldown Persistence ───────────────────────────────────────────────────────

def load_cooldowns(pid: str):
    global item_cooldowns
    item_cooldowns[pid] = load_item_cooldowns(pid)

def save_cooldowns(pid: str):
    global item_cooldowns
    save_item_cooldowns(pid, item_cooldowns.get(pid, {}))

# ── Middleware Init Hook (call once at login) ──────────────────────────────────

async def initialize_player_data(update: Update):
    """
    Loads inventory and cooldowns into memory for the player.
    Should be called early in player interaction.
    """
    pid = str(update.effective_user.id)
    load_cooldowns(pid)
    _ = load_inventory(pid)  # warm-up inventory for use/add functions
# blackmarket_system.py (Part 9 of X)

# ── Google Sheets Support Functions (add to google_sheets.py) ──────────────────

def load_inventory(player_id: str) -> dict:
    """Loads a player's inventory from the sheet."""
    try:
        recs = inventory_ws.get_all_records()
        return {
            row["item_id"]: int(row.get("quantity", 0))
            for row in recs
            if str(row.get("player_id")) == str(player_id)
        }
    except Exception as e:
        logger.exception("Error loading inventory:")
        return {}

def save_inventory(player_id: str, inventory: dict):
    """Saves the player's inventory to the sheet."""
    try:
        # Remove all rows for the player
        for cell in inventory_ws.findall(player_id):
            inventory_ws.delete_row(cell.row)
        # Add back updated inventory
        for item_id, qty in inventory.items():
            inventory_ws.append_row([player_id, item_id, qty])
    except Exception as e:
        logger.exception("Error saving inventory:")

def load_item_cooldowns(player_id: str) -> dict:
    """Returns {item_id: cooldown_end_timestamp}"""
    try:
        recs = cooldowns_ws.get_all_records()
        return {
            row["item_id"]: row["cooldown_end"]
            for row in recs
            if str(row.get("player_id")) == str(player_id)
        }
    except Exception as e:
        logger.exception("Error loading item cooldowns:")
        return {}

def save_item_cooldowns(player_id: str, cooldowns: dict):
    """Saves cooldowns for all items."""
    try:
        for cell in cooldowns_ws.findall(player_id):
            cooldowns_ws.delete_row(cell.row)
        for item_id, end in cooldowns.items():
            cooldowns_ws.append_row([player_id, item_id, end])
    except Exception as e:
        logger.exception("Error saving item cooldowns:")

# blackmarket_system.py (Part 10 of X)

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.google_sheets import load_inventory

# ── /inventory Command ──────────────────────────────────────────────────────────

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the player's current items and quantities."""
    player_id = str(update.effective_user.id)
    inv = load_inventory(player_id)

    if not inv:
        return await update.message.reply_text("🎒 Your inventory is empty.")

    lines = ["<b>🎒 Your Inventory:</b>"]
    for item_id, qty in inv.items():
        name = BLACK_MARKET_ITEMS[item_id]["name"]
        lines.append(f"• {name}: {qty}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
# blackmarket_system.py (Part 11 of X)

from utils.google_sheets import consume_item

# ── /use Command ────────────────────────────────────────────────────────────────

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args

    if not args:
        return await update.message.reply_text("Usage: /use [item_id]")

    item_id = args[0].lower()
    item = BLACK_MARKET_ITEMS.get(item_id)

    if not item:
        return await update.message.reply_text("❌ Invalid item ID.")

    inventory = load_inventory(player_id)
    if inventory.get(item_id, 0) <= 0:
        return await update.message.reply_text("❌ You don't have that item.")

    # Deduct item
    consume_item(player_id, item_id)

    # TODO: Apply the effect here based on item logic
    # e.g., revive buildings, reveal targets, boost mining, etc.
    # For now we send a placeholder success message

    await update.message.reply_text(
        f"✅ Used {item['name']}!\n\n(Effect logic coming soon...)"
    )
# blackmarket_system.py (Part 12 of X)

from telegram import KeyboardButton, ReplyKeyboardMarkup

STORE_ITEMS = {
    "boost_mine": {
        "name": "⛏️ Mine Booster",
        "desc": "Doubles mining output for 1 hour.",
        "cost": 500,
    },
    "boost_training": {
        "name": "🏋️‍♂️ Training Booster",
        "desc": "Halves training time for 1 hour.",
        "cost": 500,
    },
    "credit_pack": {
        "name": "💳 Credit Pack",
        "desc": "Gives 1000 Credits instantly.",
        "cost": 1000,
    },
}

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    lines = ["🛒 <b>Empire Store</b>\n"]

    for item_id, item in STORE_ITEMS.items():
        lines.append(
            f"• <b>{item['name']}</b>\n  {item['desc']}\n  Cost: {item['cost']} Credits\n  /buy {item_id}"
        )

    await update.message.reply_text(
        "\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP
    )
# blackmarket_system.py (Part 13 of X)

from utils.google_sheets import load_resources, save_resources

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        return await update.message.reply_text("Usage: /buy [item_id]")

    item_id = args[0].lower()
    item = STORE_ITEMS.get(item_id)
    if not item:
        return await update.message.reply_text("❌ Unknown item. Use /store to view available items.")

    resources = load_resources(player_id)
    credits = resources.get("credits", 0)
    if credits < item["cost"]:
        return await update.message.reply_text("❌ Not enough Credits.")

    # Deduct and apply effect
    resources["credits"] -= item["cost"]
    if item_id == "credit_pack":
        resources["credits"] += 1000
        await update.message.reply_text("✅ You received 1000 Credits!")
    elif item_id == "boost_mine":
        # Placeholder for applying mining boost logic
        await update.message.reply_text("✅ Mining output doubled for 1 hour!")
    elif item_id == "boost_training":
        # Placeholder for applying training boost logic
        await update.message.reply_text("✅ Training time halved for 1 hour!")

    save_resources(player_id, resources)

# blackmarket_system.py (Part 14 of X)

# ── Start of Black Market Items ────────────────────────────────────────────

BLACKMARKET_ITEMS = {
    "infinity_scout": {
        "name": "🛰️ Infinity Scout",
        "desc": "Scouts all enemy assets instantly. One-time use.",
        "cost": 500,
        "type": "one_time",
    },
    "revive_token": {
        "name": "💊 Revive Token",
        "desc": "Revives all damaged troops & buildings (excl. Black Market items).",
        "cost": 2000,
        "type": "one_time",
    },
    "hazmat_drone": {
        "name": "☣️ Hazmat Drone",
        "desc": "Allows access to Radiation Zones for mining rare materials.",
        "cost": 750,
        "type": "reusable",
    },
    "emp_device": {
        "name": "🔌 EMP Device",
        "desc": "Disables enemy defenses for 30 minutes.",
        "cost": 1000,
        "type": "one_time",
    },
    "advanced_shield": {
        "name": "🛡️ Advanced Shield",
        "desc": "Automatically blocks one attack per day.",
        "cost": 1500,
        "type": "reusable",
    },
}

def get_blackmarket_ui():
    buttons = []
    for item_id, item in BLACKMARKET_ITEMS.items():
        label = f"{item['name']} — {item['cost']} Credits"
        buttons.append([InlineKeyboardButton(label, callback_data=f"BMINFO:{item_id}")])
    return "🕶️ <b>Black Market</b>\nSelect an item to view details.", InlineKeyboardMarkup(buttons)
# blackmarket_system.py (Part 15 of X)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    load_blackmarket_items,
    save_blackmarket_item,
)

# ── Handle Item View Callback ──────────────────────────────────────────────

async def bm_item_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    item_id = query.data.split(":")[1]

    item = BLACKMARKET_ITEMS[item_id]
    owned = item_id in load_blackmarket_items(pid)
    desc = item["desc"]
    cost = item["cost"]
    type_text = "Reusable" if item["type"] == "reusable" else "One-time use"
    owned_text = "✅ Owned" if owned else "❌ Not owned"

    text = (
        f"<b>{item['name']}</b>\n"
        f"{desc}\n\n"
        f"<b>Cost:</b> {cost} Credits\n"
        f"<b>Type:</b> {type_text}\n"
        f"<b>Status:</b> {owned_text}"
    )

    buttons = [
        [InlineKeyboardButton("🛒 Purchase", callback_data=f"BMBUY:{item_id}")],
        [InlineKeyboardButton("« Back to Market", callback_data="BLACKMARKET")]
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
# blackmarket_system.py (Part 16 of X)

# ── Handle Purchase Logic ─────────────────────────────────────────────────────

async def bm_buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    item_id = query.data.split(":")[1]

    item = BLACKMARKET_ITEMS[item_id]
    credits_required = item["cost"]
    is_reusable = item["type"] == "reusable"

    resources = load_resources(pid)
    current_credits = resources.get("credits", 0)
    already_has = item_id in load_blackmarket_items(pid)

    if current_credits < credits_required:
        return await query.edit_message_text(
            f"❌ Not enough credits. You have {current_credits}, but need {credits_required}.",
            parse_mode=ParseMode.HTML,
        )

    if is_reusable and already_has:
        return await query.edit_message_text(
            "⚠️ You already own this reusable item.",
            parse_mode=ParseMode.HTML,
        )

    # Deduct credits and save item
    resources["credits"] -= credits_required
    save_resources(pid, resources)
    save_blackmarket_item(pid, item_id)

    await query.edit_message_text(
        f"✅ <b>{item['name']}</b> purchased successfully!\nYou now have {resources['credits']} credits remaining.",
        parse_mode=ParseMode.HTML
    )
# blackmarket_system.py (Part 17 of X)

from telegram.ext import CommandHandler, CallbackQueryHandler

# ── Telegram Handlers for Black Market ────────────────────────────────────────

def register_blackmarket_handlers(app):
    app.add_handler(CommandHandler("blackmarket", show_blackmarket))
    app.add_handler(CallbackQueryHandler(bm_buy_item, pattern="^BM_BUY:"))
the zip folders are not dioing justice can you correct the code in text
