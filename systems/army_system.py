import json
import datetime

from utils import google_sheets
from utils.google_sheets import get_building_level
from utils.ui_helpers import render_status_panel


# Load unit stats
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)


# ── Dynamic Army Cap ─────────────────────────────────────────────────────────
def get_max_army_size(player_id: str) -> int:
    """
    Calculates the maximum army size based on the level of the Command Center.
    Defaults to a base capacity if the Command Center hasn't been built.
    """
    lvl = get_building_level(player_id, "command_center") or 1
    return 1000 + lvl * 500


# ── Training ─────────────────────────────────────────────────────────────────
async def train_units(update, context):
    """
    Handles the /train command, allowing players to queue units for training.
    """
    pid = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        return await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\n\n" + render_status_panel(pid)
        )

    unit = args[0].lower()
    try:
        amt = int(args[1])
        if amt <= 0:
            return await update.message.reply_text(
                "⚡ Amount must be a positive number.\n\n" + render_status_panel(pid)
            )
    except ValueError:
        return await update.message.reply_text(
            "⚡ Amount must be a valid number.\n\n" + render_status_panel(pid)
        )

    if unit not in UNIT_STATS:
        available_units = ", ".join(UNIT_STATS.keys())
        return await update.message.reply_text(
            f"❌ Invalid unit. Available: {available_units}\n\n"
            + render_status_panel(pid)
        )

    # Capacity check
    queue = google_sheets.load_training_queue(pid)
    in_train = sum(t["amount"] for t in queue.values())
    army = google_sheets.load_player_army(pid)
    total = sum(army.values())
    cap = get_max_army_size(pid)

    if total + in_train + amt > cap:
        return await update.message.reply_text(
            f"⚡ Not enough capacity! {total}/{cap} army size, {in_train} in training.\n\n"
            + render_status_panel(pid)
        )

    # Schedule training
    per_min = UNIT_STATS[unit]["training_time"]
    dur = datetime.timedelta(minutes=per_min * amt)
    end = datetime.datetime.now() + dur
    google_sheets.save_training_task(pid, unit, amt, end)

    await update.message.reply_text(
        f"🏭 Training {amt}× {unit.title()} (ready in {per_min * amt}m)\n\n"
        + render_status_panel(pid)
    )


# ── View Army ────────────────────────────────────────────────────────────────
async def view_army(update, context):
    """
    Displays the player's current army composition and overall stats.
    """
    pid = str(update.effective_user.id)
    army = google_sheets.load_player_army(pid)

    if not army:
        return await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to recruit.\n\n"
            + render_status_panel(pid)
        )

    lines = []
    atk = defp = hp = 0

    for u, cnt in army.items():
        stats = UNIT_STATS.get(u, {})
        if not stats:
            # Defensive check for missing unit data
            print(f"Warning: Unit stats not found for '{u}'")
            continue

        unit_atk = stats.get("attack", 0)
        unit_def = stats.get("defense", 0)
        unit_hp = stats.get("hp", 0)

        atk += unit_atk * cnt
        defp += unit_def * cnt
        hp += unit_hp * cnt

        lines.append(
            f"🔹 {u.title()}: {cnt} | Atk:{unit_atk * cnt} Def:{unit_def * cnt} Hp:{unit_hp * cnt}"
        )

    lines.append(f"\nTotal: Atk={atk} Def={defp} Hp={hp}")
    await update.message.reply_text(
        "🛡️ Your Army:\n\n" + "\n".join(lines) + "\n\n" + render_status_panel(pid)
    )


# ── Training Status ──────────────────────────────────────────────────────────
async def training_status(update, context):
    """
    Displays the player's current training queue with remaining times.
    """
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)

    if not queue:
        return await update.message.reply_text(
            "🏭 No units currently training.\n\n" + render_status_panel(pid)
        )

    now = datetime.datetime.now()
    msgs = []

    for idx, t in queue.items():
        end = datetime.datetime.strptime(t["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() <= 0:
            msgs.append(f"✅ {t['amount']} {t['unit_name'].title()} ready to claim!")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            msgs.append(f"⏳ {t['amount']} {t['unit_name'].title()}: {m}m{s}s")

    await update.message.reply_text(
        "🛡️ Training Status:\n\n"
        + "\n".join(msgs)
        + "\n\n"
        + render_status_panel(pid)
    )


# ── Claim Training ───────────────────────────────────────────────────────────
async def claim_training(update, context):
    """
    Finalizes training for completed units and adds them to the player's army.
    """
    pid = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    now = datetime.datetime.now()
    claimed = {}

    # Collect ready units and delete their tasks
    for idx, t in list(queue.items()):
        end = datetime.datetime.strptime(t["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[t["unit_name"]] = claimed.get(t["unit_name"], 0) + t["amount"]
            google_sheets.delete_training_task(idx)

    if not claimed:
        return await update.message.reply_text(
            "⏳ Nothing ready yet.\n\n" + render_status_panel(pid)
        )

    # Add claimed units to the army
    army = google_sheets.load_player_army(pid)
    for unit, count in claimed.items():
        army[unit] = army.get(unit, 0) + count
    google_sheets.save_player_army(pid, army)

    msg = "\n".join(f"✅ {count} {unit.title()}" for unit, count in claimed.items())
    await update.message.reply_text(
        "Units claimed:\n" + msg + "\n\n" + render_status_panel(pid)
    )
