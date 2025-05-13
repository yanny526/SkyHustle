import logging
import os
from logging.handlers import RotatingFileHandler

# … your existing logging setup …

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
from handlers.research    import handler as research_handler, callback_handler as research_callback
from handlers.help        import handler as help_handler

# … army, achievements, chaos, etc. …

# Research background job
from modules.research_manager import complete_research_job

def main():
    sheets_init()
    app = Application.builder().token(BOT_TOKEN).build()

    # Register all your handlers…
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

    # Research
    app.add_handler(research_handler)     # /research
    app.add_handler(research_callback)    # inline “Cancel” buttons

    app.add_handler(help_handler)

    # … other handlers …

    # Slash-command registration including research
    async def set_bot_commands(app):
        commands = [
            # … existing commands …
            BotCommand("research", "🔬 Browse & queue research projects"),
            # …
        ]
        await app.bot.set_my_commands(commands)
    app.post_init = set_bot_commands

    # Unknown fallback
    async def unknown(update, context):
        await update.message.reply_text("❓ Unknown command. Use /help.")
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Schedule background jobs
    register_pre_notice_job(app)
    register_event_job(app)
    app.job_queue.run_repeating(
        complete_research_job,
        interval=60,
        first=0,
        name="research_completion"
    )

    app.run_polling()

if __name__ == "__main__":
    main()
