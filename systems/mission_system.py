# mission_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import load_player_missions, save_player_mission, load_resources, save_resources
from utils.google_sheets import get_building_level, load_player_army
from utils.ui_helpers import render_status_panel

# ── Define Static Missions ───────────────────────────────────────────────
MISSIONS = {
    "build_mine": {
        "title": "⛏️ Construct a Metal Mine",
        "desc": "Begin extracting metal to fuel your empire.",
        "check": lambda stats: stats.get("metal_mine", 0) >= 1,
        "reward": {"metal": 300, "fuel": 150},
    },
    "train_units": {
        "title": "🪖 Train Your First Troops",
        "desc": "Arm your empire by training at least 5 units.",
        "check": lambda stats: stats.get("total_units", 0) >= 5,
        "reward": {"credits": 100},
    },
    "upgrade_barracks": {
        "title": "🏗️ Upgrade the Barracks",
        "desc": "Level up your Barracks to improve training speed.",
        "check": lambda stats: stats.get("barracks", 0) >= 2,
        "reward": {"metal": 500},
    },
}

# ── Preload Mission Data ───────────────────────────────────────────────
def get_player_mission_stats(pid: str) -> dict:
    stats = {}
    # Buildings
    for bld in ["metal_mine", "barracks"]:
        stats[bld] = get_building_level(pid, bld)

    # Army
    army = load_player_army(pid)
    stats["total_units"] = sum(v for k, v in army.items() if not "_" in k)

    return stats

# ── Missions Command ──────────────────────────────────────────────────
async def missions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    existing = {m["mission_id"]: m for m in load_player_missions(pid)}
    stats = get_player_mission_stats(pid)

    lines = ["<b>📜 Mission Log</b>"]
    buttons = []

    for key, meta in MISSIONS.items():
        completed = existing.get(key, {}).get("completed", False)
        achieved = meta["check"](stats)

        lines.append(f"\n<b>{meta['title']}</b>")
        lines.append(f"{meta['desc']}")

        if completed:
            lines.append("✅ <i>Completed</i>")
        elif achieved:
            reward_str = ", ".join(f"{k.title()}: {v}" for k, v in meta["reward"].items())
            lines.append(f"🎁 <i>Reward Ready</i>: {reward_str}")
            buttons.append([InlineKeyboardButton(f"Claim: {meta['title']}", callback_data=f"CLAIM_MISSION:{key}")])
        else:
            lines.append("⏳ <i>In Progress</i>")

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=markup)
# ── Callback to Claim Mission ─────────────────────────────────────────────
async def claim_mission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)

    mission_id = query.data.split(":", 1)[1]
    mission = MISSIONS.get(mission_id)
    if not mission:
        return await query.edit_message_text("❌ Invalid mission ID.")

    # Check if already completed
    completed_missions = {m["mission_id"]: m for m in load_player_missions(pid)}
    if completed_missions.get(mission_id, {}).get("completed", False):
        return await query.edit_message_text("✅ Mission already claimed.")

    # Check if player qualifies
    stats = get_player_mission_stats(pid)
    if not mission["check"](stats):
        return await query.edit_message_text("⏳ You haven’t completed this mission yet.")

    # Apply reward
    rewards = mission["reward"]
    resources = load_resources(pid)
    for res, amount in rewards.items():
        resources[res] = resources.get(res, 0) + amount
    save_resources(pid, resources)

    # Save mission completion
    save_player_mission(pid, mission_id, True)

    # Confirm to player
    reward_str = ", ".join(f"{k.title()}: {v}" for k, v in rewards.items())
    await query.edit_message_text(
        f"🎉 <b>{mission['title']}</b>\n"
        f"You claimed: {reward_str}\n\n"
        + render_status_panel(pid),
        parse_mode=ParseMode.HTML,
    )
# ── Optional Command to Manually Trigger Missions Menu ────────────────────
async def missions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    await send_mission_list(update, context)

# ── Helper to Add Mission from Admin or Future Triggers ───────────────────
def unlock_mission_for_player(player_id: str, mission_id: str):
    existing = {m["mission_id"]: m for m in load_player_missions(player_id)}
    if mission_id not in existing:
        save_player_mission(player_id, mission_id, False)

# ── Registration Function for Bot Main File ───────────────────────────────
def register_mission_handlers(app):
    from telegram.ext import CommandHandler, CallbackQueryHandler

    app.add_handler(CommandHandler("missions", missions_cmd))
    app.add_handler(CallbackQueryHandler(claim_mission_callback, pattern="^CLAIM:"))
    app.add_handler(CallbackQueryHandler(send_mission_list, pattern="^MISSIONS$"))
