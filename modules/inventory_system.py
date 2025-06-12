from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from modules.sheets_helper import get_player_data, update_player_data
import datetime
from datetime import timezone
import telegram

# Item definitions
ITEMS = {
    "revive_all": {
        "name": "🧬 Revive All Units",
        "description": "Instantly revives all dead troops in your army.",
        "effect": "All dead troops have been revived!"
    },
    "emp_device": {
        "name": "💥 EMP Field Device",
        "description": "Boosts resource production by 50% for 1 hour.",
        "effect": "Resource production boosted for 1 hour!"
    },
    "infinite_scout": {
        "name": "🔎 Infinity Scout",
        "description": "Allows unlimited scouting without alerting enemies.",
        "effect": "Infinite scouting activated for 24 hours!"
    },
    "hazmat_mask": {
        "name": "☢️ Hazmat Mask",
        "description": "Grants access to radiation zones for 24 hours.",
        "effect": "Radiation zone access granted for 24 hours!"
    },
    "speedup_1h": {
        "name": "⏱️ 1h Speed-Up",
        "description": "Reduces any active timer by 1 hour.",
        "effect": "Active timer reduced by 1 hour!"
    },
    "shield_adv": {
        "name": "🛡️ Advanced Shield",
        "description": "Blocks the next attack on your base.",
        "effect": "Advanced shield activated! Next attack will be blocked."
    },
    "hazmat_drone": {
        "name": "☢️ Hazmat Drone",
        "description": "Grants access to radiation zones for 24 hours.",
        "effect": "Radiation zone access granted for 24 hours!"
    }
}

async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the player's inventory with grouped items and action buttons."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = get_player_data(user_id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    # Fetch data
    consumables = [
        ("Revive All",    data.get("items_revive_all", 0)),
        ("EMP Field Device", data.get("items_emp_device", 0)),
        ("Infinity Scout", data.get("items_infinite_scout", 0)),
        ("Hazmat Mask",   data.get("items_hazmat_mask", 0)),
        ("1 H Speed-Up",  data.get("items_speedup_1h", 0)),
        ("Advanced Shield", data.get("items_shield_adv", 0)),
        ("Hazmat Drone",  data.get("items_hazmat_drone", 0)),
    ]
    bm_units = [
        ("BM Barrage",    data.get("army_bm_barrage", 0)),
        ("Venom Reapers", data.get("army_venom_reaper", 0)),
        ("Titan Crushers",data.get("army_titan_crusher", 0)),
    ]
    diamonds = data.get("diamonds", 0)

    # Build message text
    text = "🎒 *Your Inventory*\n\n"
    text += "*Consumables:*\n"
    for name, cnt in consumables:
        text += f"• {name}: **{cnt}**\n"
    text += "\n*Black Market Units:*\n"
    for name, cnt in bm_units:
        text += f"• {name}: **{cnt}**\n"
    text += f"\n💎 Diamonds: **{diamonds}**"

    # Generate keyboard
    keyboard = []
    for key, (name, cnt) in zip(
        ["revive_all", "emp_device", "infinite_scout", "hazmat_mask", "speedup_1h", "shield_adv", "hazmat_drone"],
        consumables
    ):
        row = [
            InlineKeyboardButton("🛈 Info", callback_data=f"inv_info:{key}")
        ]
        if cnt > 0:
            row.append(InlineKeyboardButton("▶️ Use", callback_data=f"inv_use:{key}"))
        keyboard.append(row)

    for key, (name, cnt) in zip(
        ["bm_barrage", "venom_reaper", "titan_crusher"],
        bm_units
    ):
        row = [InlineKeyboardButton("🛈 Info", callback_data=f"inv_info:{key}")]
        if cnt > 0:
            row.append(InlineKeyboardButton("▶️ Use", callback_data=f"inv_use:{key}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BACK_TO_BASE")])

    # Send message
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                text,
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Fallback to sending new message if edit fails
            await update.callback_query.message.reply_text(
                text,
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await update.message.reply_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def show_item_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed information about an item."""
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            pass
        else:
            print(f"Error answering callback query: {e}")
            return

    item_key = query.data.split(":", 1)[1]
    
    # Item descriptions
    item_descriptions = {
        "revive_all": "🧬 Revives all dead troops instantly.",
        "emp_device": "💥 Boosts resource production by 50% for 1 hour.",
        "infinite_scout": "🔎 Allows unlimited scouting without alerting enemies.",
        "hazmat_mask": "☢️ Grants access to radiation zones for 24 hours.",
        "speedup_1h": "⏱️ Reduces any active timer by 1 hour.",
        "shield_adv": "🛡️ Blocks the next attack on your base.",
        "hazmat_drone": "☢️ Grants access to radiation zones for 24 hours.",
    }

    description = item_descriptions.get(item_key, "No description available.")
    await query.edit_message_text(
        f"*{item_key.replace('_', ' ').title()}*\n\n{description}",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def inventory_use_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show menu of available items to use."""
    user = update.effective_user
    if not user:
        return

    data = get_player_data(user.id)
    if not data:
        await update.message.reply_text("❌ You aren't registered yet. Send /start to begin.")
        return

    # Build keyboard with available items
    keyboard = []
    for key, item in ITEMS.items():
        count = data.get(f"items_{key}", 0)
        if count > 0:
            keyboard.append([
                InlineKeyboardButton(
                    f"{item['name']} x{count}",
                    callback_data=f"use_item_{key}"
                )
            ])

    if not keyboard:
        await update.message.reply_text("❌ You have no items to use.")
        return

    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="INV_BACK")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🛠 *Select an item to use:*",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def use_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show confirmation dialog for item usage."""
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            pass
        else:
            print(f"Error answering callback query: {e}")
            return

    key = query.data.split("_", 2)[2]
    item = ITEMS.get(key)
    if not item:
        await query.edit_message_text("❌ Invalid item selected.")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_use_{key}"),
            InlineKeyboardButton("❌ No", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🛠 *Use {item['name']}?*\n\n"
        f"{item['description']}\n\n"
        "Confirm?",
        parse_mode=constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def confirm_use_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle item usage confirmation."""
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            pass
        else:
            print(f"Error answering callback query: {e}")
            return

    if query.data == "cancel":
        await inventory_handler(update, context)
        return

    key = query.data.split("_", 2)[2]
    item = ITEMS.get(key)
    if not item:
        await query.edit_message_text("❌ Invalid item selected.")
        return

    user_id = query.from_user.id
    data = get_player_data(user_id)
    if not data:
        await query.edit_message_text("❌ You aren't registered yet. Send /start to begin.")
        return

    # Check item count
    item_field = f"items_{key}"
    current_count = data.get(item_field, 0)
    if current_count <= 0:
        await query.edit_message_text("❌ You don't have this item anymore.")
        return

    # Decrement item count
    update_player_data(user_id, item_field, current_count - 1)

    # Apply item effect
    now = datetime.datetime.now(timezone.utc)
    if key == "revive_all":
        dead_infantry = data.get("army_dead_infantry", 0)
        dead_tanks = data.get("army_dead_tanks", 0)

        if dead_infantry > 0:
            update_player_data(user_id, "army_infantry", data.get("army_infantry", 0) + dead_infantry)
            update_player_data(user_id, "army_dead_infantry", 0)

        if dead_tanks > 0:
            update_player_data(user_id, "army_tank", data.get("army_tank", 0) + dead_tanks)
            update_player_data(user_id, "army_dead_tanks", 0)

    elif key == "emp_device":
        boost_end_time = now + datetime.timedelta(hours=1)
        update_player_data(user_id, "timers_emp_boost_end", boost_end_time.isoformat() + "Z")

    elif key == "hazmat_drone":
        access_end_time = now + datetime.timedelta(hours=24)
        update_player_data(user_id, "timers_hazmat_access_end", access_end_time.isoformat() + "Z")

    elif key == "speedup_1h":
        timer_fields = [
            "timers_base_level", "timers_mine_level", "timers_lumber_level",
            "timers_warehouse_level", "timers_barracks_level", "timers_power_level",
            "timers_hospital_level", "timers_research_level", "timers_workshop_level",
            "timers_jail_level"
        ]
        
        for field in timer_fields:
            timer = data.get(field)
            if timer:
                try:
                    if isinstance(timer, datetime.datetime):
                        timer_dt = timer
                    else:
                        timer_dt = datetime.datetime.fromisoformat(str(timer).rstrip("Z")).replace(tzinfo=timezone.utc)
                    
                    if timer_dt > now:
                        new_time = timer_dt - datetime.timedelta(hours=1)
                        if new_time > now:
                            update_player_data(user_id, field, new_time.isoformat() + "Z")
                except (ValueError, TypeError):
                    continue

    elif key == "shield_adv":
        shield_end_time = now + datetime.timedelta(days=7)
        update_player_data(user_id, "timers_shield_end", shield_end_time.isoformat() + "Z")

    # Show success message
    await query.edit_message_text(
        f"✅ You used {item['name']}\\. {item['effect']}",
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

    # Refresh base UI
    from modules.base_ui import base_handler
    await base_handler(update, context)

def setup_inventory_system(app: Application) -> None:
    """Register inventory system handlers."""
    app.add_handler(CommandHandler("inventory", inventory_handler))
    app.add_handler(CommandHandler("use", inventory_use_menu))
    app.add_handler(CallbackQueryHandler(inventory_handler, pattern="^INV_BACK$"))
    app.add_handler(CallbackQueryHandler(show_item_info, pattern="^item_info:"))
    app.add_handler(CallbackQueryHandler(use_item_callback, pattern="^use_item_"))
    app.add_handler(CallbackQueryHandler(confirm_use_callback, pattern="^confirm_use_")) 