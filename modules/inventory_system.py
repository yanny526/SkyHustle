from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from modules.sheets_helper import get_player_data, update_player_data
import datetime
from datetime import timezone


async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = get_player_data(user_id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    # Gather counts
    items = {
        "�� Revive All Units": {"key": "revive_all", "count": data.get("items_revive_all", 0)},
        "💥 EMP Field Device": {"key": "emp_device", "count": data.get("items_emp_device", 0)},
        "🔎 Infinity Scout": {"key": "infinite_scout", "count": data.get("items_infinite_scout", 0)},
        "☢️ Hazmat Mask": {"key": "hazmat_mask", "count": data.get("items_hazmat_mask", 0)},
        "⏱️ 1h Speed-Up": {"key": "speedup_1h", "count": data.get("items_speedup_1h", 0)},
        "🛡️ Advanced Shield": {"key": "shield_adv", "count": data.get("items_shield_adv", 0)},
        "☢️ Hazmat Drone": {"key": "hazmat_drone", "count": data.get("items_hazmat_drone", 0)},
    }
    units = {
        "🧨 BM Barrage": data.get("army_bm_barrage", 0),
        "🦂 Venom Reapers": data.get("army_venom_reaper", 0),
        "🦾 Titan Crushers": data.get("army_titan_crusher", 0),
    }

    text = "🎒 *[YOUR INVENTORY]*\n\n"
    
    # Consumable Items section
    text += "🛍️ *Consumable Items:*\n"
    for name, item_info in items.items():
        text += f"{name}: {item_info['count']}\n"
    
    # Black Market Units section
    text += "\n🪖 *Black Market Units:*\n"
    for name, cnt in units.items():
        text += f"{name}: {cnt}\n"
    
    # Diamonds
    text += f"\n💎 *Diamonds:* {data.get('diamonds',0)}\n"

    # Buttons for using items
    use_item_buttons = []
    for name, item_info in items.items():
        if item_info['count'] > 0:
            use_item_buttons.append(InlineKeyboardButton(f"Use {name.split(':')[0].strip()}", callback_data=f"use_item:{item_info['key']}"))
    
    keyboard = []
    if use_item_buttons:
        keyboard.append(use_item_buttons)
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="INV_BACK")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id, text, parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

# --- Callbacks for Item Use ---

async def use_item_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles callback queries for item usage (use_item:<key>).
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    _, item_key = query.data.split(':') # Expected format: "use_item:revive_all"

    player_data = get_player_data(user_id)
    if not player_data:
        await query.edit_message_text("❌ You aren't registered yet. Send /start to begin.")
        return

    item_field = f"items_{item_key}"
    current_item_count = player_data.get(item_field, 0)

    if current_item_count <= 0:
        await query.edit_message_text(f"You have no *{item_key.replace('_', ' ').title()}* left.",
                                      parse_mode=constants.ParseMode.MARKDOWN)
        return

    # Decrement item count
    update_player_data(user_id, item_field, current_item_count - 1)

    summary_message = f"*Used {item_key.replace('_', ' ').title()}!*\n\n"
    now = datetime.datetime.now(timezone.utc)

    if item_key == "revive_all":
        dead_infantry = player_data.get("army_dead_infantry", 0)
        dead_tanks = player_data.get("army_dead_tanks", 0)

        if dead_infantry > 0:
            update_player_data(user_id, "army_infantry", player_data.get("army_infantry", 0) + dead_infantry)
            update_player_data(user_id, "army_dead_infantry", 0)
            summary_message += f"👣 Revived {dead_infantry} infantry.\n"

        if dead_tanks > 0:
            update_player_data(user_id, "army_tank", player_data.get("army_tank", 0) + dead_tanks)
            update_player_data(user_id, "army_dead_tanks", 0)
            summary_message += f"🛡️ Revived {dead_tanks} tanks.\n"

        if dead_infantry == 0 and dead_tanks == 0:
            summary_message = "You used *Revive All*, but had no dead troops to revive!\n"

    elif item_key == "emp_device":
        boost_end_time = now + datetime.timedelta(hours=1)
        update_player_data(user_id, "timers_emp_boost_end", boost_end_time.isoformat() + "Z")
        summary_message += "⚡ EMP device activated! Resource production boosted for 1 hour.\n"

    elif item_key == "hazmat_drone":
        access_end_time = now + datetime.timedelta(hours=24)
        update_player_data(user_id, "timers_hazmat_access_end", access_end_time.isoformat() + "Z")
        summary_message += "☢️ Hazmat Drone deployed! You now have access to radiation zones for 24 hours.\n"

    else:
        summary_message = f"Unknown item: {item_key.replace('_', ' ').title()}.\n"

    await query.edit_message_text(summary_message, parse_mode=constants.ParseMode.MARKDOWN)
    # Optionally, refresh the inventory view after item use
    await inventory_handler(update, context) # Call inventory_handler to show updated inventory

def setup_inventory_system(app: Application) -> None:
    app.add_handler(CommandHandler("inventory", inventory_handler))
    app.add_handler(CallbackQueryHandler(inventory_handler, pattern="^INV_BACK$"))
    app.add_handler(CallbackQueryHandler(use_item_callback, pattern="^use_item:")) 