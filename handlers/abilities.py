# handlers/abilities.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from modules.special_abilities import get_unit_abilities, purchase_ability
from utils.format_utils import section_header

async def abilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args

    if not args:
        lines = [
            section_header("UNIT SPECIAL ABILITIES", "✨", color="purple"),
            "",
            "Special abilities enhance your units in battle. Purchase them using premium credits.",
            "",
            "Available for Infantry:",
        ]
        infantry_abilities = get_unit_abilities('infantry')
        for ability in infantry_abilities:
            lines.append(f"• {ability['name']}: {ability['effect']} - {ability['cost']} ⭐")
        
        lines.append("")
        lines.append("Available for Tanks:")
        tank_abilities = get_unit_abilities('tanks')
        for ability in tank_abilities:
            lines.append(f"• {ability['name']}: {ability['effect']} - {ability['cost']} ⭐")
        
        lines.append("")
        lines.append("Available for Artillery:")
        arty_abilities = get_unit_abilities('artillery')
        for ability in arty_abilities:
            lines.append(f"• {ability['name']}: {ability['effect']} - {ability['cost']} ⭐")
        
        lines.append("")
        lines.append("Purchase abilities using `/ability buy <unit> <ability_id>`")

        kb = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("Buy Premium Credits", callback_data="buy_premium")
        ])

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
        return
    
    if args[0].lower() == 'buy' and len(args) >= 3:
        unit_type = args[1].lower()
        ability_id = args[2].lower()
        success, message = purchase_ability(uid, unit_type, ability_id)
        await update.message.reply_text(
            f"Purchase Result: {message}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "Invalid command. Use `/ability buy <unit> <ability_id>` to purchase an ability.",
            parse_mode=ParseMode.MARKDOWN
        )

handler = CommandHandler("ability", abilities)
