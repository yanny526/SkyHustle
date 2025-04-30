# battle_system.py

import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_player_army,
    save_battle_result,
    load_resources,
    save_resources,
)

# ── Dummy Scan Logic: Replace with real scouting system later ──
def get_nearby_enemies(player_id: str) -> list:
    return [
        {"player_id": f"enemy_{i}", "name": f"Enemy {i}"} for i in range(1, 4)
    ]

# ── /attack Command: Show enemy list ──
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    enemies = get_nearby_enemies(player_id)

    if not enemies:
        return await update.message.reply_text("No enemies found nearby.")

    buttons = [
        [InlineKeyboardButton(e["name"], callback_data=f"ATTACK:{e['player_id']}")]
        for e in enemies
    ]
    await update.message.reply_text(
        "Choose a target to attack:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
# ── Battle Resolution ──

def calculate_battle_result(attacker_army: dict, defender_army: dict) -> str:
    atk_power = 0
    def_power = 0

    for unit, qty in attacker_army.items():
        if not unit.endswith("_attack") and isinstance(qty, int):
            unit_attack = attacker_army.get(f"{unit}_attack", 5)
            atk_power += qty * unit_attack

    for unit, qty in defender_army.items():
        if not unit.endswith("_defense") and isinstance(qty, int):
            unit_defense = defender_army.get(f"{unit}_defense", 5)
            def_power += qty * unit_defense

    return "win" if atk_power >= def_power else "lose"
# ── Callback: Resolve Attack ──

import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.google_sheets import (
    load_player_army,
    save_battle_result
)

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
        battle_id=f"{attacker_id}-{timestamp}",
        attacker_id=attacker_id,
        defender_id=defender_id,
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
# ── Registration Helpers (to be placed in your handler setup file, e.g., main.py) ──

from telegram.ext import CommandHandler, CallbackQueryHandler
from systems import battle_system

def register_battle_handlers(app):
    app.add_handler(CommandHandler("attack", battle_system.attack))
    app.add_handler(CallbackQueryHandler(battle_system.attack_tactic_callback, pattern="^ATTACK:"))
