from telegram.ext import ApplicationBuilder, MessageHandler, filters
from handlers import core
from config import BOT_TOKEN

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, core.handle_message))
app.run_polling()
