# main.py

from config import BOT_TOKEN
from sheets_service import init as sheets_init

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import time as dtime

# Handlers
from handlers.start import handler as start_handler
from handlers.setname import handler as setname_handler
from handlers.status import handler as status_handler, callback_handler as status_callback
from handlers.build import handler as build_handler
from handlers.queue import handler as queue_handler
from handlers.train import handler as train_handler
from handlers.attack import handler as attack_handler
from handlers.reports import handler as reports_handler, callback_handler as reports_callback
from handlers.leaderboard import handler as leaderboard_handler, callback_handler as leaderboard_callback
from handlers.help import handler as help_handler

# ←── Updated imports here to pull in all army callbacks
from handlers.army import (
    handler           as army_handler,
    callback_handler  as army_callback,
    attack_callback   as army_attack_callback,
    build_callback    as army_build_callback,
)

from handlers.achievements import handler as achievements_handler
from handlers.announce import handler as announce_handler
from handlers.challenges import daily, weekly
from handlers.whisper import handler as whisper_handler
from handlers.inbox import handler as inbox_handler

# ←── Import AI handlers here
from handlers.ai_commands import handler as ai_commands_handler
from handlers.ai_commands import callback_handler as ai_callback_handler

def main():
    # 1) Initialize Sheets & headers
    sheets_init()

    # 2) Build bot
    app = Application.builder().token(BOT_TOKEN).build()

    # 3) Register handlers
    app.add_handler(start_handler)
    app.add_handler(setname_handler)
    app.add_handler(status_handler)
    app.add_handler(status_callback)
    app.add_handler(build_handler)
    app.add_handler(queue_handler)
    app.add_handler(train_handler)
    app.add_handler(attack_handler)
    app.add_handler(reports_handler)     # /reports for pending
    app.add_handler(reports_callback)    # 📜 View Pending button
    app.add_handler(leaderboard_handler)
    app.add_handler(leaderboard_callback)
    app.add_handler(help_handler)

    # ←── Register army and its three callbacks
    app.add_handler(army_handler)
    app.add_handler(army_callback)
    app.add_handler(army_attack_callback)
    app.add_handler(army_build_callback)

    app.add_handler(achievements_handler)
    app.add_handler(announce_handler)
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(whisper_handler)
    app.add_handler(inbox_handler)

    # ←── Register AI handlers here
    app.add_handler(ai_commands_handler)
    app.add_handler(ai_callback_handler)

    # 4) Slash commands
    async def set_bot_commands(app):
        commands = [
            BotCommand("status",       "📊 View your base status"),
            BotCommand("army",         "⚔️ View your army units"),
            BotCommand("queue",        "⏳ View pending upgrades"),
            BotCommand("leaderboard",  "🏆 See top commanders"),
            BotCommand("daily",        "📅 View daily challenges"),
            BotCommand("weekly",       "📆 View weekly challenges"),
            BotCommand("achievements", "🏅 View your achievements"),
            BotCommand("announce",     "📣 [Admin] Broadcast an announcement"),
            BotCommand("chaos",        "🌪️ Preview Random Chaos Storms"),
            BotCommand("chaos_test",   "🧪 [Admin] Test Chaos Storm"),
            BotCommand("reports",      "🗒️ View pending operations"),
            BotCommand("whisper",      "🤫 Send a private message"),
            BotCommand("inbox",        "📬 View your private messages"),
            BotCommand("help",         "🆘 Show help & all commands"),
            BotCommand("ai",           "🤖 Challenge AI opponents")  # <- Added AI command
        ]
        await app.bot.set_my_commands(commands)

    app.post_init = set_bot_commands

    # 5) Unknown-command fallback
    async def unknown(update, context):
        await update.message.reply_text("❓ Unknown command. Use /help.")
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # 6) Start polling
    app.run_polling()


if __name__ == "__main__":
    main()
