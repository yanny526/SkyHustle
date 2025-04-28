import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# === Load Unit Stats & Capacities ===
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

CAPACITY_BY_LEVEL = {1:100, 5:300, 10:800, 15:2000}
DEFAULT_CAPACITY = 1000

def get_max_army_size(player_id: str) -> int:
    lvl = google_sheets.get_building_level(player_id, "command_center")
    for threshold in sorted(CAPACITY_BY_LEVEL.keys(), reverse=True):
        if lvl >= threshold:
            return CAPACITY_BY_LEVEL[threshold]
    return DEFAULT_CAPACITY

# === Part 1: Train Units ===
async def train_units(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    args = context.args or []

    if len(args) != 2:
        return await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\nExample: /train soldier 50\n\n" + panel
        )

    unit = args[0].lower()
    try:
        amount = int(args[1])
    except:
        return await update.message.reply_text("⚡ Amount must be a number.\n\n" + panel)

    if unit not in UNIT_STATS:
        return await update.message.reply_text(
            f"❌ Invalid unit. Available: {', '.join(UNIT_STATS)}\n\n" + panel
        )

    # 1) Capacity check
    max_cap = get_max_army_size(pid)
    queue = google_sheets.load_training_queue(pid)
    in_training = sum(t["amount"] for t in queue.values())
    army = google_sheets.load_player_army(pid)
    current = sum(army.values())

    if current + in_training + amount > max_cap:
        space = max_cap - (current + in_training)
        return await update.message.reply_text(
            f"⚡ Not enough capacity!\n"
            f"Current: {current}/{max_cap}\n"
            f"In Training: {in_training}\n"
            f"Ordering: {amount}\n"
            f"Space Left: {space}\n\n" + panel
        )

    # 2) Resource check & deduction
    cost_per = UNIT_STATS[unit].get("training_cost", {})
    resources = google_sheets.load_resources(pid)
    total_cost = {res: cost * amount for res, cost in cost_per.items()}

    for res, needed in total_cost.items():
        if resources.get(res, 0) < needed:
            return await update.message.reply_text(
                f"❌ Not enough {res}. Need {needed}, have {resources.get(res,0)}.\n\n" + panel
            )
    # Deduct now
    for res, needed in total_cost.items():
        resources[res] -= needed
    google_sheets.save_resources(pid, resources)

    # 3) Schedule training
    per_min = UNIT_STATS[unit]["training_time"]
    delta = datetime.timedelta(minutes=per_min * amount)
    ready_at = datetime.datetime.now() + delta
    google_sheets.save_training_task(pid, unit, amount, ready_at)

    await update.message.reply_text(
        f"🛡️ Training Started!\n\n"
        f"{amount}× {unit.capitalize()} (Time: {per_min*amount:.0f}m)\n"
        f"Ready at: {ready_at:%Y-%m-%d %H:%M:%S}\n\n" + render_status_panel(pid)
    )
# === Part 2: View Army ===
async def view_army(update, context):
    pid = str(update.effective_user.id)
    army = google_sheets.load_player_army(pid)
    panel = render_status_panel(pid)

    if not army:
        return await update.message.reply_text(
            "🛡️ Your army is empty. Use /train to build forces.\n\n" + panel
        )

    lines, atk, defe, hp = [], 0, 0, 0
    for unit, qty in army.items():
        stats = UNIT_STATS.get(unit, {})
        a = stats.get("attack",0) * qty
        d = stats.get("defense",0) * qty
        h = stats.get("hp",0) * qty
        atk += a; defe += d; hp += h
        lines.append(f"🔹 {unit.capitalize()}: {qty} (Atk:{a} Def:{d} HP:{h})")

    summary = (
        "🛡️ Current Army:\n\n"
        + "\n".join(lines)
        + f"\n\n⚔️ Total Atk: {atk} | 🛡️ Def: {defe} | ❤️ HP: {hp}"
    )
    await update.message.reply_text(summary + "\n\n" + panel)
# === Part 3: Training Status ===
async def training_status(update, context):
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    panel = render_status_panel(pid)

    if not queue:
        return await update.message.reply_text(
            "🛡️ No units in training. Use /train to start.\n\n" + panel
        )

    now = datetime.datetime.now()
    msgs = []
    for idx, task in queue.items():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
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
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    panel = render_status_panel(pid)

    if not queue:
        return await update.message.reply_text("🛡️ Nothing to claim!\n\n" + panel)

    now = datetime.datetime.now()
    claimed = {}
    for idx, task in list(queue.items()):
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[task["unit_name"]] = claimed.get(task["unit_name"], 0) + task["amount"]
            google_sheets.delete_training_task(idx)

    if not claimed:
        return await update.message.reply_text(
            "⏳ Still training—nothing ready yet.\n\n" + panel
        )

    army = google_sheets.load_player_army(pid)
    for unit, amt in claimed.items():
        army[unit] = army.get(unit, 0) + amt
    google_sheets.save_player_army(pid, army)

    lines = [f"🔹 {amt}× {unit.capitalize()}" for unit, amt in claimed.items()]
    msg = "🎉 Claimed units:\n\n" + "\n".join(lines)
    await update.message.reply_text(msg + "\n\n" + panel)
