# mission_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import load_player_missions, save_player_mission, load_resources, save_resources
from utils.ui_helpers import render_status_panel

# ── Static Mission Definitions ────────────────────────────────────────────

MISSIONS = {
    "build_metal_mine": {
        "title": "⛏️ Construct a Metal Mine",
        "desc": "Start metal extraction by building your first mine.",
        "check": lambda stats: stats.get("metal_mine", 0) >= 1,
        "reward": {"metal": 300, "fuel": 150}
    },
    "train_soldiers": {
        "title": "🪖 Train Soldiers",
        "desc": "Recruit a basic force to defend your empire.",
        "check": lambda stats: stats.get("soldier", 0) >= 5,
        "reward": {"credits": 100}
    },
    "upgrade_barracks": {
        "title": "🏗️ Barracks Upgrade",
        "desc": "Upgrade your Barracks to level 2 or more.",
        "check": lambda stats: stats.get("barracks", 0) >= 2,
        "reward": {"metal": 500}
    },
    "build_crystal_synth": {
        "title": "🔮 Crystal Synthesizer Online",
        "desc": "Unlock and build a Crystal Synthesizer.",
        "check": lambda stats: stats.get("crystal_synthesizer", 0) >= 1,
        "reward": {"crystal": 100}
    },
    "train_tanks": {
        "title": "🚛 Tank Division",
        "desc": "Train at least 3 tanks for your armored unit.",
        "check": lambda stats: stats.get("tank", 0) >= 3,
        "reward": {"credits": 250, "metal": 500}
    },
}
# ── Helper: Check Mission Completion ──────────────────────────────────────

def evaluate_missions(player_id: str, stats: dict) -> dict:
    """
    Returns dict of mission_id → status (complete or not)
    """
    results = {}
    completed = {m["mission_id"] for m in load_player_missions(player_id)}
    for key, mission in MISSIONS.items():
        is_done = mission["check"](stats)
        results[key] = "CLAIMED" if key in completed else ("READY" if is_done else "LOCKED")
    return results


# ── Command: /missions — View Mission List ────────────────────────────────

async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    stats = context.user_data.get("stats", {})  # must be pre-loaded externally
    if not stats:
        return await update.message.reply_text("❌ Error: Mission stats missing.")

    status = evaluate_missions(pid, stats)
    lines = ["<b>📜 Missions</b>"]
    buttons = []

    for key, mission in MISSIONS.items():
        state = status[key]
        emoji = "✅" if state == "CLAIMED" else "🎯" if state == "READY" else "🔒"
        lines.append(f"{emoji} <b>{mission['title']}</b>\n<code>{mission['desc']}</code>")
        if state == "READY":
            buttons.append([InlineKeyboardButton(f"🎁 Claim {mission['title']}", callback_data=f"CLAIM_MISSION:{key}")])

    lines.append("\nTap the buttons below to claim rewards.")

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(
        "\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=markup
    )


# ── Callback: Claim Mission Reward ─────────────────────────────────────────
async def claim_mission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":", 1)[1]

    stats = context.user_data.get("stats", {})
    if not stats:
        return await query.edit_message_text("❌ Error: Mission data not loaded.")

    state = evaluate_missions(pid, stats).get(key)
    if state != "READY":
        return await query.edit_message_text("⚠️ Mission not complete or already claimed.")

    reward = MISSIONS[key]["reward"]
    resources = load_resources(pid)
    for k, v in reward.items():
        resources[k] = resources.get(k, 0) + v
    save_resources(pid, resources)
    save_player_mission(pid, key, completed=True)

    await query.edit_message_text(
        f"🎉 You claimed rewards for <b>{MISSIONS[key]['title']}</b>!\n"
        f"Resources gained: " + ", ".join(f"{k.title()}: {v}" for k, v in reward.items()),
        parse_mode=ParseMode.HTML
    )
# ── Helper: Preload Stats for Mission Evaluation ──────────────────────────

def load_mission_stats(player_id: str) -> dict:
    """
    Assembles the relevant data used by all mission check functions.
    This should include building levels, army size, etc.
    """
    from utils.google_sheets import get_building_level, load_player_army

    stats = {}

    # Building levels
    stats["metal_mine"] = get_building_level(player_id, "metal_mine")
    stats["barracks"] = get_building_level(player_id, "barracks")

    # Army size
    army = load_player_army(player_id)
    total_units = sum(qty for unit, qty in army.items() if not "_" in unit)
    stats["total_units"] = total_units

    return stats


# ── Middleware Hook or Updater Logic Integration ──────────────────────────

async def preload_mission_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Should be called before any mission commands to ensure mission stats are available.
    """
    pid = str(update.effective_user.id)
    context.user_data["stats"] = load_mission_stats(pid)
