import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_player_army,
    save_player_army,
    load_resources,
    save_battle_result,
    get_building_level,
)

# ── Player Scanning Placeholder ──────────────────────────────────────────────
def get_nearby_enemies(player_id: str) -> list:
    # In production, replace with smarter filtering
    # Here we simulate fake enemies
    return [
        {"player_id": f"enemy_{i}", "name": f"Enemy_{i}"} for i in range(1, 4)
    ]

# ── Entry Point: /attack ─────────────────────────────────────────────────────
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    enemies = get_nearby_enemies(player_id)

    if not enemies:
        return await update.message.reply_text("No enemies found to attack!")

    buttons = [
        [InlineKeyboardButton(e["name"], callback_data=f"ATTACK:{e['player_id']}")]
        for e in enemies
    ]
    await update.message.reply_text(
        "Select a target:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# ── Core Battle Resolution ───────────────────────────────────────────────────
def calculate_battle_result(attacker_army: dict, defender_army: dict) -> str:
    atk_power = 0
    def_power = 0
    for unit, qty in attacker_army.items():
        if not unit.endswith("_attack") and isinstance(qty, int):
            atk_power += qty * attacker_army.get(f"{unit}_attack", 5)
    for unit, qty in defender_army.items():
        if not unit.endswith("_defense") and isinstance(qty, int):
            def_power += qty * defender_army.get(f"{unit}_defense", 5)
    return "win" if atk_power >= def_power else "lose"

# ── Callback: Resolve attack ─────────────────────────────────────────────────
async def attack_tactic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    attacker_id = str(query.from_user.id)
    defender_id = query.data.split(":")[1]

    attacker_army = load_player_army(attacker_id)
    defender_army = load_player_army(defender_id)

    outcome = calculate_battle_result(attacker_army, defender_army)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_battle_result(
        f"{attacker_id}-{timestamp}",
        attacker_id,
        defender_id,
        tactic="auto",
        outcome=outcome,
        rewards="TBD",
        timestamp=timestamp,
    )

    result_text = (
        f"<b>⚔️ Battle Report</b>\n"
        f"You attacked <code>{defender_id}</code> and <b>{'won' if outcome == 'win' else 'lost'}</b>!"
    )
    await query.edit_message_text(result_text, parse_mode=ParseMode.HTML)
