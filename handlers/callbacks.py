# handlers/callbacks.py

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from handlers.status import status as status_handler
from handlers.queue import queue as queue_handler
from handlers.army import army as army_handler
from handlers.leaderboard import leaderboard as leaderboard_handler
from handlers.help import help_command as help_handler

async def menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_status":
        await status_handler(update, context)
    elif query.data == "menu_queue":
        await queue_handler(update, context)
    elif query.data == "menu_army":
        await army_handler(update, context)
    elif query.data == "menu_leaderboard":
        await leaderboard_handler(update, context)
    elif query.data == "menu_help":
        await help_handler(update, context)
    else:
        await query.edit_message_text("❓ Unknown menu option.")

handler = CallbackQueryHandler(menu_callback)
