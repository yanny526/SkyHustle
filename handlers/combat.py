#   handlers/combat.py
#   Handles the ,attack command

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from core import player  #   Import player-related functions
from core import combat  #   Import combat-related functions


async def attack_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,attack <target> command.

    Initiates an attack on another player.
    Calculates the outcome of the attack and updates player data.
    """

    if not args:
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,attack <target>`"
        )
        return

    target_name = args[0].lower()
    attacker = player.find_or_create_player(update.message.chat_id)
    defender = player.find_player_by_name(target_name)

    if not defender:
        await update.message.reply_text(
            f"🎯 Commander '{target_name}' not found in this sector."
        )
        return

    if attacker.name == defender.name:
        await update.message.reply_text("⚔️ You cannot attack yourself, Commander.")
        return

    #   Placeholder for shield check (implement later)
    #   if defender.shield_until and defender.shield_until > datetime.now():
    #       await update.message.reply_text(f"🛡️ Commander {defender.name} is currently shielded.")
    #       return

    damage = combat.calculate_attack_damage(attacker, defender)
    combat.apply_attack_results(attacker, defender, damage)

    #   Update wins/losses
    if damage > 0:  #   Simplified win/loss condition
        attacker.wins += 1
        defender.losses += 1
        await update.message.reply_text(
            f"💥 Battle Report: You inflicted significant damage! Victory is yours!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        attacker.losses += 1
        defender.wins += 1
        await update.message.reply_text(
            f"💥 Battle Report: You suffered heavy losses! Defeat!",
            parse_mode=ParseMode.MARKDOWN,
        )

    player.save_player(attacker)
    player.save_player(defender)
