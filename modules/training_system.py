from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data

# Hardcoded unit stats for now
_UNIT_STATS = {
    "infantry": {
        "name": "Infantry",
        "cost": {"food": 10, "gold": 5},
        "time_s": 30, # seconds
    },
    "tank": {
        "name": "Tank",
        "cost": {"food": 20, "stone": 10},
        "time_s": 60,
    },
    "artillery": {
        "name": "Artillery",
        "cost": {"food": 15, "wood": 10},
        "time_s": 45,
    },
    "destroyer": {
        "name": "Destroyer",
        "cost": {"gold": 25, "wood": 15},
        "time_s": 90,
    },
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
        f"• 👣 Infantry (Tier 1)", # Barracks level 1
        f"• 🛡️ Tank (Tier 1)", # Barracks level 1
        f"• 🎯 Artillery (Tier 1)", # Barracks level 2
        f"• 🚧 Destroyer (Tier 1)", # Barracks level 3
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
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ Send /start first.")
        return

    unit_type = query.data.replace("TRAIN_", "")
    unit_info = _UNIT_STATS.get(unit_type)

    if not unit_info:
        await query.edit_message_text("❌ Unknown unit.")
        return

    unit_name = unit_info["name"]
    cost = unit_info["cost"]
    time_s = unit_info["time_s"]

    # Calculate max affordable
    max_affordable = float('inf')
    for resource, quantity in cost.items():
        player_resource = data.get(f"resources_{resource}", 0)
        if quantity > 0:
            max_affordable = min(max_affordable, player_resource // quantity)
        else:
            # If cost is 0, it's 'free' in terms of this resource, so doesn't limit.
            # We can skip this or set to max_affordable for this resource to a very high number.
            pass 

    if max_affordable == float('inf'): # If unit costs nothing or all costs are 0
        max_affordable = 9999 # Arbitrarily large number

    msg = "\n".join([
        f"🪖 *How many {unit_name} do you want to train?*",
        f"_Each: ⏳ {time_s}s, Cost: {', '.join([f'{qty} {res}' for res, qty in cost.items()])}_",
        f"(Max affordable: {max_affordable})",
    ])

    keyboard = [
        [
            InlineKeyboardButton("➕10", callback_data=f"TRAIN_CONFIRM_{unit_type}_10"),
            InlineKeyboardButton("➕25", callback_data=f"TRAIN_CONFIRM_{unit_type}_25"),
            InlineKeyboardButton("➕50", callback_data=f"TRAIN_CONFIRM_{unit_type}_50"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="TRAIN_CANCEL"),
        ],
    ]

    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def confirm_train(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ Send /start first.")
        return

    parts = query.data.split("_")
    unit_type = parts[2] # TRAIN_CONFIRM_{unit}_{qty}
    qty = int(parts[3])

    unit_info = _UNIT_STATS.get(unit_type)
    if not unit_info:
        await query.edit_message_text("❌ Unknown unit.")
        return

    cost = unit_info["cost"]
    time_s = unit_info["time_s"]

    # Check resources
    can_afford = True
    for resource, single_cost in cost.items():
        total_cost = single_cost * qty
        if data.get(f"resources_{resource}", 0) < total_cost:
            can_afford = False
            break

    if not can_afford:
        await query.edit_message_text("❌ Not enough resources.")
        return

    # Deduct resources
    for resource, single_cost in cost.items():
        total_cost = single_cost * qty
        update_player_data(user.id, f"resources_{resource}", data[f"resources_{resource}"] - total_cost)

    # Add to army
    army_field = f"army_{unit_type}"
    current_army = data.get(army_field, 0) # Get current army count, default to 0
    update_player_data(user.id, army_field, current_army + qty)

    # Confirm message
    msg = (
        f"✅ Training {qty} {unit_info['name']} started!\n"
        f"It'll take {qty * time_s}s."
    )

    await query.edit_message_text(msg, parse_mode=constants.ParseMode.MARKDOWN)

async def cancel_train(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Training canceled.")

def setup_training_system(app: Application) -> None:
    """Register training system handlers."""
    app.add_handler(CommandHandler("train", train_menu))
    app.add_handler(CallbackQueryHandler(train_menu, pattern="^TRAIN_MENU$"))
    app.add_handler(CallbackQueryHandler(train_choice, pattern="^TRAIN_"))
    app.add_handler(CallbackQueryHandler(confirm_train, pattern="^TRAIN_CONFIRM_"))
    app.add_handler(CallbackQueryHandler(cancel_train, pattern="^TRAIN_CANCEL$")) 