from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import utils.db as db

# Define unit costs
UNIT_COSTS = {
    "scout": {"gold": 100, "stone": 50, "iron": 30},
    "soldier": {"gold": 300, "stone": 150, "iron": 90},
    "tank": {"gold": 800, "stone": 400, "iron": 240},
    "drone": {"gold": 1500, "stone": 800, "iron": 500}
}

async def forge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forge (train) army units."""
    telegram_id = update.effective_user.id
    if len(context.args) != 2:
        return await update.message.reply_text("⚔️ Usage: /forge <unit> <amount>")

    unit_type = context.args[0].lower()
    try:
        amount = int(context.args[1])
    except ValueError:
        return await update.message.reply_text("⚔️ Please specify a valid amount!")

    if unit_type not in UNIT_COSTS:
        return await update.message.reply_text("⚔️ Invalid unit type! Available: scout, soldier, tank, drone")

    player_data = db.get_player_data(telegram_id)
    if not player_data:
        return await update.message.reply_text("⚔️ You must /start first!")

    # Calculate total cost
    cost = UNIT_COSTS[unit_type]
    total_gold = cost['gold'] * amount
    total_stone = cost['stone'] * amount
    total_iron = cost['iron'] * amount

    # Check resources
    if (player_data['Gold'] < total_gold or 
        player_data['Stone'] < total_stone or 
        player_data['Iron'] < total_iron):
        return await update.message.reply_text("⚔️ You don't have enough resources to forge this many units!")

    # Deduct resources
    db.update_player_resources(telegram_id, 
        gold_delta=-total_gold, 
        stone_delta=-total_stone, 
        iron_delta=-total_iron
    )

    # Update army
    if not db.get_army(telegram_id):
        db.create_army(telegram_id)

    if unit_type == "scout":
        db.update_army(telegram_id, scouts_delta=amount)
    elif unit_type == "soldier":
        db.update_army(telegram_id, soldiers_delta=amount)
    elif unit_type == "tank":
        db.update_army(telegram_id, tanks_delta=amount)
    elif unit_type == "drone":
        db.update_army(telegram_id, drones_delta=amount)

    await update.message.reply_text(f"⚔️ Successfully forged {amount} {unit_type}(s)!")

async def army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View your current army composition."""
    telegram_id = update.effective_user.id
    army_data = db.get_army(telegram_id)

    if not army_data:
        return await update.message.reply_text("🛡️ You have no army yet. Use /forge to create one!")

    text = (
        f"🛡️ Your Army:\n\n"
        f"👀 Scouts: {army_data['Scouts']}\n"
        f"🪖 Soldiers: {army_data['Soldiers']}\n"
        f"🛡️ Tanks: {army_data['Tanks']}\n"
        f"🛰️ Drones: {army_data['Drones']}"
    )
    await update.message.reply_text(text)
