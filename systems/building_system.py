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

# ── BUILDING DEFINITIONS ────────────────────────────────────────────────────────
# base_time in minutes, time_mult per level,
# resource_cost(level) → dict, effect(level) → dict
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
            "mine_speed_pct": 10 * lvl  # +10% per level
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
            "storage_pct": 20 * lvl  # +20% cap per level
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
            "train_time_pct": -5 * lvl,  # -5% per level
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

# ── HELPERS ────────────────────────────────────────────────────────────────────
def _format_timedelta(delta: datetime.timedelta) -> str:
    secs = int(delta.total_seconds())
    h, rem = divmod(secs, 3600)
    m, s   = divmod(rem, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ── COMMANDS ───────────────────────────────────────────────────────────────────
async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # Current & next level
    cur_lv = get_building_level(player_id, key)
    nxt_lv = cur_lv + 1

    # Cost check
    cost = BUILDINGS[key]["resource_cost"](nxt_lv)
    res  = load_resources(player_id)
    for r, amt in cost.items():
        if res.get(r, 0) < amt:
            return await update.message.reply_text(
                f"❌ Not enough {r.capitalize()}: need {amt}, have {res.get(r,0)}\n\n"
                + render_status_panel(player_id)
            )

    # Deduct cost & save
    for r, amt in cost.items():
        res[r] -= amt
    save_resources(player_id, res)

    # Schedule build
    base = BUILDINGS[key]["base_time"]
    mult = BUILDINGS[key]["time_mult"]
    minutes = int(base * (mult ** cur_lv))
    ready_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    save_building_task(player_id, key, datetime.datetime.now(), ready_at)

    await update.message.reply_text(
        f"🔨 Upgrading **{key.title()}** to level {nxt_lv}.\n"
        f"⏱️ Ready in {minutes} minutes.\n\n"
        + render_status_panel(player_id)
    )

async def buildstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    queue = load_building_queue(player_id)
    if not queue:
        return await update.message.reply_text(
            "✅ No active constructions.\n\n" + render_status_panel(player_id)
        )

    now = datetime.datetime.now()
    lines = ["🔨 **Active Constructions:**"]
    for idx, task in queue.items():
        end = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
        rem = _format_timedelta(end - now)
        key = task["building_name"]
        lv  = get_building_level(player_id, key) + 1
        lines.append(f"• {key.title()} → Lv {lv} ({rem} remaining)")
    lines.append("")
    lines.append(render_status_panel(player_id))

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def buildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    cur    = get_building_level(player_id, key)
    nxt    = cur + 1
    cost   = BUILDINGS[key]["resource_cost"](nxt)
    effect = BUILDINGS[key]["effect"](nxt) or {}

    cost_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in cost.items())
    eff_str  = ", ".join(f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
                          for k, v in effect.items()) or "(no direct effect)"

    resp = (
        f"🏗️ **{key.title()}**\n"
        f"• Current Lv: {cur}\n"
        f"• Next Lv:    {nxt}\n"
        f"• Cost:       {cost_str}\n"
        f"• Effect:     {eff_str}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(resp, parse_mode="Markdown")
