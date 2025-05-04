# main.py

from config import BOT_TOKEN
from sheets_service import init as sheets_init

from datetime import time as dtime
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
from handlers.achievements import handler as achievements_handler
from handlers.announce import handler as announce_handler
from handlers.challenges import daily, weekly
from handlers.whisper import handler as whisper_handler
from handlers.inbox import handler as inbox_handler

# ⚡ Chaos Storms
from handlers.chaos import handler as chaos_handler
from handlers.chaos_event import chaos_event_job


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
    app.add_handler(announce_handler)
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(whisper_handler)
    app.add_handler(inbox_handler)
    app.add_handler(chaos_handler)  # ➡️ Preview Random Chaos Storms

    # 4) Set visible slash commands in Telegram
    async def set_bot_commands(app):
        commands = [
            BotCommand("menu",        "📋 Show command menu"),
            BotCommand("status",      "📊 View your base status"),
            BotCommand("army",        "⚔️ View your army units"),
            BotCommand("queue",       "⏳ View pending upgrades"),
            BotCommand("leaderboard", "🏆 See top commanders"),
            BotCommand("daily",       "📅 View daily challenges"),
            BotCommand("weekly",      "📆 View weekly challenges"),
            BotCommand("achievements","🏅 View your achievements"),
            BotCommand("announce",    "📣 Broadcast an announcement"),
            BotCommand("chaos",       "🌪️ Preview Random Chaos Storms"),
            BotCommand("whisper",     "🤫 Send a private message"),
            BotCommand("inbox",       "📬 View your private messages"),
            BotCommand("help",        "🆘 Show help & all commands"),
        ]
        await app.bot.set_my_commands(commands)

    app.post_init = set_bot_commands

    # 5) Fallback for unknown commands
    async def unknown(update, context):
        await update.message.reply_text("❓ Unknown command. Use /help.")
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # 6) Schedule weekly Chaos Storm (Mon @ 09:00 UTC)
    app.job_queue.run_weekly(
        chaos_event_job,
        day_of_week="mon",
        time=dtime(hour=9, minute=0),
        name="weekly_chaos_storm"
    )

    # 7) Start polling
    app.run_polling()


if __name__ == "__main__":
    main()
