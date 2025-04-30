# resource_economy_system.py (Part 1 of X)

import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    get_building_level,
)
from utils.ui_helpers import render_status_panel

# ── Constants ────────────────────────────────────────────────────────────────

RESOURCE_TYPES = ["metal", "fuel", "crystal"]
BASE_PRODUCTION_RATES = {
    "metal": 20,
    "fuel": 10,
    "crystal": 5,
}

BONUS_PER_LEVEL = {
    "metal": 10,
    "fuel": 6,
    "crystal": 4,
}

BUILDING_MAPPING = {
    "metal": "metal_mine",
    "fuel": "fuel_refinery",
    "crystal": "crystal_synthesizer",
}

# In-memory tracker for last collection times
last_collected = {}

# ── Core Functions ────────────────────────────────────────────────────────────

def calculate_production(player_id: str, resource: str) -> int:
    building = BUILDING_MAPPING[resource]
    level = get_building_level(player_id, building)
    base = BASE_PRODUCTION_RATES[resource]
    bonus = BONUS_PER_LEVEL[resource]
    return base + (bonus * level)


def calculate_earnings(player_id: str, resource: str) -> int:
    last_time = last_collected.get((player_id, resource))
    now = datetime.datetime.now()
    if not last_time:
        last_collected[(player_id, resource)] = now
        return 0

    elapsed_minutes = (now - last_time).total_seconds() / 60
    rate = calculate_production(player_id, resource)
    earnings = int(rate * elapsed_minutes)
    return max(0, earnings)
# resource_economy_system.py (Part 2 of X)

async def collect_resource(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)

    if len(context.args) != 1 or context.args[0].lower() not in RESOURCE_TYPES:
        return await update.message.reply_text(
            "Usage: /collect [metal|fuel|crystal]\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    res = context.args[0].lower()
    amount = calculate_earnings(player_id, res)

    if amount <= 0:
        return await update.message.reply_text(
            f"⏳ No {res.title()} available to collect yet.\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    resources = load_resources(player_id)
    resources[res] += amount
    save_resources(player_id, resources)
    last_collected[(player_id, res)] = datetime.datetime.now()

    await update.message.reply_text(
        f"✅ Collected {amount} {res.title()}!\n\n" + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )


async def collect_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    total_collected = {}

    for res in RESOURCE_TYPES:
        amt = calculate_earnings(player_id, res)
        if amt > 0:
            total_collected[res] = amt
            last_collected[(player_id, res)] = datetime.datetime.now()

    if not total_collected:
        return await update.message.reply_text(
            "⏳ Nothing to collect yet. Come back later.\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    resources = load_resources(player_id)
    for res, amt in total_collected.items():
        resources[res] += amt
    save_resources(player_id, resources)

    lines = [f"✅ Collected:"]
    lines += [f"• {res.title()}: {amt}" for res, amt in total_collected.items()]
    lines.append("")
    lines.append(render_status_panel(player_id))

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
# resource_economy_system.py (Part 3 of X)

def get_mining_speed(player_id: str, resource: str) -> int:
    level = get_building_level(player_id, f"{resource}_mine")
    if resource == "metal":
        return 100 * (2 ** (level - 1)) if level else 0
    elif resource == "fuel":
        return 60 * (2 ** (level - 1)) if level else 0
    elif resource == "crystal":
        return 30 * (2 ** (level - 1)) if level else 0
    return 0


def get_last_collected_time(player_id: str, res: str) -> datetime.datetime:
    return last_collected.get((player_id, res), datetime.datetime.now())


def calculate_earnings(player_id: str, res: str) -> int:
    speed = get_mining_speed(player_id, res)
    last_time = get_last_collected_time(player_id, res)
    elapsed_seconds = (datetime.datetime.now() - last_time).total_seconds()
    return int(speed * elapsed_seconds // 60)


def format_economy_report(player_id: str) -> str:
    report = ["<b>⛏️ Resource Production Report:</b>"]
    for res in RESOURCE_TYPES:
        speed = get_mining_speed(player_id, res)
        last_time = get_last_collected_time(player_id, res)
        earnings = calculate_earnings(player_id, res)
        since = (datetime.datetime.now() - last_time).seconds // 60
        report.append(f"• {res.title()}: {earnings} (⏱️ {speed}/min, {since}m)")
    return "\n".join(report)


async def economy_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    report = format_economy_report(player_id)
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        f"{report}\n\n{panel}",
        parse_mode=ParseMode.HTML,
    )
# resource_economy_system.py (Part 4 of X)

async def manual_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    collected = {}
    resources = load_resources(player_id)

    for res in RESOURCE_TYPES:
        gain = calculate_earnings(player_id, res)
        if gain > 0:
            resources[res] = resources.get(res, 0) + gain
            last_collected[(player_id, res)] = datetime.datetime.now()
            collected[res] = gain

    save_resources(player_id, resources)

    if not collected:
        await update.message.reply_text("⏳ No new resources to collect yet.")
        return

    summary = "\n".join(
        f"• {res.title()}: +{amt}" for res, amt in collected.items()
    )
    panel = render_status_panel(player_id)
    await update.message.reply_text(
        f"✅ Collected Resources:\n{summary}\n\n{panel}",
        parse_mode=ParseMode.HTML,
    )


def register_economy_handlers(app):
    app.add_handler(CommandHandler("collect", manual_collect))
    app.add_handler(CommandHandler("economy", economy_status))

