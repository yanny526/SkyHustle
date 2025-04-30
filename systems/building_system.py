import json
import os
with open(os.path.join(os.path.dirname(__file__), "../config/building_stats.json"), "r") as f:
    BUILDINGS = json.load(f)

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


# ── BUILDING DEFINITIONS ───────────────────────────────────────────────────────
BUILDING_DATA = {
    "command_center": {
        "display_name": "Command Center",
        "base_time": 60,
        "time_mult": 1.5,
        "resource_cost": {"metal": 1000, "fuel": 500, "crystal": 100},
        "cost_increase_factor": 1.8,
        "effects": {"max_army": lambda lvl: 1000 + lvl * 500},
        "max_level": 5,
    },
    "metal_mine": {
        "display_name": "Metal Mine",
        "base_time": 30,
        "time_mult": 1.2,
        "resource_cost": {"metal": 200, "fuel": 100},
        "cost_increase_factor": 1.7,
        "effects": {"mine_speed_pct": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
    "fuel_refinery": {
        "display_name": "Fuel Refinery",
        "base_time": 30,
        "time_mult": 1.2,
        "resource_cost": {"metal": 150, "fuel": 150},
        "cost_increase_factor": 1.7,
        "effects": {"refinery_speed_pct": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
    "crystal_synthesizer": {
        "display_name": "Crystal Synthesizer",
        "base_time": 45,
        "time_mult": 1.3,
        "resource_cost": {"metal": 300, "crystal": 50},
        "cost_increase_factor": 1.7,
        "effects": {"crystal_rate_pct": lambda lvl: 5 * lvl},
        "max_level": 5,
    },
    "warehouse": {
        "display_name": "Warehouse",
        "base_time": 40,
        "time_mult": 1.25,
        "resource_cost": {"metal": 500, "fuel": 500, "crystal": 200},
        "cost_increase_factor": 1.7,
        "effects": {"storage_pct": lambda lvl: 20 * lvl},
        "max_level": 5,
    },
    "barracks": {
        "display_name": "Barracks",
        "base_time": 40,
        "time_mult": 1.3,
        "resource_cost": {"metal": 500, "fuel": 200, "crystal": 100},
        "cost_increase_factor": 1.7,
        "effects": {
            "train_time_pct": lambda lvl: -5 * lvl,
            "train_slots": lambda lvl: 50 + 10 * lvl,
        },
        "max_level": 5,
    },
    "vehicle_factory": {
        "display_name": "Vehicle Factory",
        "base_time": 120,
        "time_mult": 1.4,
        "resource_cost": {"metal": 2000, "fuel": 1000, "crystal": 200},
        "cost_increase_factor": 1.8,
        "effects": {"vehicle_build_pct": lambda lvl: -5 * lvl},
        "max_level": 5,
    },
    "drone_hangar": {
        "display_name": "Drone Hangar",
        "base_time": 50,
        "time_mult": 1.3,
        "resource_cost": {"metal": 300, "fuel": 100},
        "cost_increase_factor": 1.7,
        "effects": {"drone_speed_pct": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
    "research_lab": {
        "display_name": "Research Lab",
        "base_time": 90,
        "time_mult": 1.2,
        "resource_cost": {"metal": 500, "crystal": 500},
        "cost_increase_factor": 1.7,
        "effects": {"tech_slots": lambda lvl: 2 * lvl},
        "max_level": 5,
    },
    "shield_generator": {
        "display_name": "Shield Generator",
        "base_time": 80,
        "time_mult": 1.25,
        "resource_cost": {"metal": 600, "crystal": 200},
        "cost_increase_factor": 1.75,
        "effects": {"damage_reduction_pct": lambda lvl: 2 * lvl},
        "max_level": 5,
    },
    "laser_turrets": {
        "display_name": "Laser Turrets",
        "base_time": 60,
        "time_mult": 1.2,
        "resource_cost": {"metal": 800},
        "cost_increase_factor": 1.7,
        "effects": {"turret_dps_pct": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
    "missile_silos": {
        "display_name": "Missile Silos",
        "base_time": 70,
        "time_mult": 1.2,
        "resource_cost": {"metal": 1000, "fuel": 500},
        "cost_increase_factor": 1.7,
        "effects": {"missile_speed_pct": lambda lvl: 5 * lvl},
        "max_level": 5,
    },
    "radar_station": {
        "display_name": "Radar Station",
        "base_time": 45,
        "time_mult": 1.15,
        "resource_cost": {"metal": 300, "fuel": 200},
        "cost_increase_factor": 1.6,
        "effects": {"detection_range": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
    "orbital_shipyard": {
        "display_name": "Orbital Shipyard",
        "base_time": 180,
        "time_mult": 1.3,
        "resource_cost": {"metal": 5000, "crystal": 1000},
        "cost_increase_factor": 1.9,
        "effects": {"ship_slots": lambda lvl: lvl},
        "max_level": 5,
    },
    "trade_hub": {
        "display_name": "Trade Hub",
        "base_time": 100,
        "time_mult": 1.2,
        "resource_cost": {"metal": 1000, "fuel": 1000, "crystal": 500},
        "cost_increase_factor": 1.7,
        "effects": {"trade_capacity": lambda lvl: 10 * lvl},
        "max_level": 5,
    },
}


# ── Helper Functions ─────────────────────────────────────────────────────────
def calculate_building_time(building: str, level: int) -> int:
    data = BUILDING_DATA[building]
    return int(data["base_time"] * (data["time_mult"] ** (level - 1)))


def calculate_building_cost(building: str, level: int) -> dict:
    data = BUILDING_DATA[building]
    base_cost = data["resource_cost"]
    factor = data["cost_increase_factor"]
    return {
        res: int(base_cost.get(res, 0) * (factor ** (level - 1)))
        for res in base_cost
    }


def get_building_effect(building: str, level: int) -> dict:
    data = BUILDING_DATA[building]
    effects = data.get("effects", {})
    return {name: fn(level) for name, fn in effects.items()}


# ── /build — start building ───────────────────────────────────────────────────
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        return await update.message.reply_text(
            "Usage: /build [building_name]\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    building = args[0].lower()
    if building not in BUILDING_DATA:
        available = ", ".join(
            BUILDING_DATA[b]["display_name"] for b in BUILDING_DATA
        )
        return await update.message.reply_text(
            f"Unknown building. Available: {available}\n\n"
            + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    level = get_building_level(player_id, building) + 1
    if level > BUILDING_DATA[building]["max_level"]:
        return await update.message.reply_text(
            "Max level reached!\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    cost = calculate_building_cost(building, level)
    resources = load_resources(player_id)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            return await update.message.reply_text(
                f"Not enough resources to build {BUILDING_DATA[building]['display_name']} "
                f"(Level {level}).\n"
                f"Needed: {amt} {res.title()}\n"
                f"You have: {resources.get(res, 0)} {res.title()}\n\n"
                + render_status_panel(player_id),
                parse_mode=ParseMode.HTML,
            )

    # Deduct resources
    for res, amt in cost.items():
        resources[res] -= amt
    save_resources(player_id, resources)

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=calculate_building_time(building, level))
    task = {
        "building_name": building,
        "level": level,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_building_task(player_id, task)

    await update.message.reply_text(
        f"🏗️ Building {BUILDING_DATA[building]['display_name']} "
        f"(Level {level})… Time: {int((end_time - start_time).total_seconds())}s\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )


# ── /buildstatus — list in-progress builds ────────────────────────────────────
async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    queue = load_building_queue(player_id)

    if not queue:
        return await update.message.reply_text(
            "✅ No active constructions.\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    now = datetime.datetime.now()
    lines = ["<b>🔨 Active Constructions:</b>"]
    for idx, task in queue.items():
        end_time = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = end_time - now
        key = task["building_name"]
        level = task["level"]
        lines.append(
            f"• <b>{BUILDING_DATA[key]['display_name']}</b> → Lv {level} ({rem})"
        )

    lines.append("")
    lines.append(render_status_panel(player_id))

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


# ── /buildinfo — show next-level cost & effect ───────────────────────────────
async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /buildinfo [building_name]\n\n"
            + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    key = context.args[0].lower()
    if key not in BUILDING_DATA:
        available = ", ".join(
            BUILDING_DATA[b]["display_name"] for b in BUILDING_DATA
        )
        return await update.message.reply_text(
            f"Unknown building. Available: {available}\n\n"
            + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    cur = get_building_level(player_id, key)
    nxt = cur + 1
    cost = calculate_building_cost(key, nxt)
    eff = get_building_effect(key, nxt) or {}

    cost_str = " | ".join(f"{k.title()}: {v}" for k, v in cost.items())
    eff_str = ", ".join(
        f"{k.replace('_', ' ').title()}: {v}{'%' if 'pct' in k else ''}"
        for k, v in eff.items()
    ) or "(no direct effect)"

    await update.message.reply_text(
        f"<b>🏗️ {BUILDING_DATA[key]['display_name']}</b>\n"
        f"• Current Lv: {cur}\n"
        f"• Next Lv: {nxt}\n"
        f"• Cost: {cost_str}\n"
        f"• Effect: {eff_str}\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )
