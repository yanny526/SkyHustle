#!/usr/bin/env python3
import logging
from telegram.ext import Application
from config import BOT_TOKEN
from sheets_service import init as sheets_init

# Import every handler
from handlers.start        import handler as start_handler
from handlers.setname      import handler as setname_handler
from handlers.menu         import handler as menu_handler
from handlers.help         import handler as help_handler
from handlers.status       import handler as status_handler
from handlers.build        import handler as build_handler
from handlers.queue        import handler as queue_handler
from handlers.train        import handler as train_handler
from handlers.attack       import handler as attack_handler
from handlers.army         import handler as army_handler
from handlers.leaderboard  import handler as leaderboard_handler

def main():
    # Enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # 1) Ensure all Sheets tabs & headers exist
    sheets_init()

    # 2) Build the Telegram application
    app = Application.builder().token(BOT_TOKEN).build()

    # 3) Register all command handlers
    app.add_handler(start_handler)        # /start
    app.add_handler(setname_handler)     # /setname
    app.add_handler(menu_handler)        # /menu
    app.add_handler(help_handler)        # /help
    app.add_handler(status_handler)      # /status
    app.add_handler(build_handler)       # /build
    app.add_handler(queue_handler)       # /queue
    app.add_handler(train_handler)       # /train
    app.add_handler(attack_handler)      # /attack
    app.add_handler(army_handler)        # /army
    app.add_handler(leaderboard_handler) # /leaderboard

    # 4) Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
