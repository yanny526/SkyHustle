from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, ContextTypes
from modules.sheets_helper import get_player_data


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = get_player_data(user_id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    # Gather counts
    items = {
        "🧬 Revive All Units": data.get("items_revive_all", 0),
        "💥 EMP Field Device": data.get("items_emp_device", 0),
        "🔎 Infinity Scout": data.get("items_infinite_scout", 0),
        "☢️ Hazmat Mask": data.get("items_hazmat_mask", 0),
        "⏱️ 1h Speed-Up": data.get("items_speedup_1h", 0),
        "🛡️ Advanced Shield": data.get("items_shield_adv", 0),
    }
    units = {
        "🧨 BM Barrage": data.get("army_bm_barrage", 0),
        "🦂 Venom Reapers": data.get("army_venom_reaper", 0),
        "🦾 Titan Crushers": data.get("army_titan_crusher", 0),
    }

    text = "🎒 *[YOUR INVENTORY]*\n\n"
    text += "🛍️ *Consumable Items:*\n"
    for name, cnt in items.items():
        text += f"{name}: {cnt}\n"
    text += "\n🪖 *Black Market Units:*\n"
    for name, cnt in units.items():
        text += f"{name}: {cnt}\n"
    text += f"\n💎 *Diamonds:* {data.get('diamonds',0)}"

    # Buttons
    buttons = [[InlineKeyboardButton("🏠 Back to Base", callback_data="INV_BACK")]]

    await context.bot.send_message(
        chat_id, text, parse_mode=constants.ParseMode.MARKDOWN, 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def setup_inventory_system(app: Application) -> None:
    app.add_handler(CommandHandler("inventory", inventory_handler)) 