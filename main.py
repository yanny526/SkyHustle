import asyncio
from config import BOT_TOKEN
from sheets_service import init as sheets_init
from handlers import (
    start, status, menu,
    build, queue, train,
    attack, leaderboard
)
from telegram.ext import Application

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    sheets_init()  # ensure sheets exist
    
    app.add_handler(start.handler)
    app.add_handler(status.handler)
    app.add_handler(menu.handler)
    app.add_handler(build.handler)
    app.add_handler(queue.handler)
    app.add_handler(train.handler)
    app.add_handler(attack.handler)
    app.add_handler(leaderboard.handler)
    
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
