# army_system.py

import json
import datetime
from utils import google_sheets

# Load army unit stats from JSON config
with open("config/army_stats.json", "r") as file:
    UNIT_STATS = json.load(file)

# Max army size base settings (expand later based on Command Center level)
BASE_MAX_ARMY_SIZE = 1000

# Train units
async def train_units(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("🛡️ Usage: /train [unit] [amount]\nExample: /train soldier 50")
        return

    unit_name = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("⚡ Amount must be a number.")
        return

    if unit_name not in UNIT_STATS:
        await update.message.reply_text(f"❌ Invalid unit. Available units: {', '.join(UNIT_STATS.keys())}")
        return

    # Load player's current army
    player_army = google_sheets.load_player_army(player_id)

    # Calculate current army size
    current_total = sum(player_army.values())

    # Check if enough capacity
    if current_total + amount > BASE_MAX_ARMY_SIZE:
        await update.message.reply_text(
            f"⚡ Not enough army capacity!\n"
            f"Current: {current_total}/{BASE_MAX_ARMY_SIZE}\n"
            f"Trying to add: {amount}\n"
            f"Space Left: {BASE_MAX_ARMY_SIZE - current_total}"
        )
        return

    # Add units
    player_army[unit_name] = player_army.get(unit_name, 0) + amount

    # Save back to Google Sheets
    google_sheets.save_player_army(player_id, player_army)

    await update.message.reply_text(
        f"🛡️ Training Complete!\n\n"
        f"Trained {amount} {unit_name.capitalize()}(s).\n"
        f"New Army Size: {sum(player_army.values())}/{BASE_MAX_ARMY_SIZE}"
    )

# View army
async def view_army(update, context):
    player_id = str(update.effective_user.id)

    # Load army from Google Sheets
    player_army = google_sheets.load_player_army(player_id)

    if not player_army:
        await update.message.reply_text("🛡️ Your army is empty.\nUse /train to build your forces.")
        return

    army_list = []
    total_power = 0

    for unit, count in player_army.items():
        stats = UNIT_STATS.get(unit, {})
        unit_power = stats.get("attack", 0) * count
        total_power += unit_power
        army_list.append(f"🔹 {unit.capitalize()}: {count} units (Power: {unit_power})")

    await update.message.reply_text(
        "🛡️ Your Current Army:\n\n" +
        "\n".join(army_list) +
        f"\n\n⚡ Total Army Strength: {total_power} ⚡"
    )
