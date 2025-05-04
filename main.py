# main.py

from config import BOT_TOKEN
from sheets_service import init as sheets_init

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import all handler modules
from handlers.start import handler as start_handler
from handlers.setname import handler as setname_handler
from handlers.menu import handler as menu_handler
from handlers.status import handler as status_handler, callback_handler as status_callback
from handlers.build import handler as build_handler
from handlers.queue import handler as queue_handler
from handlers.train import handler as train_handler
from handlers.attack import handler as attack_handler
from handlers.leaderboard import handler as leaderboard_handler
from handlers.help import handler as help_handler
from handlers.army import handler as army_handler
from handlers.callbacks import handler as menu_callback_handler
from handlers.achievements import handler as achievements_handler
from handlers.announce import handler as announce_handler
from handlers.challenges import daily, weekly
from handlers.whisper import handler as whisper_handler
from handlers.inbox import handler as inbox_handler

def main():
    # 1) Auto-create Sheets & headers
    sheets_init()

    # 2) Build bot
    app = Application.builder().token(BOT_TOKEN).build()

    # 3) Register all command + callback handlers
    app.add_handler(start_handler)
    app.add_handler(setname_handler)
    app.add_handler(menu_handler)
    app.add_handler(status_handler)
    app.add_handler(status_callback)
    app.add_handler(build_handler)
    app.add_handler(queue_handler)
    app.add_handler(train_handler)
    app.add_handler(attack_handler)
    app.add_handler(leaderboard_handler)
    app.add_handler(help_handler)
    app.add_handler(army_handler)
    app.add_handler(achievements_handler)
    app.add_handler(menu_callback_handler)
    app.add_handler(announce_handler)
    app.add_handler(CommandHandler('daily', daily))
    app.add_handler(CommandHandler('weekly', weekly))
    app.add_handler(whisper_handler)
    app.add_handler(inbox_handler)
    
    # 4) Set visible slash commands in Telegram
    async def set_bot_commands(app):
        commands = [
            BotCommand("menu", "📋 Show command menu"),
            BotCommand("status", "📊 View your base status"),
            BotCommand("army", "⚔️ View your army units"),
            BotCommand("queue", "⏳ Pending upgrades"),
            BotCommand("leaderboard", "🏆 Top commanders"),
            BotCommand("daily", "📅 View daily challenges"),
            BotCommand("weekly", "📆 View weekly challenges"),
            BotCommand("achievements", "🏅 View your achievements"),
            BotCommand("announce", "📣 Broadcast an announcement"),
            BotCommand("help", "🆘 Show help and all commands"),
            BotCommand("whisper", "🤫 Send a private message to a commander"),
            BotCommand("inbox",   "📬 View your private messages"),
        ]
        await app.bot.set_my_commands(commands)

    app.post_init = set_bot_commands

    # 5) Fallback for unknown commands
    async def unknown(update, context):
        await update.message.reply_text("❓ Unknown command. Use /help.")
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # 6) Start polling
    app.run_polling()


if __name__ == "__main__":
    main()
