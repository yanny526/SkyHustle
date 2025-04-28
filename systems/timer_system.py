import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# Load army unit stats from JSON config
with open("config/army_stats.json", "r") as file:
    UNIT_STATS = json.load(file)

# Max army size base settings (expand later based on Command Center level)
BASE_MAX_ARMY_SIZE = 1000

async def train_units(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\n"
            "Example: /train soldier 50\n\n"
            + render_status_panel(player_id)
        )
        return

    unit_name = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text(
            "⚡ Amount must be a number.\n\n"
            + render_status_panel(player_id)
        )
        return

    if unit_name not in UNIT_STATS:
        await update.message.reply_text(
            f"❌ Invalid unit. Available: {', '.join(UNIT_STATS.keys())}\n\n"
            + render_status_panel(player_id)
        )
        return

    # Load current training queue and army
    training_queue = google_sheets.load_training_queue(player_id)
    total_in_training = sum(item['amount'] for item in training_queue.values())
    current_army = google_sheets.load_player_army(player_id)
    current_total = sum(current_army.values())

    if current_total + total_in_training + amount > BASE_MAX_ARMY_SIZE:
        await update.message.reply_text(
            f"⚡ Not enough capacity!\n"
            f"Current Army: {current_total}/{BASE_MAX_ARMY_SIZE}\n"
            f"In Training: {total_in_training}\n"
            f"Ordering: {amount}\n"
            f"Space Left: {BASE_MAX_ARMY_SIZE - (current_total + total_in_training)}\n\n"
            + render_status_panel(player_id)
        )
        return

    # Calculate training time
    per_min = UNIT_STATS[unit_name]["training_time"]
    total_time = datetime.timedelta(minutes=per_min * amount)
    ready_at = datetime.datetime.now() + total_time

    # Save to Google Sheets
    google_sheets.save_training_task(player_id, unit_name, amount, ready_at)

    await update.message.reply_text(
        f"🛡️ Training Started!\n\n"
        f"{amount}× {unit_name.capitalize()} — ready in {int(per_min*amount)}m\n"
        f"({ready_at.strftime('%Y-%m-%d %H:%M:%S')})\n\n"
        + render_status_panel(player_id)
    )
async def view_army(update, context):
    player_id = str(update.effective_user.id)
    player_army = google_sheets.load_player_army(player_id)

    if not player_army:
        await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to build forces.\n\n"
            + render_status_panel(player_id)
        )
        return

    lines = []
    atk, defe, hp = 0, 0, 0

    for unit, qty in player_army.items():
        stats = UNIT_STATS.get(unit, {})
        a, d, h = stats.get("attack",0), stats.get("defense",0), stats.get("hp",0)
        lines.append(f"🔹 {unit.capitalize()}: {qty} units (Atk:{a*qty} Def:{d*qty} HP:{h*qty})")
        atk += a*qty; defe += d*qty; hp += h*qty

    summary = (
        "🛡️ Your Army:\n\n" +
        "\n".join(lines) +
        f"\n\n⚔️ Total Atk: {atk} | 🛡️ Def: {defe} | ❤️ HP: {hp}"
    )
    await update.message.reply_text(summary + "\n\n" + render_status_panel(player_id))
async def training_status(update, context):
    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)

    if not queue:
        await update.message.reply_text(
            "🛡️ No units in training.\nUse /train to start.\n\n"
            + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    msgs = []
    for row_idx, task in queue.items():
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() <= 0:
            msgs.append(f"✅ {task['amount']}× {task['unit_name'].capitalize()} ready!")
        else:
            m, s = divmod(int(rem.total_seconds()),60)
            msgs.append(f"⏳ {task['amount']}× {task['unit_name'].capitalize()}: {m}m{s}s left")

    output = "🛡️ Training Status:\n\n" + "\n".join(msgs)
    await update.message.reply_text(output + "\n\n" + render_status_panel(player_id))
async def claim_training(update, context):
    player_id = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(player_id)

    if not queue:
        await update.message.reply_text(
            "🛡️ Nothing to claim!\n\n" + render_status_panel(player_id)
        )
        return

    now = datetime.datetime.now()
    claimed = {}
    for row_idx, task in list(queue.items()):
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[task['unit_name']] = claimed.get(task['unit_name'],0) + task['amount']
            google_sheets.delete_training_task(row_idx)

    if not claimed:
        await update.message.reply_text(
            "⏳ Still training—nothing ready yet.\n\n"
            + render_status_panel(player_id)
        )
        return

    # Add to army
    army = google_sheets.load_player_army(player_id)
    for unit, amt in claimed.items():
        army[unit] = army.get(unit,0) + amt
    google_sheets.save_player_army(player_id, army)

    lines = [f"🔹 {amt}× {unit.capitalize()}" for unit,amt in claimed.items()]
    msg = "🎉 Claimed:\n\n" + "\n".join(lines)
    await update.message.reply_text(msg + "\n\n" + render_status_panel(player_id))
