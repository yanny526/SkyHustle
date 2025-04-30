import json
import datetime

from utils import google_sheets
from utils.google_sheets import get_building_level
from utils.ui_helpers import render_status_panel

# Load unit stats
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)


def get_max_army_size(player_id: str) -> int:
    """
    Calculates max army size based on Command Center level.
    """
    lvl = get_building_level(player_id, "command_center") or 1
    return 1000 + lvl * 500


# ── Training ─────────────────────────────────────────────────────────────────
async def train_units(update, context):
    """
    /train [unit] [amount] — Queue units for training.
    """
    pid = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        return await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\n\n"
            + render_status_panel(pid)
        )

    unit = args[0].lower()
    try:
        amt = int(args[1])
        if amt <= 0:
            raise ValueError
    except ValueError:
        return await update.message.reply_text(
            "⚡ Amount must be a positive integer.\n\n"
            + render_status_panel(pid)
        )

    if unit not in UNIT_STATS:
        available = ", ".join(UNIT_STATS.keys())
        return await update.message.reply_text(
            f"❌ Invalid unit. Available: {available}\n\n"
            + render_status_panel(pid)
        )

    # Capacity check
    queue = google_sheets.load_training_queue(pid)
    in_train = sum(task["amount"] for task in queue.values())
    army = google_sheets.load_player_army(pid)
    total = sum(army.values())
    cap = get_max_army_size(pid)

    if total + in_train + amt > cap:
        return await update.message.reply_text(
            f"⚡ Not enough capacity! {total}/{cap} in use + {in_train} queued.\n\n"
            + render_status_panel(pid)
        )

    # Schedule training
    per_min = UNIT_STATS[unit]["training_time"]
    duration = datetime.timedelta(minutes=per_min * amt)
    end_time = datetime.datetime.now() + duration
    google_sheets.save_training_task(pid, unit, amt, end_time)

    await update.message.reply_text(
        f"🏭 Training {amt}× {UNIT_STATS[unit]['display_name']} "
        f"(ready in {per_min * amt}m)\n\n"
        + render_status_panel(pid)
    )


# ── View Army ────────────────────────────────────────────────────────────────
async def view_army(update, context):
    """
    /army — Display current army composition and stats.
    """
    pid = str(update.effective_user.id)
    army = google_sheets.load_player_army(pid)

    if not army:
        return await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to recruit.\n\n"
            + render_status_panel(pid)
        )

    lines = []
    atk = df = hp = 0
    for unit, count in army.items():
        stats = UNIT_STATS.get(unit, {})
        unit_atk = stats.get("attack", 0)
        unit_def = stats.get("defense", 0)
        unit_hp = stats.get("hp", 0)
        atk += unit_atk * count
        df += unit_def * count
        hp += unit_hp * count
        lines.append(
            f"🔹 {stats.get('display_name', unit.title())}: {count} "
            f"| Atk:{unit_atk * count} Def:{unit_def * count} HP:{unit_hp * count}"
        )

    total = sum(army.values())
    cap = get_max_army_size(pid)
    header = f"⚔️ SkyHustle Army — {total}/{cap} slots used"
    footer = f"Total Atk:{atk} Def:{df} HP:{hp}"

    msg = (
        f"{header}\n\n"
        + "\n".join(lines)
        + f"\n\n{footer}\n\n"
        + render_status_panel(pid)
    )
    await update.message.reply_text(msg)


# ── Training Status & Claim ─────────────────────────────────────────────────
async def training_status(update, context):
    """
    /trainstatus — Show queued training and time remaining.
    """
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)

    if not queue:
        return await update.message.reply_text(
            "🛡️ No units in training.\n\n" + render_status_panel(pid)
        )

    now = datetime.datetime.now()
    msgs = []
    for task in queue.values():
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = (end - now).total_seconds()
        name = task['unit_name'].title()
        qty = task['amount']
        if rem <= 0:
            msgs.append(f"✅ {qty}× {name} ready to claim!")
        else:
            m, s = divmod(int(rem), 60)
            msgs.append(f"⏳ {qty}× {name}: {m}m{s}s")

    await update.message.reply_text(
        "🛡️ Training Status:\n\n" + "\n".join(msgs)
        + "\n\n" + render_status_panel(pid)
    )


async def claim_training(update, context):
    """
    /claimtrain — Finalize completed training and add units.
    """
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    now = datetime.datetime.now()
    claimed = {}

    for task_id, task in list(queue.items()):
        end = datetime.datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            unit = task['unit_name']
            claimed[unit] = claimed.get(unit, 0) + task['amount']
            google_sheets.delete_training_task(task_id)

    if not claimed:
        return await update.message.reply_text(
            "⏳ Nothing ready yet.\n\n" + render_status_panel(pid)
        )

    army = google_sheets.load_player_army(pid)
    for unit, cnt in claimed.items():
        army[unit] = army.get(unit, 0) + cnt
    google_sheets.save_player_army(pid, army)

    lines = [f"🔹 {cnt}× {unit.title()}" for unit, cnt in claimed.items()]
    await update.message.reply_text(
        "🎉 Claimed Units:\n\n" + "\n".join(lines)
        + "\n\n" + render_status_panel(pid)
    )
