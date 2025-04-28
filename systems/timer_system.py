# army_system.py

import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# === Load Unit Stats ===
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

# === Army Capacity by Command Center Level ===
CAPACITY_BY_LEVEL = {
    1: 100,
    5: 300,
    10: 800,
    15: 2000,
}
DEFAULT_CAPACITY = 1000

def get_max_army_size(player_id: str) -> int:
    """
    Determine max army size based on player's Command Center level.
    """
    level = google_sheets.get_building_level(player_id, "command_center")
    # Find highest threshold <= level
    for lvl in sorted(CAPACITY_BY_LEVEL.keys(), reverse=True):
        if level >= lvl:
            return CAPACITY_BY_LEVEL[lvl]
    return DEFAULT_CAPACITY


# === Part 1: Train Units ===
async def train_units(update, context):
    player_id = str(update.effective_user.id)
    panel = render_status_panel(player_id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\nExample: /train soldier 50\n\n" + panel
        )
        return

    unit = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text(
            "⚡ Amount must be a number.\n\n" + panel
        )
        return

    if unit not in UNIT_STATS:
        await update.message.reply_text(
            f"❌ Invalid unit. Available: {', '.join(UNIT_STATS.keys())}\n\n" + panel
        )
        return

    # Capacity checks
    max_capacity = get_max_army_size(player_id)
    training_queue = google_sheets.load_training_queue(player_id)
    in_training = sum(item['amount'] for item in training_queue.values())
    army = google_sheets.load_player_army(player_id)
    current = sum(army.values())

    if current + in_training + amount > max_capacity:
        space_left = max_capacity - (current + in_training)
        await update.message.reply_text(
            f"⚡ Not enough capacity!\n"
            f"Current: {current}/{max_capacity}\n"
            f"In Training: {in_training}\n"
            f"Ordering: {amount}\n"
            f"Space Left: {space_left}\n\n" + panel
        )
        return

    # Schedule training
    per_unit = UNIT_STATS[unit]["training_time"]
    total_time = datetime.timedelta(minutes=per_unit * amount)
    ready_at = datetime.datetime.now() + total_time

    google_sheets.save_training_task(player_id, unit, amount, ready_at)

    msg = (
        f"🛡️ Training Started!\n\n"
        f"{amount}× {unit.capitalize()} (Time: {int(per_unit*amount)}m)\n"
        f"Ready at: {ready_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await update.message.reply_text(msg + "\n\n" + panel)


# === Part 2: View Army ===
async def view_army(update, context):
    player_id = str(update.effective_user.id)
    army = google_sheets.load_player_army(player_id)
    panel = render_status_panel(player_id)

    if not army:
        await update.message.reply_text(
            "🛡️ Your army is empty. Use /train to build forces.\n\n" + panel
        )
        return

    lines = []
    total_atk = total_def = total_hp = 0
    for unit, qty in army.items():
        stats = UNIT_STATS.get(unit, {})
        atk = stats.get("attack", 0) * qty
        de  = stats.get("defense", 0) * qty
        hp  = stats.get("hp", 0) * qty
        total_atk += atk
        total_def += de
        total_hp  += hp
        lines.append(f"🔹 {unit.capitalize()}: {qty} (Atk:{atk} Def:{de} HP:{hp})")

    summary = (
        "🛡️ Current Army:\n\n" +
        "\n".join(lines) +
        f"\n\n⚔️ Total Atk: {total_atk} | 🛡️ Def: {total_def} | ❤️ HP: {total_hp}"
    )
    await update.message.reply_text(summary + "\n\n" + panel)


# === Part 3: Training Status ===
async def training_status(update, context):
    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)
    panel = render_status_panel(player_id)

    if not queue:
        await update.message.reply_text(
            "🛡️ No units in training. Use /train to start.\n\n" + panel
        )
        return

    now = datetime.datetime.now()
    msgs = []
    for idx, task in queue.items():
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() <= 0:
            msgs.append(f"✅ {task['amount']}× {task['unit_name'].capitalize()} ready!")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            msgs.append(f"⏳ {task['amount']}× {task['unit_name'].capitalize()}: {m}m{s}s left")

    output = "🛡️ Training Status:\n\n" + "\n".join(msgs)
    await update.message.reply_text(output + "\n\n" + panel)


# === Part 4: Claim Training ===
async def claim_training(update, context):
    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)
    panel = render_status_panel(player_id)

    if not queue:
        await update.message.reply_text(
            "🛡️ Nothing to claim!\n\n" + panel
        )
        return

    now = datetime.datetime.now()
    claimed = {}
    for idx, task in list(queue.items()):
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[task['unit_name']] = claimed.get(task['unit_name'], 0) + task['amount']
            google_sheets.delete_training_task(idx)

    if not claimed:
        await update.message.reply_text(
            "⏳ Still training—nothing ready yet.\n\n" + panel
        )
        return

    army = google_sheets.load_player_army(player_id)
    for unit, amt in claimed.items():
        army[unit] = army.get(unit, 0) + amt
    google_sheets.save_player_army(player_id, army)

    lines = [f"🔹 {amt}× {unit.capitalize()}" for unit, amt in claimed.items()]
    msg = "🎉 Claimed units:" + "\n" + "\n".join(lines)
    await update.message.reply_text(msg + "\n\n" + panel)
