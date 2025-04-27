# handlers/economy.py

from telegram import Update
from telegram.ext import ContextTypes
import json
import utils.db as db

# Load normal store items
def load_store_items():
    with open("data/items.json", "r") as f:
        data = json.load(f)
    return data["store_items"]

# Load blackmarket items
def load_blackmarket_items():
    with open("data/items.json", "r") as f:
        data = json.load(f)
    return data["blackmarket_items"]

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_items = load_store_items()
    text = "✨ **SkyHustle General Store** ✨\n\n"
    for item in store_items:
        if "gold" in item["id"]:
            emoji = "💰"  # Gold bag
        elif "stone" in item["id"]:
            emoji = "🪨"  # Gear / mining
        elif "iron" in item["id"]:
            emoji = "🛠️"  # Gear / mining
        elif "energy" in item["id"]:
            emoji = "⚡"  # Lightning
        elif "shield" in item["id"]:
            emoji = "🛡️"  # Shield
        else:
            emoji = "🏦"  # Store icon

        text += f"{emoji} `{item['id']}` | {item['name']} — {item['price']} Gold\n"

    text += "\n✨ To buy an item, type `/buy <item_id>`!"
    await update.message.reply_text(text)

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blackmarket_items = load_blackmarket_items()
    text = "🧙‍♂️ **SkyHustle Black Market** 🧙‍♂️\n\n"
    for item in blackmarket_items:
        if "scout" in item["id"]:
            emoji = "🚀"  # Rocket (spy drone)
        elif "hazmat" in item["id"]:
            emoji = "☣️"  # Biohazard
        elif "emp" in item["id"]:
            emoji = "🔌"  # Electric plug
        elif "revive" in item["id"]:
            emoji = "⚖️"  # Scales (revival)
        else:
            emoji = "🕵️‍♂️"  # Detective

        text += f"{emoji} `{item['id']}` | {item['name']} — {item['price']} Gold\n"

    text += "\n🌏 To buy a black market item, type `/blackbuy <item_id>`!"
    await update.message.reply_text(text)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("💼 Usage: /buy <item_id>")

    item_id = context.args[0].lower()
    store_items = load_store_items()

    selected_item = next((item for item in store_items if item["id"].lower() == item_id), None)

    if not selected_item:
        return await update.message.reply_text("🕵️‍♂️ Item not found in store!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("💸 Not enough Gold!")

    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])

    if selected_item.get("gold") or selected_item.get("stone") or selected_item.get("iron") or selected_item.get("energy"):
        db.update_player_resources(
            telegram_id,
            gold_delta=selected_item.get("gold", 0),
            stone_delta=selected_item.get("stone", 0),
            iron_delta=selected_item.get("iron", 0),
            energy_delta=selected_item.get("energy", 0)
        )
        await update.message.reply_text(f"✅ You bought {selected_item['name']}!")
    else:
        db.add_to_inventory(telegram_id, selected_item['id'])
        await update.message.reply_text(f"📦 {selected_item['name']} added to your inventory!")

async def blackbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if len(context.args) != 1:
        return await update.message.reply_text("🤖 Usage: /blackbuy <item_id>")

    item_id = context.args[0].lower()
    black_items = load_blackmarket_items()

    selected_item = next((item for item in black_items if item["id"].lower() == item_id), None)

    if not selected_item:
        return await update.message.reply_text("🕵️‍♂️ Item not found in Black Market!")

    player = db.get_player_data(telegram_id)
    if player["Gold"] < selected_item["price"]:
        return await update.message.reply_text("💸 Not enough Gold!")

    db.update_player_resources(telegram_id, gold_delta=-selected_item["price"])
    db.add_to_inventory(telegram_id, selected_item['id'])

    await update.message.reply_text(f"🧙‍♂️ {selected_item['name']} purchased secretly! It's now in your inventory. 🚫")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if len(context.args) != 1:
        return await update.message.reply_text("🎯 Usage: /use <item_id>")

    item_id = context.args[0].lower()

    if not db.has_item(telegram_id, item_id):
        return await update.message.reply_text("❌ You don't own this item!")

    if item_id == "basicshield":
        player = db.get_player_data(telegram_id)
        if player["ShieldActive"] == "Yes":
            return await update.message.reply_text("🛡️ You already have a shield active!")
        db.player_profile.update_cell(db.find_player(telegram_id), 9, "Yes")
        await update.message.reply_text("\ud83d\udee1\ufe0f Basic Shield activated! You're protected for 24 hours.")

    elif item_id == "revivekit":
        await update.message.reply_text("\ud83d\udd27 Revive Kit used! (Troop revive feature coming soon...)")

    elif item_id == "infinityscout":
        await update.message.reply_text("\ud83d\ude80 Infinity Scout launched! (Spying system coming soon...)")

    elif item_id == "hazmatdrone":
        await update.message.reply_text("\u2623\ufe0f Hazmat Drone deployed! (Radiation zones coming soon...)")

    elif item_id == "empdevice":
        await update.message.reply_text("\ud83d\udd0c EMP Device activated! (Enemy shields disruption coming soon...)")

    else:
        return await update.message.reply_text("\u2753 Unknown item or feature not available yet!")

    db.remove_from_inventory(telegram_id, item_id)  # Consume item
