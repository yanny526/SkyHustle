# main.py

from config import BOT_TOKEN
from sheets_service import init as sheets_init

from handlers.start import handler as start_handler
from handlers.setname import handler as setname_handler
from handlers.menu import handler as menu_handler
from handlers.status import handler as status_handler
from handlers.build import handler as build_handler
from handlers.queue import handler as queue_handler
from handlers.train import handler as train_handler
from handlers.attack import handler as attack_handler
from handlers.leaderboard import handler as leaderboard_handler

from telegram.ext import Application

def main():
    # 1. Ensure all Sheets tabs & headers exist
    sheets_init()

    # 2. Build the Telegram bot application
    app = Application.builder().token(BOT_TOKEN).build()

    # 3. Register your command handlers
    app.add_handler(start_handler)
    app.add_handler(setname_handler)
    app.add_handler(menu_handler)
    app.add_handler(status_handler)
    app.add_handler(build_handler)
    app.add_handler(queue_handler)
    app.add_handler(train_handler)
    app.add_handler(attack_handler)
    app.add_handler(leaderboard_handler)

    # 4. Start polling (blocks until interrupted)
    app.run_polling()

if __name__ == "__main__":
    main()
