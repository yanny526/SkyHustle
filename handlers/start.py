from telegram import Update
from telegram.ext import ContextTypes
import utils.db as db

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    created = db.create_player(user.id, user.first_name)
    
    if created:
        await update.message.reply_text(
            "🌌 **Welcome, Commander!** 🌌\n\n"
            "A new empire is born from the ashes...\n"
            "Type /help to begin your conquest! 🏰"
        )
    else:
        await update.message.reply_text(
            "🏰 **Welcome back, Commander!**\n\n"
            "Your empire awaits your command. ⚔️"
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧭 **SkyHustle Command Guide** 🧭\n\n"
        "🏰 *Empire Management*\n"
        "`/start` - Begin your empire\n"
        "`/status` - View your empire's strength\n"
        "`/name <new_name>` - Change your Commander name (future)\n\n"
        "⛏️ *Resource Commands*\n"
        "`/daily` - Claim daily resource rewards\n"
        "`/mine` - Start mining expedition\n"
        "`/collect` - Collect mined resources\n"
        "`/resources` - View current resources (future)\n\n"
        "🛡️ *Military Commands*\n"
        "`/forge <unit> <amount>` - Train army units (future)\n"
        "`/army` - View your army (future)\n"
        "`/use <item>` - Use special items (future)\n\n"
        "🌍 *Territory Commands*\n"
        "`/claim` - Claim a zone (future)\n"
        "`/map` - View the world map (future)\n"
        "`/zone` - View your zone (future)\n\n"
        "⚔️ *Warfare Commands*\n"
        "`/scan` - Scan nearby territories\n"
        "`/attack <player>` - Attack a rival Commander\n\n"
        "🧬 *Research & Market*\n"
        "`/research <tech> <level>` - Research technologies (future)\n"
        "`/blackmarket` - Visit the secret Black Market (future)\n"
        "`/buy <item>` - Buy a Black Market item (future)\n\n"
        "🎯 *Missions & Rankings*\n"
        "`/missions` - Complete missions (future)\n"
        "`/rank` - View your rank\n"
        "`/leaderboard` - View top players\n\n"
        "⚙️ *Admin Commands (Dev Only)*\n"
        "`/admin give <player> <resource> <amount>`\n"
        "`/admin wipe <player>`\n"
        "`/debug` - Testing functions\n\n"
        "🏆 _Conquer. Expand. Dominate._ 🏆"
        , parse_mode='Markdown'
    )
