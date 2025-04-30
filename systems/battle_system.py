import json
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils import google_sheets
from systems import army_system
from utils.army_combat import calculate_battle_outcome, calculate_battle_rewards
from utils.ui_helpers import render_status_panel

# Load battle tactics
with open("config/battle_tactics.json", "r") as f:
    BATTLE_TACTICS = json.load(f)


# ── Attack another player ─────────────────────────────────────────────────────
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /attack [player_id] — Initiate an attack with tactic selection.
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

    # Load both armies
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

    # Tactic Selection UI
    buttons = [
        [InlineKeyboardButton(tac["display_name"], callback_data=f"TACTIC:{name}")]
        for name, tac in BATTLE_TACTICS.items()
    ]
    markup = InlineKeyboardMarkup(buttons)

    # Store attack context for callback
    context.user_data["attack_data"] = {
        "target_id": target_id,
        "player_army": player_army,
        "target_army": target_army,
    }

    await update.message.reply_text(
        "Choose your battle tactic:", reply_markup=markup
    )


# ── Tactic callback ─────────────────────────────────────────────────────────
async def tactic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles tactic choice, performs combat, shows results.
    """
    query = update.callback_query
    await query.answer()

    player_id = str(query.from_user.id)
    data = context.user_data.pop("attack_data", None)
    if not data:
        return await query.edit_message_text(
            "⚠️ Attack context lost. Please try /attack again.", parse_mode=None
        )

    tactic_key = query.data.split("":", 1)[1]
    tactic = BATTLE_TACTICS.get(tactic_key, {})

    player_army = data["player_army"]
    target_army = data["target_army"]
    target_id = data["target_id"]

    # Perform combat (ignoring tactics for now)
    outcome, battle_log = calculate_battle_outcome(player_army, target_army)
    rewards = calculate_battle_rewards(outcome, player_army, target_army)

    # Record battle
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    google_sheets.save_battle_result(
        player_id, target_id, outcome, rewards, now_str, battle_log
    )

    # Display results
    msg = (
        f"⚔️ Battle vs {target_id} — {outcome}!\n"
        f"Tactic: {tactic.get('display_name', tactic_key)}\n\n"
        f"🎖️ Rewards: {rewards}\n\n"
        f"📜 Battle Log:\n{battle_log}\n\n"
        + render_status_panel(player_id)
    )
    await query.edit_message_text(msg)


# ── View battle history ───────────────────────────────────────────────────────
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


# ── Spy another player's army ────────────────────────────────────────────────
async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /spy [player_id] — Reveal another player's army composition.
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
            f"❌ Player {target_id} has no army to spy on.\n\n"
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
