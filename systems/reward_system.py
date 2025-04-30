# reward_system.py (Part 1 of X)

import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    save_resources,
    load_player_missions,
    save_player_mission,
)
from utils.ui_helpers import render_status_panel

# Daily login tracker (in-memory for now, will switch to Sheets if needed)
daily_login_tracker = {}

# Daily Reward Configuration
DAILY_REWARD = {
    1: {"metal": 200, "fuel": 100},
    2: {"metal": 300, "fuel": 150, "crystal": 25},
    3: {"metal": 500, "fuel": 300, "crystal": 50, "credits": 25},
}

# ── Daily Reward Logic ───────────────────────────────────────────────────────

def get_day_streak(player_id: str) -> int:
    last_login = daily_login_tracker.get(player_id)
    if not last_login:
        return 1
    delta = datetime.datetime.now().date() - last_login.date()
    return 1 if delta.days > 1 else min(3, (last_login.day % 3) + 1)

def record_login(player_id: str):
    daily_login_tracker[player_id] = datetime.datetime.now()
# reward_system.py (Part 2 of X)

async def claim_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    streak = get_day_streak(player_id)
    reward = DAILY_REWARD.get(streak, DAILY_REWARD[1])

    resources = load_resources(player_id)
    for res, amt in reward.items():
        resources[res] = resources.get(res, 0) + amt
    save_resources(player_id, resources)
    record_login(player_id)

    reward_text = "\n".join([f"• {res.title()}: +{amt}" for res, amt in reward.items()])
    await update.message.reply_text(
        f"🎁 <b>Daily Reward (Day {streak}) Claimed!</b>\n{reward_text}\n\n"
        + render_status_panel(player_id),
        parse_mode=ParseMode.HTML,
    )


# ── Mission Reward Claim ──────────────────────────────────────────────────────

def get_mission_rewards(player_id: str):
    missions = load_player_missions(player_id)
    return {m["mission_id"]: m["completed"] for m in missions}

async def claim_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args
    if not args:
        return await update.message.reply_text("Usage: /claimmission [mission_id]")

    mission_id = args[0]
    from systems.mission_system import MISSIONS

    if mission_id not in MISSIONS:
        return await update.message.reply_text("❌ Invalid mission ID.")

    rewards_claimed = get_mission_rewards(player_id)
    if not rewards_claimed.get(mission_id):
        return await update.message.reply_text("❌ Mission not completed or already claimed.")

    reward = MISSIONS[mission_id]["reward"]
    resources = load_resources(player_id)
    for res, amt in reward.items():
        resources[res] = resources.get(res, 0) + amt
    save_resources(player_id, resources)

    save_player_mission(player_id, mission_id, False)  # Mark as claimed

    reward_str = "\n".join(f"• {k.title()}: +{v}" for k, v in reward.items())
    await update.message.reply_text(
        f"✅ <b>Mission Reward Claimed</b>\n{reward_str}",
        parse_mode=ParseMode.HTML
    )
# reward_system.py (Part 3 of X)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def show_rewards_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎁 Claim Daily", callback_data="REWARD:DAILY")],
        [InlineKeyboardButton("📜 Claim Mission Reward", callback_data="REWARD:MISSION")],
        [InlineKeyboardButton("« Back to Main Menu", callback_data="MAIN_MENU")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎉 <b>Rewards Center</b>\nChoose an option below:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )


async def rewards_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)

    if query.data == "REWARD:DAILY":
        streak = get_day_streak(pid)
        reward = DAILY_REWARD.get(streak, DAILY_REWARD[1])
        resources = load_resources(pid)
        for res, amt in reward.items():
            resources[res] = resources.get(res, 0) + amt
        save_resources(pid, resources)
        record_login(pid)

        reward_text = "\n".join([f"• {res.title()}: +{amt}" for res, amt in reward.items()])
        return await query.edit_message_text(
            f"🎁 <b>Daily Reward (Day {streak}) Claimed!</b>\n{reward_text}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="REWARDS_MENU")]
            ])
        )

    elif query.data == "REWARD:MISSION":
        return await query.edit_message_text(
            "ℹ️ Use <code>/claimmission [id]</code> to claim completed missions.\nExample: /claimmission build_mine",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="REWARDS_MENU")]
            ])
        )

    elif query.data == "REWARDS_MENU":
        return await show_rewards_menu(update, context)
