#!/usr/bin/env python3
import os
import base64
import logging
from telegram.ext import Application
from config import BOT_TOKEN

# —————————————————————————————————————————
# Decode your service account JSON from BASE64_CREDS
# into SERVICE_ACCOUNT_INFO so sheets_service.py can load it.
if not os.getenv("SERVICE_ACCOUNT_INFO"):
    b64 = os.getenv("BASE64_CREDS")
    if b64:
        try:
            decoded = base64.b64decode(b64).decode()
            os.environ["SERVICE_ACCOUNT_INFO"] = decoded
        except Exception as e:
            logging.error(f"Failed to decode BASE64_CREDS: {e}")
# —————————————————————————————————————————

from sheets_service import init as sheets_init

# Import every handler so we can register them below
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
    # Turn on logging (so if anything else blows up, it'll end up in your Render logs)
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # 1) Ensure your Sheets tabs & headers exist
    sheets_init()

    # 2) Build the Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()

    # 3) Register all the commands
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
