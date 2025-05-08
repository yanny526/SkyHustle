# handlers/train.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from modules.units import Unit
from utils.format import section_header

units_data = {
    "infantry": Unit("Infantry", 10, 50),
    "tanks": Unit("Tanks", 30, 150),
    "artillery": Unit("Artillery", 50, 300)
}

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        kb = [[InlineKeyboardButton(f"Train {unit.name} (Cost: {unit.cost} credits)", callback_data=f"train_{name}")] for name, unit in units_data.items()]
        kb.append([InlineKeyboardButton("Close", callback_data="close")])

        await update.message.reply_text(
            f"{section_header('TRAINING MENU', '👨‍✈️', 'purple')}\n\n"
            "Select a unit to train:\n\n" +
            "\n".join([f"{name}: Power {unit.power} | Cost {unit.cost} | Trained {unit.count}" for name, unit in units_data.items()]),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    unit_name = args[0].lower()
    if unit_name in units_data:
        unit = units_data[unit_name]
        unit.train(1)
        await update.message.reply_text(
            f"👨‍✈️ *Unit Trained* 👨‍✈️\n\n"
            f"{unit.name} trained! Total: {unit.count}\n"
            f"Power: {unit.power} | Cost: {unit.cost} credits",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Invalid unit name. Use /train to see available units.",
            parse_mode="Markdown"
        )