import datetime

from utils.ui_helpers import render_status_panel
from utils import google_sheets

# In-memory mining tracker
# player_mining[player_id] = {resource: {"amount": int, "end_time": str}}
player_mining: dict[str, dict[str, dict[str, str]]] = {}

# Resources per minute
MINING_SPEEDS = {
    "metal": 100,
    "fuel": 60,
    "crystal": 30,
}


async def start_mining(update, context):
    """
    /mine [resource] [amount] — Start mining a resource.
    """
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    args = context.args or []

    if len(args) != 2:
        return await update.message.reply_text(
            "⛏️ Usage: /mine [resource] [amount]\n"
            "Example: /mine metal 1000\n\n" + panel
        )

    resource = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        return await update.message.reply_text(
            "⚡ Amount must be a number.\n\n" + panel
        )

    if resource not in MINING_SPEEDS:
        return await update.message.reply_text(
            "❌ Invalid resource. Available: metal, fuel, crystal.\n\n" + panel
        )

    speed = MINING_SPEEDS[resource]
    minutes = amount / speed
    finish_dt = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    finish_str = finish_dt.strftime("%Y-%m-%d %H:%M:%S")

    player_mining.setdefault(pid, {})[resource] = {
        "amount": amount,
        "end_time": finish_str,
    }

    await update.message.reply_text(
        f"⛏️ Mining {amount} {resource.title()}... "
        f"(ends {finish_str})\n\n" + panel
    )


async def mining_status(update, context):
    """
    /minestatus — Check current mining operations.
    """
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    mines = player_mining.get(pid, {})

    if not mines:
        return await update.message.reply_text(
            "❌ Not currently mining anything.\n\n" + panel
        )

    now = datetime.datetime.now()
    lines = ["⛏️ Current Mining Operations:"]

    for resource, info in mines.items():
        end_str = info.get("end_time")
        if not end_str:
            continue
        end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        rem = end_dt - now
        if rem.total_seconds() <= 0:
            lines.append(f"✅ {resource.title()} ready to claim ({info['amount']}).")
        else:
            m, s = divmod(int(rem.total_seconds()), 60)
            lines.append(f"⏳ {resource.title()}: {m}m{s}s remaining.")

    await update.message.reply_text("\n".join(lines) + "\n\n" + panel)


async def claim_mining(update, context):
    """
    /claimmine — Claim completed mining operations.
    """
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    mines = player_mining.get(pid, {})

    if not mines:
        return await update.message.reply_text(
            "❌ Nothing to claim.\n\n" + panel
        )

    now = datetime.datetime.now()
    claimed: dict[str, int] = {}
    for resource, info in list(mines.items()):
        end_str = info.get("end_time")
        if not end_str:
            continue
        end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        if now >= end_dt:
            claimed[resource] = info["amount"]
            del mines[resource]

    if not claimed:
        return await update.message.reply_text(
            "⏳ Still mining—no resources ready.\n\n" + panel
        )

    resources = google_sheets.load_resources(pid)
    for r, amt in claimed.items():
        resources[r] = resources.get(r, 0) + amt
    google_sheets.save_resources(pid, resources)

    claimed_str = ", ".join(f"{amt} {r.title()}" for r, amt in claimed.items())
    await update.message.reply_text(f"✅ Claimed: {claimed_str}\n\n" + panel)
