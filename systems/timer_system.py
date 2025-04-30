import datetime
from utils.ui_helpers import render_status_panel
from utils import google_sheets

# In-memory mining tracker
player_mining = {}

# Resources per minute
MINING_SPEEDS = {
    "metal": 100,
    "fuel": 60,
    "crystal": 30,
}


# ── /mine — start mining ───────────────────────────────────────────────────────
async def start_mining(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    args = context.args or []

    if len(args) != 2:
        return await update.message.reply_text(
            "⛏️ Usage: /mine [resource] [amount]\n"
            "Example: /mine metal 1000\n\n"
            + panel
        )

    res = args[0].lower()
    try:
        amt = int(args[1])
    except ValueError:
        return await update.message.reply_text(
            "⚡ Amount must be a number.\n\n" + panel
        )

    if res not in MINING_SPEEDS:
        return await update.message.reply_text(
            "❌ Invalid resource. Available: metal, fuel, crystal.\n\n" + panel
        )

    # Prevent overlapping same-resource mines
    pm = player_mining.get(pid, {})
    if pm.get(res):
        return await update.message.reply_text(
            f"⚡ Already mining {res.capitalize()}! Claim first.\n\n" + panel
        )

    # Schedule mining
    speed = MINING_SPEEDS[res]
    seconds = amt / speed * 60
    finish = datetime.datetime.now() + datetime.timedelta(seconds=seconds)

    player_mining.setdefault(pid, {})[res] = {
        "amount": amt,
        "end": finish.strftime("%Y-%m-%d %H:%M:%S"),
    }

    msg = (
        "⛏️ Mining Started!\n\n"
        f"Resource: {res.capitalize()}\n"
        f"Amount: {amt}\n"
        f"Complete at: {finish:%Y-%m-%d %H:%M:%S}"
    )
    await update.message.reply_text(msg + "\n\n" + panel)


# ── /mining_status — check current mining ─────────────────────────────────────
async def mining_status(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    pm = player_mining.get(pid, {})

    if not pm:
        return await update.message.reply_text(
            "❌ No active mining. Use /mine to start.\n\n" + panel
        )

    now = datetime.datetime.now()
    lines = []

    for res, info in pm.items():
        end = datetime.datetime.strptime(info["end"], "%Y-%m-%d %H:%M:%S")
        rem = end - now
        if rem.total_seconds() <= 0:
            lines.append(f"✅ {res.capitalize()} ready to claim ({info['amount']}).")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            lines.append(f"⏳ {res.capitalize()}: {m}m{s}s remaining.")

    await update.message.reply_text("\n".join(lines) + "\n\n" + panel)


# ── /claim_mining — claim finished mining ────────────────────────────────────
async def claim_mining(update, context):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    pm = player_mining.get(pid, {})

    if not pm:
        return await update.message.reply_text(
            "❌ Nothing to claim.\n\n" + panel
        )

    now = datetime.datetime.now()
    claimed = {}

    for res, info in list(pm.items()):
        end = datetime.datetime.strptime(info["end"], "%Y-%m-%d %H:%M:%S")
        if now >= end:
            claimed[res] = info["amount"]
            del pm[res]

    if not claimed:
        return await update.message.reply_text(
            "⏳ Still mining—no resources ready.\n\n" + panel
        )

    # Add claimed resources to Google Sheets
    resources = google_sheets.load_resources(pid)
    for r, a in claimed.items():
        resources[r] = resources.get(r, 0) + a
    google_sheets.save_resources(pid, resources)

    summary = (
        "🎉 Claimed:\n"
        + "\n".join(f"🔹 {a} {r.capitalize()}" for r, a in claimed.items())
    )
    await update.message.reply_text(summary + "\n\n" + panel)
