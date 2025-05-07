# handlers/premium.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from utils.format_utils import section_header

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    lines = [
        section_header("PREMIUM MEMBERSHIP", "⭐", color="orange"),
        "",
        "✨ Unlock exclusive features:",
        "• Double rewards from achievements",
        "• Special units and buildings",
        "• Ad-free experience",
        "• And much more!",
        "",
        "💎 Premium Credits can be purchased with real money.",
        "Use them to accelerate your progress:",
        "• Instant building upgrades",
        "• Special unit boosts",
        "• Event-exclusive content",
        "",
        section_header("AVAILABLE PACKS", "💳", color="orange"),
        "• Small Pack: 100 ⭐ - $1.99",
        "• Medium Pack: 500 ⭐ - $4.99",
        "• Large Pack: 1500 ⭐ - $9.99",
        "• Massive Pack: 5000 ⭐ - $24.99",
    ]

    kb = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton("Buy Premium Credits", callback_data="buy_premium"),
        InlineKeyboardButton("Redeem Code", callback_data="redeem_code")
    ])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )

async def premium_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy_premium":
        await query.edit_message_text(
            "Please visit our premium store to purchase credits:\n"
            "• Small Pack: 100 ⭐ - $1.99\n"
            "• Medium Pack: 500 ⭐ - $4.99\n"
            "• Large Pack: 1500 ⭐ - $9.99\n"
            "• Massive Pack: 5000 ⭐ - $24.99",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "redeem_code":
        await query.edit_message_text(
            "Send your redemption code to @GameSupportBot to activate premium credits.",
            parse_mode=ParseMode.MARKDOWN
        )

handler = CommandHandler("premium", premium)
callback_handler = CallbackQueryHandler(premium_button, pattern=r"^buy_premium$|^redeem_code$")
