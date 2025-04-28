import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# Load army unit stats from JSON config
with open("config/army_stats.json", "r") as file:
    UNIT_STATS = json.load(file)

# Max army size base settings (expand later based on Command Center level)
BASE_MAX_ARMY_SIZE = 1000

# Train units with a timer
async def train_units(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\nExample: /train soldier 50\n\n" +
            render_status_panel(player_id)
        )
        return

    unit_name = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("⚡ Amount must be a number.\n\n" + render_status_panel(player_id))
        return

    if unit_name not in UNIT_STATS:
        await update.message.reply_text(
            f"❌ Invalid unit. Available units: {', '.join(UNIT_STATS.keys())}\n\n" +
            render_status_panel(player_id)
        )
        return

    # Load current training queue and army
    training_queue = google_sheets.load_training_queue(player_id)
    total_in_training = sum(item['amount'] for item in training_queue.values())
    current_army = google_sheets.load_player_army(player_id)
    current_total = sum(current_army.values())

    # Capacity check
    if current_total + total_in_training + amount > BASE_MAX_ARMY_SIZE:
        await update.message.reply_text(
            f"⚡ Not enough army capacity!\n"
            f"Current Army: {current_total}/{BASE_MAX_ARMY_SIZE}\n"
            f"In Training: {total_in_training}\n"
            f"Trying to add: {amount}\n"
            f"Space Left: {BASE_MAX_ARMY_SIZE - (current_total + total_in_training)}\n\n" +
            render_status_panel(player_id)
        )
        return

    # Calculate training time
    per_unit_minutes = UNIT_STATS[unit_name]["training_time"]
    total_training_time = datetime.timedelta(minutes=per_unit_minutes * amount)
    end_time = datetime.datetime.now() + total_training_time

    # Save training task
    google_sheets.save_training_task(player_id, unit_name, amount, end_time)

    # Reply with confirmation + status panel
    msg = (
        f"🛡️ Training Started!\n\n"
        f"Units: {amount} {unit_name.capitalize()}\n"
        f"Ready In: {int(per_unit_minutes * amount)} minutes\n"
        f"Completion Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)

# View current army
async def view_army(update, context):
    player_id = str(update.effective_user.id)

    # Load army
    player_army = google_sheets.load_player_army(player_id)
    if not player_army:
        await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to build your forces.\n\n" +
            render_status_panel(player_id)
        )
        return

    # Build army list
    army_list = []
    total_power = 0
    total_defense = 0
    total_hp = 0
    for unit, count in player_army.items():
        stats = UNIT_STATS.get(unit, {})
        attack = stats.get("attack", 0) * count
        defense = stats.get("defense", 0) * count
        hp = stats.get("hp", 0) * count
        total_power += attack
        total_defense += defense
        total_hp += hp
        army_list.append(
            f"🔹 {unit.capitalize()}: {count} | Atk:{attack} Def:{defense} HP:{hp}"
        )

    # Respond with detailed army + status panel
    msg = (
        "⚔️ SkyHustle Army\n\n"
        + "\n".join(army_list)
        + f"\n\nTotal Army Size: {sum(player_army.values())}/{BASE_MAX_ARMY_SIZE}\n"
        + f"Total Attack Power: {total_power}\n"
        + f"Total Defense Power: {total_defense}\n"
        + f"Total HP: {total_hp}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)

# View training status
async def training_status(update, context):
    player_id = str(update.effective_user.id)
    training_queue = google_sheets.load_training_queue(player_id)

    if not training_queue:
        await update.message.reply_text(
            "🛡️ No units currently in training.\nUse /train to start training!\n\n"
            + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    status_messages = []
    for task_id, task in training_queue.items():
        end_time = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        remaining = end_time - now
        if remaining.total_seconds() <= 0:
            status = f"✅ {task['amount']} {task['unit_name'].capitalize()} ready to claim!"
        else:
            m, s = divmod(int(remaining.total_seconds()), 60)
            status = f"⏳ {task['amount']} {task['unit_name'].capitalize()} training: {m}m {s}s remaining."
        status_messages.append(status)

    msg = (
        "🛡️ Training Status:\n\n"
        + "\n".join(status_messages)
        + "\n\n" + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)

# Claim completed training
async def claim_training(update, context):
    player_id = str(update.effective_user.id)
    training_queue = google_sheets.load_training_queue(player_id)
    if not training_queue:
        await update.message.reply_text(
            "🛡️ No completed training to claim!\n\n" + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    claimed_units = {}
    for task_id, task in list(training_queue.items()):
        end_time = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end_time:
            claimed_units[task['unit_name']] = claimed_units.get(task['unit_name'], 0) + task['amount']
            google_sheets.delete_training_task(task_id)

    if not claimed_units:
        await update.message.reply_text(
            "⏳ Training still in progress. Please wait until completion.\n\n"
            + render_status_panel(player_id)
        )
        return

    # Update army
    current_army = google_sheets.load_player_army(player_id)
    for unit_name, amt in claimed_units.items():
        current_army[unit_name] = current_army.get(unit_name, 0) + amt
    google_sheets.save_player_army(player_id, current_army)

    # Build summary and append status
    claimed_list = [f"🔹 {amt} {unit_name.capitalize()}" for unit_name, amt in claimed_units.items()]
    msg = (
        "🎉 Training Complete! You have claimed:\n\n"
        + "\n".join(claimed_list)
        + "\n\n" + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)
