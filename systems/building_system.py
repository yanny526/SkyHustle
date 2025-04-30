from datetime import datetime, timedelta
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

# ── BUILDING DEFINITIONS ────────────────────────────────────────────────────────
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
        "effects": {"train_time_pct": lambda lvl: -5 * lvl, "train_slots": lambda lvl: 50 + 10 * lvl},
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

# --- Helper Functions ---
def calculate_building_time(building: str, level: int) -> int:
    """Calculates the building time based on base time and multiplier."""
    data = BUILDING_DATA[building]
    return int(data["base_time"] * (data["time_mult"] ** (level - 1)))

def calculate_building_cost(building: str, level: int) -> dict:
    """Calculates the resource cost for a building level."""
    data = BUILDING_DATA[building]
    base_cost = data["resource_cost"]
    cost_factor = data["cost_increase_factor"]
    return {
        res: int(base_cost.get(res, 0) * (cost_factor ** (level - 1)))
        for res in base_cost
    }

def get_building_effect(building: str, level: int) -> dict:
    """Retrieves the effects of a building at a given level."""
    data = BUILDING_DATA[building]
    effects = data.get("effects", {})
    return {effect: func(level) for effect, func in effects.items()}

# ── /build — start building ────────────────────────────────────────────────────
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
        available = ", ".join(data["display_name"] for data in BUILDING_DATA.values())
        return await update.message.reply_text(
            f"Unknown building. Available: {available}\n\n" + render_status_panel(player_id),
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
                f"Not enough resources for {BUILDING_DATA[building]['display_name']} (Level {level}).\n"
                + f"Needed: {amt} {res.title()}\n"
                + f"You have: {resources.get(res, 0)} {res.title()}\n\n"
                + render_status_panel(player_id),
                parse_mode=ParseMode.HTML,
            )

    for res, amt in cost.items():
        resources[res] -= amt
    save_resources(player_id, resources)

    build_time = calculate_building_time(building, level)
    end_time = datetime.now() + timedelta(seconds=build_time)
    task = {
        "building_name": building,
        "level": level,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_building_task(player_id, task)

    return await update.message.reply_text(
        f"🏗️ Building {BUILDING_DATA[building]['display_name']} (Level {level})... Time: {build_time}s\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )

# ── /buildstatus — show building queue ─────────────────────────────────────────
async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    queue = load_building_queue(player_id)
    if not queue:
        return await update.message.reply_text(
            "No buildings in progress.\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    now = datetime.now()
    lines = []
    for task_id, task in queue.items():
        end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        remaining = end_time - now
        name = BUILDING_DATA[task["building_name"]]["display_name"]
        if remaining.total_seconds() > 0:
            lines.append(f"🏗️ {name} (Level {task['level']}): {remaining}")
        else:
            lines.append(f"✅ {name} (Level {task['level']}): Completed")

    return await update.message.reply_text(
        "🏗️ Building Queue:\n" + "\n".join(lines) + "\n\n" + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )

# ── /buildinfo — show next-level cost & effect ────────────────────────────────
async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /buildinfo [building_name]\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    building = context.args[0].lower()
    if building not in BUILDING_DATA:
        available = ", ".join(data["display_name"] for data in BUILDING_DATA.values())
        return await update.message.reply_text(
            f"Unknown building. Available: {available}\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    current_level = get_building_level(player_id, building)
    next_level = current_level + 1
    if next_level > BUILDING_DATA[building]["max_level"]:
        return await update.message.reply_text(
            "Max level reached!\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML,
        )

    cost = calculate_building_cost(building, next_level)
    effects = get_building_effect(building, next_level)

    cost_str = " | ".join(f"{res.capitalize()}: {amt}" for res, amt in cost.items())
    effects_str = (
        ", ".join(f"{name.replace('_', ' ').title()}: {val}" for name, val in effects.items())
        or "None"
    )

    return await update.message.reply_text(
        f"🏗️ {BUILDING_DATA[building]['display_name']} (Level {next_level}):\n"
        f"Cost: {cost_str}\n"
        f"Effects: {effects_str}\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )

# --- Utility Functions ---
def process_building_completion(player_id: str) -> str | None:
    """
    Checks for and finalizes completed building tasks, updating building levels.
    This should be called periodically or after certain commands.
    """
    queue = load_building_queue(player_id)
    now = datetime.now()
    completed = []
    for task_id, task in list(queue.items()):
        end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        if now >= end_time:
            save_building_level(player_id, task["building_name"], task["level"])
            delete_building_task(task_id)
            completed.append((task["building_name"], task["level"]))

    if completed:
        lines = [f"  {BUILDING_DATA[b]['display_name']} to Level {lvl}" for b, lvl in completed]
        return "🎉 Buildings upgraded:\n" + "\n".join(lines)
    return None

async def periodic_building_updates(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodically checks for completed buildings and sends updates to players.
    Schedule with `context.job_queue.run_repeating(...)`
    """
    job = context.job
    if not job:
        return
    player_id = job.user_id
    update = job.data.get("update")
    if not update:
        return
    msg = process_building_completion(player_id)
    if msg:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
