
# pvp_system.py (Part 1 of X)

import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_player_army,
    load_resources,
    save_resources,
    save_battle_result,
)
from utils.ui_helpers import render_status_panel

# ── Tactic Definitions ─────────────────────────────────────────────
TACTICS = {
    "blitz": {
        "name": "⚡ Blitz Attack",
        "desc": "Fast, high-risk attack, chance for big win or loss.",
        "mod": 1.3,
    },
    "balanced": {
        "name": "🛡️ Balanced",
        "desc": "Steady outcome, average performance.",
        "mod": 1.0,
    },
    "defensive": {
        "name": "🧱 Defensive Hold",
        "desc": "Low risk, low reward. Minimized loss.",
        "mod": 0.7,
    },
}

# ── Dummy Opponent Selector (To be replaced with zone scan later) ──
def _choose_random_opponent(current_id: str, all_ids: list[str]) -> str:
    candidates = [pid for pid in all_ids if pid != current_id]
    return random.choice(candidates) if candidates else None

# ── Start Attack ────────────────────────────────────────────────────
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    all_ids = ["1001", "1002", "1003"]  # Replace with player registry later
    target_id = _choose_random_opponent(pid, all_ids)

    if not target_id:
        return await update.message.reply_text("⚠️ No valid targets found.")

    context.user_data["target_id"] = target_id
    buttons = [
        [InlineKeyboardButton(TACTICS[t]["name"], callback_data=f"ATTACK_TACTIC:{t}")]
        for t in TACTICS
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "🎯 <b>Enemy Target Located!</b>
Choose your battle tactic:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )
    # 5. Resolve Combat
    winner_id = pid if outcome == "win" else target_id
    loser_id = target_id if winner_id == pid else pid
    winner_name = query.from_user.first_name if winner_id == pid else get_username(target_id)

    rewards = {
        "metal": random.randint(100, 300),
        "fuel": random.randint(50, 200),
        "crystal": random.randint(20, 100),
        "credits": random.randint(10, 50),
    }

    # Update winner's resources
    res = load_resources(winner_id)
    for k, v in rewards.items():
        res[k] = res.get(k, 0) + v
    save_resources(winner_id, res)

    # Save battle record
    battle_id = f"{pid}-{target_id}-{int(datetime.now().timestamp())}"
    save_battle_result(
        battle_id=battle_id,
        player_id=pid,
        target_id=target_id,
        tactic=tactic,
        outcome=outcome,
        rewards=str(rewards),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 6. Format Battle Report
    reward_text = " | ".join([f"{k.title()}: {v}" for k, v in rewards.items()])
    outcome_text = "🏆 Victory!" if outcome == "win" else "💥 Defeat!"
    report = (
        f"<b>{outcome_text}</b>\n"
        f"Opponent: {get_username(target_id)}\n"
        f"Tactic Used: {tactic.replace('_', ' ').title()}\n"
        f"Rewards: {reward_text}"
    )

    await query.edit_message_text(report, parse_mode=ParseMode.HTML)

def get_username(uid: str) -> str:
    # Optional: Pull from database or use Telegram username cache
    return f"Player {uid}"

# ── Battle Status View ──────────────────────────────────────────────
async def battle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    history = load_battle_history(pid)

    if not history:
        return await update.message.reply_text("🕊️ No battle history yet.")

    lines = ["<b>⚔️ Recent Battles:</b>"]
    for row in history[-5:][::-1]:  # Show last 5
        opp = get_username(row["target_id"])
        outcome = "✅ Won" if row["outcome"] == "win" else "❌ Lost"
        lines.append(f"• vs {opp} — {outcome} [{row['tactic'].replace('_',' ').title()}]")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
# ── Spy Mechanic (Optional PvP Tool) ──────────────────────────────────
async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    if not context.args:
        return await update.message.reply_text("Usage: /spy [player_id]")

    target_id = context.args[0]
    if target_id == pid:
        return await update.message.reply_text("🕵️‍♂️ You can't spy on yourself.")

    enemy_army = load_player_army(target_id)
    if not enemy_army:
        return await update.message.reply_text("Target has no visible army.")

    lines = [f"<b>🕵️ Intel Report on Player {target_id}</b>"]
    for unit, qty in enemy_army.items():
        if isinstance(qty, int):
            lines.append(f"• {unit.replace('_', ' ').title()}: {qty}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# ── Register PvP Command Handlers (To place in main.py) ──────────────
# app.add_handler(CommandHandler("attack", attack))
# app.add_handler(CallbackQueryHandler(attack_tactic_callback, pattern="^ATTACK_TACTIC:"))
# app.add_handler(CallbackQueryHandler(defend_tactic_callback, pattern="^DEFEND_TACTIC:"))
# app.add_handler(CommandHandler("battle_status", battle_status))
# app.add_handler(CommandHandler("spy", spy))

# END OF battle_system.py
