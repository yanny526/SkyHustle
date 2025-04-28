# handlers/ranking.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Top 5 strongest players."""
    all_players = db.army.get_all_values()[1:]  # Skip header

    if not all_players:
        return await update.message.reply_text("🏆 *No Commanders found yet!*", parse_mode="Markdown")

    rankings = []

    for player in all_players:
        try:
            telegram_id = player[0]
            scouts = int(player[1])
            soldiers = int(player[2])
            tanks = int(player[3])
            drones = int(player[4])

            army_power = (scouts * 1) + (soldiers * 2) + (tanks * 5) + (drones * 3)

            player_data = db.get_player_data(telegram_id)
            commander_name = player_data["PlayerName"] if player_data else f"Unknown({telegram_id})"

            rankings.append((commander_name, army_power))
        except Exception as e:
            print(f"Error processing player army: {e}")

    # Sort by army power, descending
    rankings.sort(key=lambda x: x[1], reverse=True)

    rank_text = "🏆 *SkyHustle Top 5 Commanders* 🏆\n\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for idx, (name, power) in enumerate(rankings[:5]):
        rank_text += f"{medals[idx]} *{name}* — 💥 Army Power: `{power}`\n"

    rank_text += "\n⚔️ _Train harder, Commander! Victory awaits!_"

    await update.message.reply_text(rank_text, parse_mode="Markdown")
