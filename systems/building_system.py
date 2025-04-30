import os
import json
import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    get_building_level,
    save_building_level,
    load_building_queue,
    save_building_task,
    delete_building_task,
)
from utils.ui_helpers import render_status_panel

# ── Core Building Data ───────────────────────────────────────────────────────
with open(os.path.join(os.path.dirname(__file__), "../config/building_stats.json"), "r") as f:
    BUILDING_STATS = json.load(f)

# ── Helper: Format timedelta ─────────────────────────────────────────────────
def _format_timedelta(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m {seconds}s")
    return " ".join(parts)

# ── Runtime BUILDINGS helper for UI calls ────────────────────────────────────
BUILDINGS = {}
for key, data in BUILDING_STATS.items():
    BUILDINGS[key] = {
        "resource_cost": lambda lvl, d=data: {
            res: int(base * (d["cost_multiplier"] ** (lvl - 1)))
            for res, base in d["base_cost"].items()
        },
        "effect": lambda lvl, d=data: {
            k: v[lvl - 1] if lvl - 1 < len(v) else ""
            for k, v in d.get("effects", {}).items()
        },
        "base_time_min": data["base_time_min"],
        "time_multiplier": data["time_multiplier"],
        "max_level": data["max_level"],
    }

# ── /build — start construction ─────────────────────────────────────────────
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        return await update.message.reply_text(
            "Usage: /build [building_name]\n\n" + render_status_panel(pid),
            parse_mode=ParseMode.HTML,
        )

    key = args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"Unknown building. Available: {', '.join(BUILDINGS.keys())}\n\n" + render_status_panel(pid),
            parse_mode=ParseMode.HTML,
        )

    level = get_building_level(pid, key) + 1
    if level > BUILDINGS[key]["max_level"]:
        return await update.message.reply_text("Max level reached!\n\n" + render_status_panel(pid), parse_mode=ParseMode.HTML)

    cost = BUILDINGS[key]["resource_cost"](level)
    resources = load_resources(pid)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            return await update.message.reply_text(
                f"Not enough {res.title()} to build {key.replace('_',' ').title()} (Lv {level}).\n\n" + render_status_panel(pid),
                parse_mode=ParseMode.HTML,
            )

    for res, amt in cost.items():
        resources[res] -= amt
    save_resources(pid, resources)

    base_time = BUILDINGS[key]["base_time_min"]
    multiplier = BUILDINGS[key]["time_multiplier"]
    duration = base_time * (multiplier ** (level - 1))
    now = datetime.datetime.now()
    end_time = now + datetime.timedelta(minutes=duration)

    save_building_task(pid, key, end_time.strftime("%Y-%m-%d %H:%M:%S"))

    await update.message.reply_text(
        f"🏗️ Building {key.replace('_',' ').title()} to Lv {level}... ETA: {_format_timedelta(end_time - now)}\n\n" + render_status_panel(pid),
        parse_mode=ParseMode.HTML,
    )

# ── /buildstatus — active constructions ──────────────────────────────────────
async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    queue = load_building_queue(pid)

    if not queue:
        return await update.message.reply_text("✅ No active constructions.\n\n" + render_status_panel(pid), parse_mode=ParseMode.HTML)

    now = datetime.datetime.now()
    lines = ["<b>🔨 Active Constructions:</b>"]
    for task in queue.values():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = _format_timedelta(end - now)
        lines.append(f"• <b>{task['building_name'].replace('_',' ').title()}</b> → Lv {task['level']} ({rem})")

    lines.append("\n" + render_status_panel(pid))
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# ── /buildinfo — preview cost & effect ───────────────────────────────────────
async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        return await update.message.reply_text("Usage: /buildinfo [building_name]\n\n" + render_status_panel(pid), parse_mode=ParseMode.HTML)

    key = args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(f"Unknown building. Available: {', '.join(BUILDINGS.keys())}\n\n" + render_status_panel(pid), parse_mode=ParseMode.HTML)

    cur = get_building_level(pid, key)
    nxt = cur + 1
    cost = BUILDINGS[key]["resource_cost"](nxt)
    eff = BUILDINGS[key]["effect"](nxt)

    cost_str = " | ".join(f"{k.title()}: {v}" for k, v in cost.items())
    eff_str = ", ".join(f"{k.replace('_',' ').title()}: {v}" for k, v in eff.items()) or "(no effect)"

    await update.message.reply_text(
        f"<b>🏗️ {key.replace('_',' ').title()}</b>\n"
        f"• Current Lv: {cur}\n"
        f"• Next Lv: {nxt}\n"
        f"• Cost: {cost_str}\n"
        f"• Effect: {eff_str}\n\n"
        + render_status_panel(pid),
        parse_mode=ParseMode.HTML,
    )
