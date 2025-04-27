from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db
import random
import datetime

# ------------------- ATTACK SYSTEM -------------------

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attack another player by Telegram ID."""
    attacker_id = update.effective_user.id

    if len(context.args) != 1:
        return await update.message.reply_text("⚔️ Usage: /attack <enemy_telegram_id>")

    target_id = context.args[0]

    if str(attacker_id) == str(target_id):
        return await update.message.reply_text("⚔️ You cannot attack yourself, Commander!")

    attacker_data = db.get_player_data(attacker_id)
    target_data = db.get_player_data(target_id)

    if not attacker_data or not target_data:
        return await update.message.reply_text("⚔️ Enemy not found on the battlefield!")

    if target_data['ShieldActive'] == "Yes":
        return await update.message.reply_text("🛡️ The enemy is under Shield protection! Attack failed.")

    attacker_army = db.get_army(attacker_id)
    target_army = db.get_army(target_id)

    if not attacker_army or not target_army:
        return await update.message.reply_text("⚔️ Armies not found for both sides!")

    # Calculate Army Strengths
    attacker_strength = (
        attacker_army['Scouts'] * 1 +
        attacker_army['Soldiers'] * 2 +
        attacker_army['Tanks'] * 5 +
        attacker_army['Drones'] * 3
    )

    defender_strength = (
        target_army['Scouts'] * 1 +
        target_army['Soldiers'] * 2 +
        target_army['Tanks'] * 5 +
        target_army['Drones'] * 3
    )

    # Random slight luck factor
    attacker_strength += random.randint(-5, 5)
    defender_strength += random.randint(-5, 5)

    if attacker_strength <= 0:
        return await update.message.reply_text("⚔️ You have no army to attack with!")
    if defender_strength <= 0:
        return await update.message.reply_text("⚔️ Enemy has no army to defend with!")

    result_text = "⚔️ **Battle Report!** ⚔️\n\n"

    if attacker_strength > defender_strength:
        # Attacker wins
        stolen_gold = min(200, target_data['Gold'])
        db.update_player_resources(attacker_id, gold_delta=stolen_gold)
        db.update_player_resources(target_id, gold_delta=-stolen_gold)

        result_text += (
            f"🏴‍☠️ Victory! You defeated the enemy!\n"
            f"💰 Resources captured: +{stolen_gold} Gold\n"
            f"🏴‍☠️ Casualties suffered: light\n"
        )
    else:
        # Defender wins
        result_text += (
            f"🛡️ Defeat! The enemy defended successfully.\n"
            f"🏴‍☠️ Casualties suffered: heavy\n"
        )

    result_text += "\n⚔️ Glory to the bold, Commander!"

    await update.message.reply_text(result_text)
# ------------------- SHIELD SYSTEM -------------------

async def shield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate a protective shield for 24 hours."""
    telegram_id = update.effective_user.id
    player_data = db.get_player_data(telegram_id)

    if not player_data:
        return await update.message.reply_text("🛡️ You must /start first!")

    if player_data['ShieldActive'] == "Yes":
        return await update.message.reply_text("🛡️ You already have a shield active!")

    # Update player profile to activate shield
    db.player_profile.update_cell(db.find_player(telegram_id), 9, "Yes")  # ShieldActive column

    await update.message.reply_text(
        "🛡️ Shield activated! You are protected from attacks for the next 24 hours.\n"
        "Stay safe, Commander!"
    )


