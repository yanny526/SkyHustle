from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data
import datetime

async def build_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await update.message.reply_text("❌ Send /start first.")
        return

    # Safely get building levels with defaults
    base_level = data.get("base_level", 1)
    lumber_house_level = data.get("lumber_house_level", 1)
    mine_level = data.get("mine_level", 1)
    warehouse_level = data.get("warehouse_level", 1)
    hospital_level = data.get("hospital_level", 1)
    research_lab_level = data.get("research_lab_level", 1)
    barracks_level = data.get("barracks_level", 1)
    power_plant_level = data.get("power_plant_level", 1)
    workshop_level = data.get("workshop_level", 1)
    jail_level = data.get("jail_level", 1)

    # Build the message
    msg = "\n".join([
        "⚒️ *[BUILD MENU]*",
        "Choose a building to upgrade:",
        "",
        f"🏠 Base: Lv {base_level}",
        f"🪓 Lumber House: Lv {lumber_house_level}",
        f"⛏️ Mine: Lv {mine_level}",
        f"🧺 Warehouse: Lv {warehouse_level}",
        f"🏥 Hospital: Lv {hospital_level}",
        f"🧪 Research Lab: Lv {research_lab_level}",
        f"🪖 Barracks: Lv {barracks_level}",
        f"🔋 Power Plant: Lv {power_plant_level}",
        f"🔧 Workshop: Lv {workshop_level}",
        f"🚔 Jail: Lv {jail_level}",
    ])

    # Create building buttons
    keyboard = [
        [InlineKeyboardButton("🏠 Base", callback_data="BUILD_base_level")],
        [InlineKeyboardButton("🪓 Lumber House", callback_data="BUILD_lumber_house_level")],
        [InlineKeyboardButton("⛏️ Mine", callback_data="BUILD_mine_level")],
        [InlineKeyboardButton("🧺 Warehouse", callback_data="BUILD_warehouse_level")],
        [InlineKeyboardButton("🏥 Hospital", callback_data="BUILD_hospital_level")],
        [InlineKeyboardButton("🧪 Research Lab", callback_data="BUILD_research_lab_level")],
        [InlineKeyboardButton("🪖 Barracks", callback_data="BUILD_barracks_level")],
        [InlineKeyboardButton("🔋 Power Plant", callback_data="BUILD_power_plant_level")],
        [InlineKeyboardButton("🔧 Workshop", callback_data="BUILD_workshop_level")],
        [InlineKeyboardButton("🚔 Jail", callback_data="BUILD_jail_level")],
        [InlineKeyboardButton("🏠 Back to Base", callback_data="BASE_MENU")],
    ]

    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def build_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ Send /start first.")
        return

    # Extract building field from callback data
    field = query.data.replace("BUILD_", "")
    current = data.get(field, 1)
    next_lv = current + 1

    # Calculate costs and time
    cost_wood = 100 * next_lv
    cost_stone = 80 * next_lv
    time_mins = 5 * next_lv

    # Get building name for display
    building_names = {
        "base_level": "Base",
        "lumber_house_level": "Lumber House",
        "mine_level": "Mine",
        "warehouse_level": "Warehouse",
        "hospital_level": "Hospital",
        "research_lab_level": "Research Lab",
        "barracks_level": "Barracks",
        "power_plant_level": "Power Plant",
        "workshop_level": "Workshop",
        "jail_level": "Jail",
    }
    building_name = building_names.get(field, field)

    # Build the message
    msg = "\n".join([
        f"🏗️ *{building_name}: Level {current} → {next_lv}*",
        f"🔨 Cost: 🪵{cost_wood} 🪨{cost_stone}",
        f"⏱️ Time: {time_mins}m",
    ])

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"CONFIRM_{field}"),
            InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_BUILD"),
        ],
    ]

    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def confirm_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await query.edit_message_text("❌ Send /start first.")
        return

    # Extract building field and recalculate costs
    field = query.data.replace("CONFIRM_", "")
    current = data.get(field, 1)
    next_lv = current + 1

    cost_wood = 100 * next_lv
    cost_stone = 80 * next_lv
    time_mins = 5 * next_lv

    # Check if player has enough resources
    if data.get("resources_wood", 0) < cost_wood or data.get("resources_stone", 0) < cost_stone:
        await query.edit_message_text("❌ Not enough resources.")
        return

    # Deduct resources
    update_player_data(user.id, "resources_wood", data["resources_wood"] - cost_wood)
    update_player_data(user.id, "resources_stone", data["resources_stone"] - cost_stone)

    # Set timer end
    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=time_mins)
    timer_field = f"timers.{field}"
    update_player_data(user.id, timer_field, end_time.isoformat() + "Z")

    # Confirm message
    msg = "\n".join([
        "✔️ Upgrade started!",
        f"🕒 Complete in {time_mins} minutes.",
    ])

    await query.edit_message_text(msg, parse_mode=constants.ParseMode.MARKDOWN)

async def cancel_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Build cancelled.")

def setup_building_system(app: Application) -> None:
    """Register building system handlers."""
    app.add_handler(CommandHandler("build", build_menu))

    # now also catch the inline "⚒️ Build" button
    app.add_handler(CallbackQueryHandler(build_menu, pattern="^BUILD_MENU$"))

    app.add_handler(CallbackQueryHandler(build_choice, pattern="^BUILD_"))
    app.add_handler(CallbackQueryHandler(confirm_build, pattern="^CONFIRM_"))
    app.add_handler(CallbackQueryHandler(cancel_build, pattern="^CANCEL_BUILD$")) 