from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data


ITEMS = [
    {"key":"revive_all",    "name":"🧬 Revive All Units",        "cost":100, "type":"item",  "desc":"Revive all fallen standard troops"},
    {"key":"emp_device",    "name":"💥 EMP Field Device",        "cost":30,  "type":"item",  "desc":"Disable enemy defenses for next attack"},
    {"key":"infinite_scout","name":"🔎 Infinity Scout",          "cost":25,  "type":"item",  "desc":"Scout without alerting"},
    {"key":"hazmat_mask",   "name":"☢️ Hazmat Mask",             "cost":40,  "type":"item",  "desc":"Access Radiation Zones"},
    {"key":"speedup_1h",    "name":"⏱️ 1-Hour Speed-Up",         "cost":20,  "type":"item",  "desc":"Reduce any timer by 1h"},
    {"key":"shield_adv",    "name":"🛡️ Advanced Shield",         "cost":50,  "type":"item",  "desc":"Block first daily attack (7d)"},
    {"key":"bm_barrage",    "name":"🧨 Black Market Barrage",      "cost":70,  "type":"unit", "desc":"Elite artillery unit (5)"},
    {"key":"venom_reaper",  "name":"🦂 Venom Reapers",            "cost":80,  "type":"unit", "desc":"Stealth infantry (10)"},
    {"key":"titan_crusher", "name":"🦾 Titan Crusher",            "cost":120, "type":"unit", "desc":"Building demolisher (2)"},
]


async def blackmarket_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    data = get_player_data(update.effective_user.id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    text = (
        "🕶️ *[BLACK MARKET]*\n"
        "Premium gear and elite units. Spend 💎 Diamonds wisely!\n\n"
        f"💎 Your Balance: *{data['diamonds']}*"
    )
    buttons = []
    for item in ITEMS:
        buttons.append([InlineKeyboardButton(f"{item['name']} — {item['cost']} 💎", callback_data=f"BM_BUY_{item['key']}")])
    buttons.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BM_CANCEL")])

    await context.bot.send_message(
        chat_id, text, parse_mode=constants.ParseMode.MARKDOWN, 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def blackmarket_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = get_player_data(user_id)

    key = query.data.split("_",2)[2]
    item = next(i for i in ITEMS if i["key"] == key)
    cost = item["cost"]

    if data["diamonds"] < cost:
        await query.edit_message_text("❌ Not enough Diamonds.", parse_mode=constants.ParseMode.MARKDOWN)
        return

    # Deduct diamonds
    update_player_data(user_id, "diamonds", data["diamonds"] - cost)

    # Add to inventory or army
    if item["type"] == "unit":
        field = f"army_{key}"
        current = data.get(field, 0)
        update_player_data(user_id, field, current + (5 if key=="bm_barrage" else 10 if key=="venom_reaper" else 2))
    else:
        # track items in a JSON field or separate columns, e.g. items_revive_all
        update_player_data(user_id, f"items_{key}", data.get(f"items_{key}", 0) + 1)

    await query.edit_message_text(
        f"✅ Purchased *{item['name']}* for {cost} 💎! \n"
        f"💎 New Balance: *{data['diamonds'] - cost}*",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def cancel_blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await context.bot.send_message(update.effective_chat.id, "🏠 Returning to base…")

def setup_black_market(app: Application) -> None:
    app.add_handler(CommandHandler("blackmarket", blackmarket_menu))
    app.add_handler(CallbackQueryHandler(blackmarket_menu,   pattern="^BM_MENU$"))
    app.add_handler(CallbackQueryHandler(blackmarket_buy,    pattern="^BM_BUY_"))
    app.add_handler(CallbackQueryHandler(cancel_blackmarket,pattern="^BM_CANCEL$")) 