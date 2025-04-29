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
    delete_building_task
)
from utils.ui_helpers import render_status_panel

# ── BUILDING DEFINITIONS ────────────────────────────────────────────────────────
BUILDINGS = {
    "command_center": {
        "base_time": 60,
        "time_mult": 1.5,
        "resource_cost": lambda lvl: {
            "metal":   1000 * lvl,
            "fuel":     500 * lvl,
            "crystal":  100 * lvl
        },
        "effect": lambda lvl: {
            "max_army": 1000 + lvl * 500
        }
    },
    "metal_mine": {
        "base_time": 30,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "metal": 200 * lvl,
            "fuel":  100 * lvl
        },
        "effect": lambda lvl: {
            "mine_speed_pct": 10 * lvl
        }
    },
    "fuel_refinery": {
        "base_time": 30,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "metal": 150 * lvl,
            "fuel":  150 * lvl
        },
        "effect": lambda lvl: {
            "refinery_speed_pct": 10 * lvl
        }
    },
    "crystal_synthesizer": {
        "base_time": 45,
        "time_mult": 1.3,
        "resource_cost": lambda lvl: {
            "metal":   300 * lvl,
            "crystal":  50 * lvl
        },
        "effect": lambda lvl: {
            "crystal_rate_pct": 5 * lvl
        }
    },
    "warehouse": {
        "base_time": 40,
        "time_mult": 1.25,
        "resource_cost": lambda lvl: {
            "metal":   500 * lvl,
            "fuel":    500 * lvl,
            "crystal": 200 * lvl
        },
        "effect": lambda lvl: {
            "storage_pct": 20 * lvl
        }
    },
    "barracks": {
        "base_time": 40,
        "time_mult": 1.3,
        "resource_cost": lambda lvl: {
            "metal":  500 * lvl,
            "fuel":   200 * lvl,
            "crystal":100 * lvl
        },
        "effect": lambda lvl: {
            "train_time_pct": -5 * lvl,
            "train_slots":    50 + 10 * lvl
        }
    },
    "vehicle_factory": {
        "base_time": 120,
        "time_mult": 1.4,
        "resource_cost": lambda lvl: {
            "metal":   2000 * lvl,
            "fuel":    1000 * lvl,
            "crystal": 200 * lvl
        },
        "effect": lambda lvl: {
            "vehicle_build_pct": -5 * lvl
        }
    },
    "drone_hangar": {
        "base_time": 50,
        "time_mult": 1.3,
        "resource_cost": lambda lvl: {
            "metal": 300 * lvl,
            "fuel":  100 * lvl
        },
        "effect": lambda lvl: {
            "drone_speed_pct": 10 * lvl
        }
    },
    "research_lab": {
        "base_time": 90,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "metal":   500 * lvl,
            "crystal": 500 * lvl
        },
        "effect": lambda lvl: {
            "tech_slots": 2 * lvl
        }
    },
    "shield_generator": {
        "base_time": 80,
        "time_mult": 1.25,
        "resource_cost": lambda lvl: {
            "metal":   600 * lvl,
            "crystal": 200 * lvl
        },
        "effect": lambda lvl: {
            "damage_reduction_pct": 2 * lvl
        }
    },
    "laser_turrets": {
        "base_time": 60,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "metal": 800 * lvl
        },
        "effect": lambda lvl: {
            "turret_dps_pct": 10 * lvl
        }
    },
    "missile_silos": {
        "base_time": 70,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "metal": 1000 * lvl,
            "fuel":   500 * lvl
        },
        "effect": lambda lvl: {
            "missile_speed_pct": 5 * lvl
        }
    },
    "radar_station": {
        "base_time": 45,
        "time_mult": 1.15,
        "resource_cost": lambda lvl: {
            "metal": 300 * lvl,
            "fuel":  200 * lvl
        },
        "effect": lambda lvl: {
            "detection_range": 10 * lvl
        }
    },
    "orbital_shipyard": {
        "base_time": 180,
        "time_mult": 1.3,
        "resource_cost": lambda lvl: {
            "metal":   5000 * lvl,
            "crystal": 1000 * lvl
        },
        "effect": lambda lvl: {
            "ship_slots": lvl
        }
    },
    "trade_hub": {
        "base_time": 30,
        "time_mult": 1.1,
        "resource_cost": lambda lvl: {
            "credits": 200 * lvl
        },
        "effect": lambda lvl: {
            "trade_bonus_pct": 2 * lvl
        }
    },
    "black_market": {
        "base_time": 120,
        "time_mult": 1.5,
        "resource_cost": lambda lvl: {
            "credits": 500 * lvl,
            "crystal": 200 * lvl
        },
        "effect": lambda lvl: {
            "discount_pct": 5 * lvl
        }
    },
    "nanite_forge": {
        "base_time": 100,
        "time_mult": 1.2,
        "resource_cost": lambda lvl: {
            "crystal": 300 * lvl
        },
        "effect": lambda lvl: {
            "conversion_efficiency_pct": 5 * lvl
        }
    },
}

# Display‐friendly names
DISPLAY = {
    key: key.replace("_", " ").title()
    for key in BUILDINGS
}

def _format_timedelta(delta: datetime.timedelta) -> str:
    secs = int(delta.total_seconds())
    h, rem = divmod(secs, 3600)
    m, s   = divmod(rem, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ── /buildings — show full menu ───────────────────────────────────────────────
async def buildings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    res = load_resources(player_id)  # just to ensure the sheet exists

    lines = ["<b>🏛️ Buildings Overview</b>"]
    for key, cfg in BUILDINGS.items():
        cur = get_building_level(player_id, key)
        nxt = cur + 1
        cost = cfg["resource_cost"](nxt)
        eff  = cfg["effect"](nxt) or {}

        cost_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in cost.items())
        eff_str  = ", ".join(
            f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
            for k, v in eff.items()
        ) or "(no direct effect)"

        lines.append(
            f"<b>{DISPLAY[key]}</b> (Lv {cur})\n"
            f" • Next Lv {nxt} cost: {cost_str}\n"
            f" • Effect: {eff_str}\n"
        )

    lines.append(render_status_panel(player_id))
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML
    )

# ── /build — queue an upgrade ───────────────────────────────────────────────
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /build [building_name]\n\n" +
            render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    key = context.args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"Unknown building. Available: {', '.join(DISPLAY.values())}\n\n"
            + render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    cur = get_building_level(player_id, key)
    nxt = cur + 1
    cost = BUILDINGS[key]["resource_cost"](nxt)
    res  = load_resources(player_id)

    # check cost
    for r, amt in cost.items():
        if res.get(r, 0) < amt:
            return await update.message.reply_text(
                f"❌ Not enough {r.title()}: need {amt}, have {res.get(r,0)}\n\n"
                + render_status_panel(player_id),
                parse_mode=ParseMode.HTML
            )

    # deduct & schedule
    for r, amt in cost.items():
        res[r] -= amt
    save_resources(player_id, res)

    minutes = int(
        BUILDINGS[key]["base_time"]
        * (BUILDINGS[key]["time_mult"] ** cur)
    )
    ready_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    save_building_task(player_id, key, datetime.datetime.now(), ready_at)

    await update.message.reply_text(
        f"🔨 Upgrading <b>{DISPLAY[key]}</b> to level {nxt}.\n"
        f"⏱️ Ready in {minutes}m.\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML
    )

# ── /buildstatus — list in-progress builds ─────────────────────────────────
async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    queue = load_building_queue(player_id)
    if not queue:
        return await update.message.reply_text(
            "✅ No active constructions.\n\n" +
            render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    now = datetime.datetime.now()
    lines = ["<b>🔨 Active Constructions:</b>"]
    for idx, task in queue.items():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = _format_timedelta(end - now)
        key = task["building_name"]
        lv  = get_building_level(player_id, key) + 1
        lines.append(
            f"• <b>{DISPLAY[key]}</b> → Lv {lv} ({rem} remaining)"
        )

    lines.append("")
    lines.append(render_status_panel(player_id))
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML
    )

# ── /buildinfo — show next-level cost & effect ─────────────────────────────
async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /buildinfo [building_name]\n\n" +
            render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    key = context.args[0].lower()
    if key not in BUILDINGS:
        return await update.message.reply_text(
            f"Unknown building. Available: {', '.join(DISPLAY.values())}\n\n"
            + render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    cur = get_building_level(player_id, key)
    nxt = cur + 1
    cost = BUILDINGS[key]["resource_cost"](nxt)
    eff  = BUILDINGS[key]["effect"](nxt) or {}

    cost_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in cost.items())
    eff_str  = ", ".join(
        f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
        for k, v in eff.items()
    ) or "(no direct effect)"

    await update.message.reply_text(
        "<b>🏗️ " + DISPLAY[key] + "</b>\n"
        f"• Current Lv: {cur}\n"
        f"• Next Lv:    {nxt}\n"
        f"• Cost:       {cost_str}\n"
        f"• Effect:     {eff_str}\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML
    )
