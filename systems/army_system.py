import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel
from utils.google_sheets import get_building_level

# Load unit stats
with open("config/army_stats.json", "r") as f:
    UNIT_STATS = json.load(f)

# ── Dynamic Army Cap ─────────────────────────────────────────────────────────
def get_max_army_size(player_id: str) -> int:
    lvl = get_building_level(player_id, "command_center") or 1
    return 1000 + lvl * 500

# ── Training ─────────────────────────────────────────────────────────────────
async def train_units(update, context):
    pid   = str(update.effective_user.id)
    args  = context.args
    if len(args) != 2:
        return await update.message.reply_text(
            "🛡️ Usage: /train [unit] [amount]\n\n" +
            render_status_panel(pid)
        )
    unit = args[0].lower()
    try:
        amt = int(args[1])
    except:
        return await update.message.reply_text(
            "⚡ Amount must be a number.\n\n" + render_status_panel(pid)
        )
    if unit not in UNIT_STATS:
        return await update.message.reply_text(
            f"❌ Invalid unit. Available: {', '.join(UNIT_STATS)}\n\n" +
            render_status_panel(pid)
        )

    # capacity check
    queue = google_sheets.load_training_queue(pid)
    in_train = sum(t['amount'] for t in queue.values())
    army     = google_sheets.load_player_army(pid)
    total    = sum(army.values())
    cap      = get_max_army_size(pid)
    if total + in_train + amt > cap:
        return await update.message.reply_text(
            f"⚡ Not enough capacity! {total}/{cap} + {in_train} in queue.\n\n"
            + render_status_panel(pid)
        )

    # schedule training
    per_min = UNIT_STATS[unit]["training_time"]
    dur     = datetime.timedelta(minutes=per_min * amt)
    end     = datetime.datetime.now() + dur
    google_sheets.save_training_task(pid, unit, amt, end)

    await update.message.reply_text(
        f"🏭 Training {amt}× {unit.title()} (ready in {per_min * amt}m)\n\n"
        + render_status_panel(pid)
    )

# ── View Army ────────────────────────────────────────────────────────────────
async def view_army(update, context):
    pid   = str(update.effective_user.id)
    army  = google_sheets.load_player_army(pid)
    if not army:
        return await update.message.reply_text(
            "🛡️ Your army is empty.\nUse /train to recruit.\n\n"
            + render_status_panel(pid)
        )

    lines = []
    atk = defp = hp = 0
    for u, cnt in army.items():
        stats = UNIT_STATS.get(u, {})
        atk  += stats.get("attack",0) * cnt
        defp += stats.get("defense",0)* cnt
        hp   += stats.get("hp",0)     * cnt
        lines.append(f"🔹 {u.title()}: {cnt} | Atk:{stats.get('attack',0)*cnt} Def:{stats.get('defense',0)*cnt} HP:{stats.get('hp',0)*cnt}")

    cap = get_max_army_size(pid)
    total = sum(army.values())
    summary = (
        f"⚔️ SkyHustle Army\n\n"
        + "\n".join(lines)
        + f"\n\nTotal: {total}/{cap}  Atk:{atk} Def:{defp} HP:{hp}\n\n"
        + render_status_panel(pid)
    )
    await update.message.reply_text(summary)

# ── Training Status & Claim ─────────────────────────────────────────────────
async def training_status(update, context):
    pid   = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    if not queue:
        return await update.message.reply_text(
            "🛡️ No units in training.\n\n" + render_status_panel(pid)
        )
    now = datetime.datetime.now()
    msgs = []
    for idx, t in queue.items():
        end = datetime.datetime.strptime(t['end_time'], "%Y-%m-%d %H:%M:%S")
        rem = (end - now).total_seconds()
        if rem <= 0:
            msgs.append(f"✅ {t['amount']} {t['unit_name'].title()} ready to claim!")
        else:
            m, s = divmod(int(rem), 60)
            msgs.append(f"⏳ {t['amount']} {t['unit_name'].title()}: {m}m{s}s")
    await update.message.reply_text("🛡️ Training Status:\n\n" + "\n".join(msgs) + "\n\n" + render_status_panel(pid))

async def claim_training(update, context):
    pid   = str(update.effective_user.id)
    queue = google_sheets.load_training_queue(pid)
    now   = datetime.datetime.now()
    claimed = {}
    for idx, t in list(queue.items()):
        end = datetime.datetime.strptime(t['end_time'], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[t['unit_name']] = claimed.get(t['unit_name'],0) + t['amount']
            google_sheets.delete_training_task(idx)
    if not claimed:
        return await update.message.reply_text("⏳ Nothing ready yet.\n\n" + render_status_panel(pid))

    army = google_sheets.load_player_army(pid)
    for u, cnt in claimed.items():
        army[u] = army.get(u,0) + cnt
    google_sheets.save_player_army(pid, army)

    lines = [f"🔹 {cnt}× {u.title()}" for u, cnt in claimed.items()]
    await update.message.reply_text("🎉 Claimed:\n\n" + "\n".join(lines) + "\n\n" + render_status_panel(pid))
