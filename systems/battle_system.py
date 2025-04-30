import json
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from utils import google_sheets
from systems import army_system
from utils.army_combat import calculate_battle_outcome, calculate_battle_rewards
from utils.ui_helpers import render_status_panel

# Load battle tactics
with open("config/battle_tactics.json", "r") as f:
    BATTLE_TACTICS = json.load(f)


async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack [player_id] — Start an attack and choose your tactic.
    """
    player_id = str(update.effective_user.id)
    args = context.args or []

    if len(args) != 1:
        await update.message.reply_text(
            "🛡️ Usage: /attack [player_id]\n"
            "Example: /attack 12345\n\n"
            + render_status_panel(player_id)
        )
        return

    target_id = args[0]

    # Load armies
    player_army = google_sheets.load_player_army(player_id)
    target_army = google_sheets.load_player_army(target_id)

    if not player_army:
        await update.message.reply_text(
            "❌ Your army is empty. Train units with /train.\n\n"
            + render_status_panel(player_id)
        )
        return

    if not target_army:
        await update.message.reply_text(
            f"❌ Player {target_id} has no army. Unable to attack.\n\n"
            + render_status_panel(player_id)
        )
        return

    # Attacker tactic selection
    buttons = [
        [InlineKeyboardButton(tac["display_name"], callback_data=f"ATTACK_TACTIC:{name}")]
        for name, tac in BATTLE_TACTICS.items()
    ]
    markup = InlineKeyboardMarkup(buttons)

    # Store attack context
    context.user_data["attacking"] = {
        "target_id": target_id,
        "player_army": player_army,
        "target_army": target_army,
    }

    await update.message.reply_text(
        "Choose your battle tactic:", reply_markup=markup
    )


async def attack_tactic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback when attacker chooses a tactic; then prompt defender counter-tactic.
    """
    query = update.callback_query
    await query.answer()

    attack_data = context.user_data.get("attacking")
    if not attack_data:
        await query.edit_message_text("❌ Attack data lost. Please retry /attack.")
        return

    tactic = query.data.split("\":\", 1)[1]
    attack_data["attacker_tactic"] = tactic

    # Defender counter-tactic selection
    buttons = [
        [InlineKeyboardButton(tac["display_name"], callback_data=f"DEFEND_TACTIC:{name}")]
        for name, tac in BATTLE_TACTICS.items()
    ]
    markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        "Choose defender counter-tactic:", reply_markup=markup
    )


async def defend_tactic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback when defender chooses counter-tactic; resolve battle.
    """
    query = update.callback_query
    await query.answer()

    attack_data = context.user_data.pop("attacking", None)
    if not attack_data:
        await query.edit_message_text("❌ Attack data lost. Please retry /attack.")
        return

    player_id = str(query.from_user.id)
    attacker_tactic = attack_data.get("attacker_tactic", "")
    defender_tactic = query.data.split("\":\", 1)[1]
    target_id = attack_data["target_id"]
    player_army = attack_data["player_army"]
    target_army = attack_data["target_army"]

    # Perform combat (only attacker tactic used currently)
    outcome, battle_log = calculate_battle_outcome(
        player_army, target_army, attacker_tactic
    )
    rewards = calculate_battle_rewards(outcome, player_army, target_army)

    # Record battle
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    google_sheets.save_battle_result(
        player_id, target_id, outcome, rewards, now_str, battle_log
    )

    atk_name = BATTLE_TACTICS.get(attacker_tactic, {}).get("display_name", attacker_tactic)
    def_name = BATTLE_TACTICS.get(defender_tactic, {}).get("display_name", defender_tactic)
    msg = (
        f"⚔️ Battle vs {target_id} — {outcome}!\n"
        f"Attacker Tactic: {atk_name}\n"
        f"Defender Counter: {def_name}\n\n"
        f"🎖️ Rewards: {rewards}\n\n"
        f"📜 Battle Log:\n{battle_log}\n\n"
        + render_status_panel(player_id)
    )
    await query.edit_message_text(msg)


async def battle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /battlestatus — Show past battle outcomes.
    """
    player_id = str(update.effective_user.id)
    history = google_sheets.load_battle_history(player_id)

    if not history:
        await update.message.reply_text(
            "❌ You have no battle history.\n\n"
            + render_status_panel(player_id)
        )
        return

    lines = [
        f"• [{row['date']}] vs {row['target_id']} — {row['outcome']} | Rewards: {row['rewards']}"
        for row in history
    ]
    msg = (
        "🛡️ Battle History:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)


async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /spy [player_id] — Reveal another player's army.
    """
    player_id = str(update.effective_user.id)
    args = context.args or []

    if len(args) != 1:
        await update.message.reply_text(
            "🛡️ Usage: /spy [player_id]\n"
            "Example: /spy 12345\n\n"
            + render_status_panel(player_id)
        )
        return

    target_id = args[0]
    target_army = google_sheets.load_player_army(target_id)

    if not target_army:
        await update.message.reply_text(
            f"❌ Player {target_id} has no army.\n\n"
            + render_status_panel(player_id)
        )
        return

    lines = [f"🔹 {unit.title()}: {qty} unit(s)" for unit, qty in target_army.items()]
    report = (
        "🕵️ Spy Report:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(report)


def register_callbacks(app):
    app.add_handler(
        CallbackQueryHandler(attack_tactic_callback, pattern="^ATTACK_TACTIC:")
    )
    app.add_handler(
        CallbackQueryHandler(defend_tactic_callback, pattern="^DEFEND_TACTIC:")
    )
