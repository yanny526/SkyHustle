from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from modules.sheets_helper import get_player_data, update_player_data
import datetime
from datetime import timezone
import telegram
import re
from typing import Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2, except '~' for strikethrough."""
    # List of special characters to escape for MarkdownV2
    # '~' is excluded as it's used for strikethrough as per the requirement.
    special_chars = ['_', '*', '[', ']', '(', ')', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def build_inventory_ui(inventory: Dict[str, int]) -> Tuple[str, InlineKeyboardMarkup]:
    """Build the inventory UI with text and keyboard layout.
    
    Args:
        inventory: Dictionary of item keys and their counts
        
    Returns:
        Tuple of (formatted text, keyboard markup)
    """
    # Item name mappings
    item_names = {
        "revive_all": "Revive All",
        "emp_field": "EMP Field Device",
        "infinity_scout": "Infinity Scout",
        "hazmat_mask": "Hazmat Mask",
        "speed_up_1h": "1 H Speed-Up",
        "advanced_shield": "Advanced Shield",
        "hazmat_drone": "Hazmat Drone",
        "bm_barrage": "BM Barrage",
        "venom_reapers": "Venom Reapers",
        "titan_crushers": "Titan Crushers"
    }
    
    # Build text sections
    text_parts = ["🎒 *Your Inventory*", "", "*Consumables:*"]
    
    # Consumables section
    consumable_keys = [
        "revive_all", "emp_field", "infinity_scout", "hazmat_mask",
        "speed_up_1h", "advanced_shield", "hazmat_drone"
    ]
    
    for key in consumable_keys:
        count = inventory.get(key, 0)
        name = item_names[key]
        if count == 0:
            text_parts.append(f"• ~{escape_markdown(name)}: 0~")
        else:
            text_parts.append(f"• {escape_markdown(name)}: {count}")
    
    # Black Market Units section
    text_parts.extend(["", "*Black Market Units:*"])
    bm_keys = ["bm_barrage", "venom_reapers", "titan_crushers"]
    
    for key in bm_keys:
        count = inventory.get(key, 0)
        name = item_names[key]
        if count == 0:
            text_parts.append(f"• ~{escape_markdown(name)}: 0~")
        else:
            text_parts.append(f"• {escape_markdown(name)}: {count}")
    
    # Diamonds section
    diamonds = inventory.get("diamonds", 0)
    text_parts.extend(["", f"💎 Diamonds: {diamonds}"])
    
    # Build keyboard
    keyboard = []
    
    # Add consumable buttons
    for key in consumable_keys:
        count = inventory.get(key, 0)
        name = item_names[key]
        row = [InlineKeyboardButton("ℹ️ Info", callback_data=f"inv_info:{key}")]
        if count > 0:
            row.append(InlineKeyboardButton(f"▶️ Use {escape_markdown(name)}", callback_data=f"inv_use:{key}"))
        else:
            row.append(InlineKeyboardButton("🚫", callback_data="noop"))
        keyboard.append(row)
    
    # Add Black Market Unit buttons
    for key in bm_keys:
        count = inventory.get(key, 0)
        name = item_names[key]
        row = [InlineKeyboardButton("ℹ️ Info", callback_data=f"inv_info:{key}")]
        if count > 0:
            row.append(InlineKeyboardButton(f"▶️ Use {escape_markdown(name)}", callback_data=f"inv_use:{key}"))
        else:
            row.append(InlineKeyboardButton("🚫", callback_data="noop"))
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BACK_TO_BASE")])
    
    return "\n".join(text_parts), InlineKeyboardMarkup(keyboard)

async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the player's inventory with grouped items and action buttons."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = get_player_data(user_id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    def safe_int(value, default=0):
        """Safely convert a value to integer, handling empty strings and None."""
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    # Build inventory dictionary
    inventory = {
        "revive_all": safe_int(data.get("items_revive_all")),
        "emp_field": safe_int(data.get("items_emp_device")),
        "infinity_scout": safe_int(data.get("items_infinite_scout")),
        "hazmat_mask": safe_int(data.get("items_hazmat_mask")),
        "speed_up_1h": safe_int(data.get("items_speedup_1h")),
        "advanced_shield": safe_int(data.get("items_shield_adv")),
        "hazmat_drone": safe_int(data.get("items_hazmat_drone")),
        "bm_barrage": safe_int(data.get("army_bm_barrage")),
        "venom_reapers": safe_int(data.get("army_venom_reaper")),
        "titan_crushers": safe_int(data.get("army_titan_crusher")),
        "diamonds": safe_int(data.get("diamonds"))
    }

    # Build UI
    text, reply_markup = build_inventory_ui(inventory)

    # Debug: Print the generated text to console
    print("--- Generated Inventory UI Text ---")
    print(text)
    print("-----------------------------------")

    # Send message
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                text,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Fallback to sending new message if edit fails
            await update.callback_query.message.reply_text(
                text,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
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
            logger.error(f"Error answering callback query: {e}")
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

    def safe_int(value, default=0):
        """Safely convert a value to integer, handling empty strings and None."""
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    # Build keyboard with available items
    keyboard = []
    for key, item in ITEMS.items():
        count = safe_int(data.get(f"items_{key}"))
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

    keyboard.append([InlineKeyboardButton("🏠 Back to Base", callback_data="BACK_TO_BASE")])
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
            logger.error(f"Error answering callback query: {e}")
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
        f"🛠 *Use {escape_markdown(item['name'])}?*\n\n"
        f"{escape_markdown(item['description'])}\n\n"
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
            logger.error(f"Error answering callback query: {e}")
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

    def safe_int(value, default=0):
        """Safely convert a value to integer, handling empty strings and None."""
        if value is None or value == '':
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    # Check item count
    item_field = f"items_{key}"
    current_count = safe_int(data.get(item_field))
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
    app.add_handler(CallbackQueryHandler(inventory_handler, pattern="^BACK_TO_BASE$"))
    app.add_handler(CallbackQueryHandler(show_item_info, pattern="^inv_info:"))
    app.add_handler(CallbackQueryHandler(use_item_callback, pattern="^use_item_"))
    app.add_handler(CallbackQueryHandler(confirm_use_callback, pattern="^confirm_use_"))
    app.add_handler(CallbackQueryHandler(inventory_handler, pattern="^SHOW_INVENTORY$")) 