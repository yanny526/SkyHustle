from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data
from telegram.helpers import escape_markdown

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
        "Available Units \(by Barracks level\):",
        "",
        f"• 👣 {escape_markdown(_UNIT_STATS['infantry']['name'])} \(Tier 1\)", 
        f"• 🛡️ {escape_markdown(_UNIT_STATS['tank']['name'])} \(Tier 1\)", 
        f"• 🎯 {escape_markdown(_UNIT_STATS['artillery']['name'])} \(Tier 1\)", 
        f"• 🚧 {escape_markdown(_UNIT_STATS['destroyer']['name'])} \(Tier 1\)", 
    ])

    keyboard = [
        [InlineKeyboardButton(f"👣 {escape_markdown(_UNIT_STATS['infantry']['name'])}", callback_data="TRAIN_infantry")],
        [InlineKeyboardButton(f"🛡️ {escape_markdown(_UNIT_STATS['tank']['name'])}", callback_data="TRAIN_tank")],
        [InlineKeyboardButton(f"🎯 {escape_markdown(_UNIT_STATS['artillery']['name'])}", callback_data="TRAIN_artillery")],
        [InlineKeyboardButton(f"🚧 {escape_markdown(_UNIT_STATS['destroyer']['name'])}", callback_data="TRAIN_destroyer")],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")],
    ]

    # Use list concatenation or extend to avoid modifying `keyboard` directly
    buttons = keyboard + [[InlineKeyboardButton("📊 Unit Stats", callback_data="TRAIN_STATS")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    if update.message:
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            msg,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )


async def train_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Acknowledge callback
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Determine unit type
    data = get_player_data(user_id)
    b_lvl = int(data.get("barracks_level", 1))
    unit_key = query.data.split("_", 1)[1]  # e.g. "infantry"

    # Use module-level _UNIT_STATS
    u = _UNIT_STATS[unit_key]
    
    # Calculate max by resources
    current_food = int(data.get("resources_food", 0))
    current_gold = int(data.get("resources_gold", 0))
    
    print(f"DEBUG in train_choice: current_food={current_food}, current_gold={current_gold}") # New debug
    print(f"DEBUG in train_choice: unit_food_cost={u['food']}, unit_gold_cost={u['gold']}") # New debug
    print(f"DEBUG in train_choice: barracks_level={b_lvl}") # New debug

    max_by_food = current_food // u["food"]
    max_by_gold = current_gold // u["gold"]
    max_qty = min(max_by_food, max_by_gold, b_lvl * 50)
    print(f"DEBUG in train_choice: max_by_food={max_by_food}, max_by_gold={max_by_gold}, b_lvl*50={b_lvl*50}, final_max_qty={max_qty}") # New debug

    # Prompt quantity
    text = (
        f"👣 *Train {escape_markdown(u['name'])}*\n"
        f"Cost per unit: 🥖 {escape_markdown(str(u['food']))}  💰 {escape_markdown(str(u['gold']))}\n"
        f"Time per unit: {escape_markdown(str(u['time']))}s\n\n"
        f"How many {escape_markdown(u['name'])} do you want to train? \(Max {max_qty}\)"
    )
    buttons = [
        [InlineKeyboardButton(f"➕ {escape_markdown(str(n))}", callback_data=f"TRAIN_QTY_{unit_key}_{n}")]
        for n in [10, 25, 50, max_qty] if n > 0 and n <= max_qty # ensure n is positive
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="TRAIN_CANCEL")])
    await context.bot.send_message(chat_id, text, parse_mode=constants.ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))

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

    # Get current resources
    current_food = int(data.get("resources_food", 0))
    current_gold = int(data.get("resources_gold", 0))

    # Check resources
    if current_food < cost_food or current_gold < cost_gold:
        await context.bot.send_message(chat_id, "❌ Not enough resources.")
        return

    # Deduct
    update_player_data(user_id, "resources_food", current_food - cost_food)
    update_player_data(user_id, "resources_gold", current_gold - cost_gold)

    # Add to army count
    field = f"army_{unit_key}"
    current_army_count = int(data.get(field, 0))
    update_player_data(user_id, field, current_army_count + qty)

    await context.bot.send_message(
        chat_id,
        f"✅ Training {escape_markdown(str(qty))} {escape_markdown(stats['name'])} started\!\n"
        f"It will take {escape_markdown(str(stats['time'] * qty))}s to complete\.",
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

async def cancel_train(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await context.bot.send_message(update.effective_chat.id, "❌ Training cancelled\.", parse_mode=constants.ParseMode.MARKDOWN_V2)

async def show_unit_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    # Use module-level _UNIT_STATS for consistent stats
    # Reformat for display if needed, but the source should be _UNIT_STATS
    display_stats = {
        "infantry": {"Attack": 4,  "HP": 10,  "Cost": f"{_UNIT_STATS['infantry']['food']}🥖,{_UNIT_STATS['infantry']['gold']}💰",   "Time": f"{_UNIT_STATS['infantry']['time']}s"},
        "tank":     {"Attack": 12, "HP": 40,  "Cost": f"{_UNIT_STATS['tank']['food']}🥖,{_UNIT_STATS['tank']['gold']}💰",  "Time": f"{_UNIT_STATS['tank']['time']}s"},
        "artillery":{"Attack": 20, "HP": 20,  "Cost": f"{_UNIT_STATS['artillery']['food']}🥖,{_UNIT_STATS['artillery']['gold']}💰",  "Time": f"{_UNIT_STATS['artillery']['time']}s"},
        "destroyer":{"Attack": 35, "HP": 80,  "Cost": f"{_UNIT_STATS['destroyer']['food']}🥖,{_UNIT_STATS['destroyer']['gold']}💰",  "Time": f"{_UNIT_STATS['destroyer']['time']}s"},
    }

    lines = ["📊 *Unit Stats*"]
    for unit_key, s in display_stats.items():
        # Use _UNIT_STATS for name, and escape all dynamic parts
        name = _UNIT_STATS[unit_key]['name']
        lines.append(f"*{escape_markdown(name)}* — ATK: {escape_markdown(str(s['Attack']))}  HP: {escape_markdown(str(s['HP']))}  Cost: {escape_markdown(s['Cost'])}  Time: {escape_markdown(s['Time'])}")
    text = "\n".join(lines)

    await context.bot.send_message(
        chat_id,
        text,
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

def setup_training_system(app: Application) -> None:
    """Register training system handlers."""
    app.add_handler(CommandHandler("train", train_menu))
    app.add_handler(CallbackQueryHandler(train_menu, pattern="^TRAIN_MENU$"))
    app.add_handler(CallbackQueryHandler(train_choice, pattern="^TRAIN_[a-z]+$"))
    app.add_handler(CallbackQueryHandler(confirm_train, pattern="^TRAIN_QTY_"))
    app.add_handler(CallbackQueryHandler(cancel_train, pattern="^TRAIN_CANCEL$"))
    app.add_handler(CallbackQueryHandler(show_unit_stats, pattern="^TRAIN_STATS$")) 