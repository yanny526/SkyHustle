from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data

# Hardcoded unit stats
_UNIT_STATS = {
    "infantry": {"name": "Infantry",   "food":  10, "gold": 5,  "time": 30},
    "tank":     {"name": "Tank",       "food":  20, "gold": 10, "time": 60},
    "artillery":{"name": "Artillery",  "food":  30, "gold": 15, "time": 90},
    "destroyer":{"name": "Destroyer",  "food":  50, "gold": 25, "time":120},
}

async def train_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        if update.message:
            await update.message.reply_text("❌ Send /start first.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ Send /start first.")
        return

    msg = "\n".join([
        "🪖 *[TRAIN YOUR ARMY]*",
        "Available Units (by Barracks level):",
        "",
        f"• 👣 Infantry (Tier 1)", 
        f"• 🛡️ Tank (Tier 1)", 
        f"• 🎯 Artillery (Tier 1)", 
        f"• 🚧 Destroyer (Tier 1)", 
    ])

    keyboard = [
        [InlineKeyboardButton("👣 Infantry", callback_data="TRAIN_infantry")],
        [InlineKeyboardButton("🛡️ Tank", callback_data="TRAIN_tank")],
        [InlineKeyboardButton("🎯 Artillery", callback_data="TRAIN_artillery")],
        [InlineKeyboardButton("🚧 Destroyer", callback_data="TRAIN_destroyer")],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN,
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN,
        )


async def train_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Acknowledge callback
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Determine unit type
    data = get_player_data(user_id)
    b_lvl = data.get("barracks_level", 1)
    unit_key = query.data.split("_", 1)[1]  # e.g. "infantry"

    # Define unit stats
    stats = {
        "infantry":   {"name": "Infantry",   "food":  10, "gold": 5,  "time": 30},
        "tank":       {"name": "Tank",       "food":  20, "gold": 10, "time": 60},
        "artillery":  {"name": "Artillery",  "food":  30, "gold": 15, "time": 90},
        "destroyer":  {"name": "Destroyer",  "food":  50, "gold": 25, "time":120},
    }
    u = stats[unit_key]
    # Calculate max by resources
    max_by_food = data["resources_food"] // u["food"]
    max_by_gold = data["resources_gold"] // u["gold"]
    max_qty = min(max_by_food, max_by_gold, b_lvl * 50)

    # Prompt quantity
    text = (
        f"👣 *Train {u['name']}*\n"
        f"Cost per unit: 🥖 {u['food']}  💰 {u['gold']}\n"
        f"Time per unit: {u['time']}s\n\n"
        f"How many {u['name']} do you want to train? (Max {max_qty})"
    )
    buttons = [
        [InlineKeyboardButton(f"➕ {n}", callback_data=f"TRAIN_QTY_{unit_key}_{n}")]
        for n in [10, 25, 50, max_qty] if n > 0 and n <= max_qty # ensure n is positive
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="TRAIN_CANCEL")])
    await context.bot.send_message(chat_id, text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))

async def confirm_train(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    _, _, unit_key, qty_str = query.data.split("_")
    qty = int(qty_str)

    data = get_player_data(user_id)
    stats = _UNIT_STATS[unit_key]

    cost_food = stats["food"] * qty
    cost_gold = stats["gold"] * qty

    # Check resources
    if data["resources_food"] < cost_food or data["resources_gold"] < cost_gold:
        await context.bot.send_message(chat_id, "❌ Not enough resources.")
        return

    # Deduct
    update_player_data(user_id, "resources_food", data["resources_food"] - cost_food)
    update_player_data(user_id, "resources_gold", data["resources_gold"] - cost_gold)

    # Add to army count
    field = f"army_{unit_key}"
    current = data.get(field, 0)
    update_player_data(user_id, field, current + qty)

    await context.bot.send_message(
        chat_id,
        f"✅ Training {qty} {stats['name']} started!\n"
        f"It will take {stats['time'] * qty}s to complete.",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def cancel_train(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await context.bot.send_message(update.effective_chat.id, "❌ Training cancelled.")

def setup_training_system(app: Application) -> None:
    """Register training system handlers."""
    app.add_handler(CommandHandler("train", train_menu))
    app.add_handler(CallbackQueryHandler(train_menu, pattern="^TRAIN_MENU$"))
    app.add_handler(CallbackQueryHandler(train_choice, pattern="^TRAIN_[a-z]+$"))
    app.add_handler(CallbackQueryHandler(confirm_train, pattern="^TRAIN_QTY_"))
    app.add_handler(CallbackQueryHandler(cancel_train, pattern="^TRAIN_CANCEL$")) 