# systems/building_system.py

import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheets import (
    load_resources,
    save_resources,
    get_building_level,
    save_building_level,
    load_building_queue,
    save_building_task,
    delete_building_task
)
from utils.ui_helpers import render_status_panel

# === Configuration for each building ===
BUILDINGS = {
    "command_center": {
        "base_time": 60,    # minutes at level 1
        "time_mult": 1.5,   # growth factor per level
        "resource_cost": lambda lvl: {
            "metal":   1000 * lvl,
            "fuel":     500 * lvl,
            "crystal":  100 * lvl
        },
        "effect": lambda lvl: {
            "max_army": 1000 + lvl * 500
        }
    },
    "mine": {
        "base_time": 30,
        "time_mult": 1.4,
        "resource_cost": lambda lvl: {
            "metal": 500 * lvl
        },
        "effect": lambda lvl: {
            # future: e.g. faster yield
        }
    },
    # ← add more buildings here
}

def _format_timedelta(delta: datetime.timedelta) -> str:
    secs = int(delta.total_seconds())
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /build [building] — queue an upgrade of that building.
    """
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /build [building_name]\n\n" + render_status_panel(player_id)
        )

    key = context.args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"Unknown building. Available: {', '.join(BUILDINGS.keys())}\n\n"
            + render_status_panel(player_id)
        )

    # Determine levels
    cur_lv = get_building_level(player_id, key)
    nxt_lv = cur_lv + 1

    # Check cost
    cost = BUILDINGS[key]["resource_cost"](nxt_lv)
    res = load_resources(player_id)
    for r, amt in cost.items():
        if res.get(r, 0) < amt:
            return await update.message.reply_text(
                f"❌ Not enough {r.capitalize()}: need {amt}, have {res.get(r,0)}\n\n"
                + render_status_panel(player_id)
            )

    # Deduct cost
    for r, amt in cost.items():
        res[r] -= amt
    save_resources(player_id, res)

    # Schedule upgrade
    base = BUILDINGS[key]["base_time"]
    mult = BUILDINGS[key]["time_mult"]
    minutes = int(base * (mult ** cur_lv))
    now = datetime.datetime.now()
    ready_at = now + datetime.timedelta(minutes=minutes)
    save_building_task(player_id, key, now, ready_at)

    await update.message.reply_text(
        f"🔨 Upgrading {key.replace('_',' ').title()} → Level {nxt_lv}\n"
        f"⏱️ Ready in {minutes} minutes.\n\n"
        + render_status_panel(player_id)
    )

async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buildstatus — list all your in-progress building upgrades.
    """
    player_id = str(update.effective_user.id)
    queue = load_building_queue(player_id)
    if not queue:
        return await update.message.reply_text(
            "✅ No active constructions.\n\n" + render_status_panel(player_id)
        )

    now = datetime.datetime.now()
    lines = ["🔨 Active Constructions:"]
    for row_idx, task in queue.items():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = _format_timedelta(end - now)
        key = task["building_name"]
        lv = get_building_level(player_id, key) + 1
        lines.append(f"• {key.replace('_',' ').title()} → lvl {lv} ({rem} remaining)")

    # Append the status panel
    lines.append("")
    lines.append(render_status_panel(player_id))

    # Send as plain text (no parse_mode)
    await update.message.reply_text("\n".join(lines))

async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buildinfo [building] — show current lvl, next-level cost & effect.
    """
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /buildinfo [building]\n\n" + render_status_panel(player_id)
        )

    key = context.args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"Unknown building. Available: {', '.join(BUILDINGS.keys())}\n\n"
            + render_status_panel(player_id)
        )

    cur = get_building_level(player_id, key)
    nxt = cur + 1
    cost = BUILDINGS[key]["resource_cost"](nxt)
    effect = BUILDINGS[key]["effect"](nxt) or {}

    cost_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in cost.items())
    eff_str  = ", ".join(f"{k}+{v}" for k, v in effect.items()) or "(no direct effect)"

    response = (
        f"🏗️ {key.replace('_',' ').title()}\n"
        f"• Current Level: {cur}\n"
        f"• Next Level:    {nxt}\n"
        f"• Cost:          {cost_str}\n"
        f"• Effect:        {eff_str}\n\n"
        + render_status_panel(player_id)
    )

    # Plain text reply
    await update.message.reply_text(response)
