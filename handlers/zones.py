#   handlers/zones.py
#   Handles zone-related commands: ,claim and ,map

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from core import player  #   Import player-related functions
from core import zones  #   Import zone-related functions
import json  #   For loading zone data (if needed)

#   Placeholder for zone data (replace with actual data loading)
ZONE_DATA = {
    "zone1": "The Crystal Mines",
    "zone2": "The Iron Wastes",
    "zone3": "The Emerald Fields",
}  #   In the future, load this from a file (e.g., zones.json)


async def claim_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]
):
    """
    Handles the ,claim <zone_name> command.

    Allows a player to claim a zone if it's not already claimed.
    """

    if not args:
        await update.message.reply_text(
            "⚠️ Incorrect command format. Usage: `,claim <zone_name>`"
        )
        return

    zone_name = args[0].lower()
    if zone_name not in ZONE_DATA:
        await update.message.reply_text("🗺️ Invalid zone name.")
        return

    current_player = player.find_or_create_player(update.message.chat_id)
    all_players = player.get_all_players()  #   Get all players

    owner = zones.find_zone_owner(zone_name, all_players)
    if owner:
        await update.message.reply_text(
            f"🚩 This zone is already under the control of Commander {owner.name}."
        )
        return

    current_player.zone = zone_name
    player.save_player(current_player)

    await update.message.reply_text(
        f"🚩 Commander, you have successfully claimed *{ZONE_DATA[zone_name]}*!",
        parse_mode=ParseMode.MARKDOWN,
    )


async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the ,map command.

    Displays the current ownership of all zones.
    """

    all_players = player.get_all_players()
    map_message = "🗺️ *Hyperion Zone Control* 🗺️\n\n"

    for zone_id, zone_name in ZONE_DATA.items():
        owner = zones.find_zone_owner(zone_id, all_players)
        owner_name = owner.name if owner else "Unclaimed"
        map_message += f"- *{zone_name}*: {owner_name}\n"

    await update.message.reply_text(map_message, parse_mode=ParseMode.MARKDOWN)
