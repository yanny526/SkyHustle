import logging
import os
from logging.handlers import RotatingFileHandler

# ─── Logging Configuration ───────────────────────────────────────────────────
LOG_LEVEL   = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE    = os.getenv('LOG_FILE', 'bot.log')
MAX_BYTES   = int(os.getenv('LOG_MAX_BYTES', 5 * 1024 * 1024))
BACKUP_COUNT= int(os.getenv('LOG_BACKUP_COUNT', 3))

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
formatter   = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

from config import BOT_TOKEN
from sheets_service import init as sheets_init

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Core command handlers
from handlers.start       import handler as start_handler
from handlers.setname     import handler as setname_handler
from handlers.status      import handler as status_handler, callback_handler as status_callback
from handlers.build       import handler as build_handler
from handlers.queue       import handler as queue_handler
from handlers.train       import handler as train_handler
from handlers.attack      import handler as attack_handler
from handlers.reports     import handler as reports_handler, callback_handler as reports_callback
from handlers.leaderboard import handler as leaderboard_handler, callback_handler as leaderboard_callback
from handlers.research    import handler as research_handler
from handlers.help        import handler as help_handler

# Army commands & callbacks
from handlers.army import (
    handler           as army_handler,
    callback_handler  as army_callback,
    attack_callback   as army_attack_callback,
    build_callback    as army_build_callback,
)

# Other game features
from handlers.achievements import handler as achievements_handler
from handlers.announce     import handler as announce_handler
from handlers.challenges   import daily, weekly
from handlers.whisper      import handler as whisper_handler
from handlers.inbox        import handler as inbox_handler

# Chaos system
from handlers.chaos            import handler as chaos_handler
from handlers.chaos_test       import handler as chaos_test_handler
from handlers.chaos_pre_notice import register_pre_notice_job
from handlers.chaos_event      import register_event_job

# Research system: background job only
from modules.research_manager import complete_research_job

def main():
    # 1) Initialize Sheets
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

    app.add_handler(reports_handler)
    app.add_handler(reports_callback)

    app.add_handler(leaderboard_handler)
    app.add_handler(leaderboard_callback)

    app.add_handler(research_handler)       # /research
    app.add_handler(help_handler)

    # Army and its callbacks
    app.add_handler(army_handler)
    app.add_handler(army_callback)
    app.add_handler(army_attack_callback)
    app.add_handler(army_build_callback)

    # Other core commands
    app.add_handler(achievements_handler)
    app.add_handler(announce_handler)
    app.add_handler(CommandHandler("daily",  daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(whisper_handler)
    app.add_handler(inbox_handler)

    # Chaos commands
    app.add_handler(chaos_handler)
    app.add_handler(chaos_test_handler)

    # 4) Slash-command registration
    async def set_bot_commands(app):
        commands = [
            BotCommand("status",      "📊 View your base status"),
            BotCommand("army",        "⚔️ View your army units"),
            BotCommand("queue",       "⏳ View pending upgrades"),
            BotCommand("leaderboard", "🏆 See top commanders"),
            BotCommand("daily",       "📅 View daily challenges"),
            BotCommand("weekly",      "📆 View weekly challenges"),
            BotCommand("achievements","🏅 View your achievements"),
            BotCommand("announce",    "📣 [Admin] Broadcast an announcement"),
            BotCommand("chaos",       "🌪️ Preview Random Chaos Storms"),
            BotCommand("chaos_test",  "🧪 [Admin] Test Chaos Storm"),
            BotCommand("research",    "🔬 Browse and queue research projects"),
            BotCommand("reports",     "🗒️ View pending operations"),
            BotCommand("whisper",     "🤫 Send a private message"),
            BotCommand("inbox",       "📬 View your private messages"),
            BotCommand("help",        "🆘 Show help & all commands"),
        ]
        await app.bot.set_my_commands(commands)
    app.post_init = set_bot_commands

    # 5) Unknown-command fallback
    async def unknown(update, context):
        await update.message.reply_text("❓ Unknown command. Use /help.")
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # 6) Schedule Chaos pre-notice checker
    register_pre_notice_job(app)

    # 7) Schedule weekly Chaos Storm
    register_event_job(app)

    # 8) Schedule research completion background job
    app.job_queue.run_repeating(
        complete_research_job,
        interval=60,
        first=0,
        name="research_completion"
    )

    # 9) Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
