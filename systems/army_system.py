# systems/army_system.py

import json
import datetime
from utils import google_sheets

# Load army unit stats from JSON config
with open("config/army_stats.json", "r") as file:
    UNIT_STATS = json.load(file)

# Base army capacity (you can later expand this based on Command Center level)
BASE_MAX_ARMY_SIZE = 1000

def get_max_army_size(player_id: str) -> int:
    """
    Determine max army size for a player.
    Currently returns a constant, but you can extend this to read
    the player's Command Center level from Google Sheets.
    """
    # e.g. level = google_sheets.get_building_level(player_id, "command_center")
    return BASE_MAX_ARMY_SIZE


# -------------- Train Units (/train) --------------
async def train_units(update, context):
    from utils.ui_helpers import render_status_panel

    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\nExample: /train soldier 50\n\n"
            + render_status_panel(player_id)
        )
        return

    unit_name = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text(
            "⚡ Amount must be a number.\n\n" + render_status_panel(player_id)
        )
        return

    if unit_name not in UNIT_STATS:
        await update.message.reply_text(
            f"❌ Invalid unit. Available units: {', '.join(UNIT_STATS.keys())}\n\n"
            + render_status_panel(player_id)
        )
        return

    # Load current training queue and army
    training_queue = google_sheets.load_training_queue(player_id)
    in_training = sum(item["amount"] for item in training_queue.values())
    army = google_sheets.load_player_army(player_id)
    current_total = sum(army.values())

    max_cap = get_max_army_size(player_id)
    if current_total + in_training + amount > max_cap:
        await update.message.reply_text(
            f"⚡ Not enough army capacity!\n"
            f"Current Army: {current_total}/{max_cap}\n"
            f"In Training: {in_training}\n"
            f"Ordering: {amount}\n"
            f"Space Left: {max_cap - (current_total + in_training)}\n\n"
            + render_status_panel(player_id)
        )
        return

    # Calculate training time
    per_unit = UNIT_STATS[unit_name]["training_time"]
    total_time = datetime.timedelta(minutes=per_unit * amount)
    ready_at = datetime.datetime.now() + total_time

    # Save training task
    google_sheets.save_training_task(player_id, unit_name, amount, ready_at)

    msg = (
        f"🛡️ Training Started!\n\n"
        f"{amount}× {unit_name.capitalize()} — ready in {int(per_unit*amount)}m\n"
        f"({ready_at.strftime('%Y-%m-%d %H:%M:%S')})\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


# -------------- View Army (/army) --------------
async def view_army(update, context):
    from utils.ui_helpers import render_status_panel

    player_id = str(update.effective_user.id)
    army = google_sheets.load_player_army(player_id)

    if not army:
        await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to build your forces.\n\n"
            + render_status_panel(player_id)
        )
        return

    army_lines = []
    total_atk = total_def = total_hp = 0
    for unit, qty in army.items():
        stats = UNIT_STATS.get(unit, {})
        atk = stats.get("attack", 0) * qty
        defe = stats.get("defense", 0) * qty
        hp  = stats.get("hp", 0) * qty
        total_atk += atk
        total_def += defe
        total_hp  += hp
        army_lines.append(
            f"🔹 {unit.capitalize()}: {qty} | Atk:{atk} Def:{defe} HP:{hp}"
        )

    max_cap = get_max_army_size(player_id)
    msg = (
        "⚔️ SkyHustle Army\n\n"
        + "\n".join(army_lines)
        + f"\n\nTotal Army Size: {sum(army.values())}/{max_cap}\n"
        + f"Total Attack Power: {total_atk}\n"
        + f"Total Defense Power: {total_def}\n"
        + f"Total HP: {total_hp}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


# -------------- Training Status (/trainstatus) --------------
async def training_status(update, context):
    from utils.ui_helpers import render_status_panel

    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)

    if not queue:
        await update.message.reply_text(
            "🛡️ No units currently in training.\nUse /train to start training!\n\n"
            + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    msgs = []
    for task in queue.values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() <= 0:
            msgs.append(f"✅ {task['amount']} {task['unit_name'].capitalize()} ready to claim!")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            msgs.append(
                f"⏳ {task['amount']} {task['unit_name'].capitalize()}: {m}m{s}s remaining."
            )

    msg = (
        "🛡️ Training Status:\n\n"
        + "\n".join(msgs)
        + "\n\n" + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


# -------------- Claim Training (/claimtrain) --------------
async def claim_training(update, context):
    from utils.ui_helpers import render_status_panel

    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)
    if not queue:
        await update.message.reply_text(
            "🛡️ No completed training to claim!\n\n" + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    claimed = {}
    for task_id, task in list(queue.items()):
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            unit = task["unit_name"]
            claimed[unit] = claimed.get(unit, 0) + task["amount"]
            google_sheets.delete_training_task(task_id)

    if not claimed:
        await update.message.reply_text(
            "⏳ Training still in progress. Please wait until completion.\n\n"
            + render_status_panel(player_id)
        )
        return

    # Save to army
    army = google_sheets.load_player_army(player_id)
    for unit, amt in claimed.items():
        army[unit] = army.get(unit, 0) + amt
    google_sheets.save_player_army(player_id, army)

    claimed_lines = [f"🔹 {amt}× {unit.capitalize()}" for unit, amt in claimed.items()]
    msg = (
        "🎉 Training Complete! You have claimed:\n\n"
        + "\n".join(claimed_lines)
        + "\n\n" + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)
