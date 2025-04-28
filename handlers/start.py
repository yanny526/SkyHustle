# handlers/start.py

from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize player profile."""
    telegram_id = update.effective_user.id
    player = db.get_player_data(telegram_id)

    if not player:
        # Create new player
        db.create_player(telegram_id, f"Commander{telegram_id}")
        await update.message.reply_text(
            "🚀 Welcome, new Commander!\n\n"
            "Your SkyHustle profile has been created.\n"
            "Type /help to see what you can do!"
        )
    else:
        await update.message.reply_text(
            "👋 Welcome back, Commander!\n"
            "Type /help to continue your conquest!"
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display help menu."""
    text = (
        "📜 **SkyHustle Commands Guide** 📜\n\n"
        "🛠️ **Account**\n"
        "• /start — Create your SkyHustle profile\n"
        "• /setname <name> — Set a unique Commander name\n"
        "• /status — View your profile and resources\n\n"
        "⛏️ **Resources**\n"
        "• /daily — Claim daily bonus rewards\n"
        "• /mine — Send miners to collect resources\n"
        "• /collect — Gather mined resources\n\n"
        "⚔️ **Army and Combat**\n"
        "• /forge <unit> — Create war units\n"
        "• /army — View your army\n"
        "• /attack <enemy> — Attack another Commander\n"
        "• /shield — Activate protective shield\n\n"
        "🧠 **Research and Technology**\n"
        "• /research <tech> <level> — Upgrade technologies\n"
        "• /tech — View your research levels\n\n"
        "🌍 **Zone Control**\n"
        "• /scan — Discover nearby zones\n"
        "• /claim <zone> — Claim a zone\n"
        "• /zone — View your current zone\n"
        "• /map — View world map\n\n"
        "🛒 **Store and Black Market**\n"
        "• /store — Browse official store\n"
        "• /blackmarket — Browse secret market\n"
        "• /buy <item> — Buy from official store\n"
        "• /blackbuy <item> — Buy from black market\n"
        "• /use <item> — Use an item from your inventory\n\n"
        "🏆 **Missions and Ranking**\n"
        "• /missions — View available missions\n"
        "• /claimmission — Claim mission rewards\n"
        "• /rank — See top players ranking\n\n"
        "🛡️ **Admin Tools** (for authorized staff)\n"
        "• /givegold <player> <amount>\n"
        "• /wipeplayer <player>\n"
        "• /shieldforce <player>\n\n"
        "✨ Keep growing your empire, Commander! ✨"
    )

    await update.message.reply_text(text)
