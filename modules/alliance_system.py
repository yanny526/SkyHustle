import os
import re
from typing import Dict, Any, List, Optional
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
    CallbackQuery,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.sheets_helper import get_player_data, update_player_data, list_all_players
from datetime import datetime, timedelta
from modules.base_ui import base_handler # Import base_handler for 'Back to Base'
from modules.zone_system import zones_main # Import zones_main for 'Zones' button


# Callback data prefixes
ALLIANCE_CB = "ALLIANCE_"

# Function to escape MarkdownV2 special characters
def escape_markdown_v2(text: str) -> str:
    # List of characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)

async def alliance_create(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    user = update.effective_user; chat_id = update.effective_chat.id
    if len(args)!=1:
        return await context.bot.send_message(chat_id, "Usage: /alliance create <name>")
    name = args[0]
    data = get_player_data(user.id)
    if data.get("alliance_name"):
        return await context.bot.send_message(chat_id, "❌ You're already in an alliance.")
    # Cost check
    cost = {"gold":2000,"wood":1500,"stone":1500,"food":1000}
    for r,v in cost.items():
        if data[f"resources_{r}"]<v:
            return await context.bot.send_message(chat_id,f"❌ Not enough {r}.")
    for r,v in cost.items():
        update_player_data(user.id,f"resources_{r}",data[f"resources_{r}"]-v)
    # Assign
    update_player_data(user.id,"alliance_name",name)
    update_player_data(user.id,"alliance_role","leader")
    # update alliance_members_count for new alliance leader
    update_player_data(user.id, "alliance_members_count", 1)
    await context.bot.send_message(chat_id,f"✅ Alliance *{name}* created! You are Leader.", parse_mode=constants.ParseMode.MARKDOWN)

async def alliance_join(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    user=update.effective_user; chat_id=update.effective_chat.id
    if len(args)!=1:
        return await context.bot.send_message(chat_id,"Usage: /alliance join <name>")
    name=args[0]; data=get_player_data(user.id)
    if data.get("alliance_name"):
        return await context.bot.send_message(chat_id,"❌ Already in an alliance.")
    # Check alliance exists (by scanning all players)
    members=[p for p in list_all_players() if p.get("alliance_name")==name]
    if not members:
        return await context.bot.send_message(chat_id,"❌ Alliance not found.")
    # Join
    update_player_data(user.id,"alliance_name",name)
    update_player_data(user.id,"alliance_role","member")
    # increment alliance_members_count for joining member
    for member in members:
        if member.get("alliance_role") == "leader": # Assuming leader holds the count
            update_player_data(member["user_id"], "alliance_members_count", member.get("alliance_members_count", 0) + 1)
            break # Only update the leader's count
    await context.bot.send_message(chat_id,f"✅ You joined alliance *{name}*.", parse_mode=constants.ParseMode.MARKDOWN)

async def alliance_war(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    user=update.effective_user; chat_id=update.effective_chat.id
    data=get_player_data(user.id)
    if data.get("alliance_role")!="leader":
        return await context.bot.send_message(chat_id,"❌ Only alliance leaders can schedule zone attacks.")
    if not args:
        return await context.bot.send_message(chat_id,"Usage: /alliance war <zone_id>")
    
    # Using zones from modules.zone_system
    from modules.zone_system import get_all_zones
    zones = get_all_zones()
    
    zid=args[0]; zone=next((z for z in zones if z["id"]==zid),None)
    if not zone:
        return await context.bot.send_message(chat_id,"❌ Invalid zone ID.")
    # check Hazmat for radiation zones
    if zid.startswith("radiation"):
        # count members with hazmat
        members=[p for p in list_all_players() if p.get("alliance_name")==data["alliance_name"]]
        have=sum(1 for m in members if m.get("items_hazmat_mask",0)>0)
        if have<5:
            return await context.bot.send_message(chat_id,"❌ Need 5 Hazmat Masks across alliance.")
    # schedule 6h from now
    sched=(datetime.utcnow()+timedelta(hours=6)).isoformat()+"Z"
    update_player_data(user.id,"scheduled_zone",zid)
    update_player_data(user.id,"scheduled_time",sched)
    await context.bot.send_message(chat_id,f"✅ Zone {zone['name']} attack scheduled for 6h from now.", parse_mode=constants.ParseMode.MARKDOWN)

async def alliance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_player_data(user_id)  # includes keys: alliance_name, alliance_role, alliance_members_count, alliance_power, zones_controlled

    text = ""
    buttons = []

    if not data.get("alliance_name"):
        # not in any alliance
        text = (
            "🤝 \*[ ALLIANCE COMMAND CENTER ]*\n\n"
            "You are not currently a member of any alliance.\n\n"
            f"🔹 \*Create a New Alliance\*\n"
            f"Cost: {escape_markdown_v2('2000 💰, 1500 🪵, 1500 🪨, 1000 🥖')}\n\n"
            f"🔹 \*Join an Existing Alliance\*\n"
            f"Search by name or browse the top alliances{escape_markdown_v2(".")}"
        )
        buttons = [
            [InlineKeyboardButton("🛠 Create Alliance", callback_data=f"{ALLIANCE_CB}CREATE")],
            [InlineKeyboardButton("🔍 Search Alliance", callback_data=f"{ALLIANCE_CB}SEARCH")],
            [InlineKeyboardButton("📈 Top Alliances", callback_data=f"{ALLIANCE_CB}LIST")],
            [InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")],
        ]
    else:
        # already in an alliance
        name = data["alliance_name"]
        role = data.get("alliance_role", "Member")
        members = data.get("alliance_members_count", 0)
        power = data.get("alliance_power", 0)
        zones = data.get("zones_controlled", "None")
        if isinstance(zones, list):
            zones = ", ".join(zones) if zones else "None"

        text = (
            f"🤝 \*[ ALLIANCE INFO ]*\n\n"
            f"🛡 \*Alliance:\* {escape_markdown_v2(name)}\n"
            f"👤 \*Your Role:\* {escape_markdown_v2(role)}\n"
            f"👥 \*Members:\* {members}/20\n"
            f"📈 \*Power:\* {power}\n"
            f"🌐 \*Zones Controlled:\* {escape_markdown_v2(zones)}"
        )
        buttons = [
            [InlineKeyboardButton("✨ Invite Member", callback_data=f"{ALLIANCE_CB}INVITE")],
            [InlineKeyboardButton("⚔️ Declare War", callback_data=f"{ALLIANCE_CB}WAR")],
            [InlineKeyboardButton("❌ Leave Alliance", callback_data=f"{ALLIANCE_CB}LEAVE")],
            [InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")],
        ]

    reply_markup = InlineKeyboardMarkup(buttons)
    
    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        print("Error: alliance_handler received an update without message or callback_query.")

async def alliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dispatch the alliance submenu buttons."""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(ALLIANCE_CB):
        return # Ignore callbacks not starting with ALLIANCE_CB
        
    action = query.data[len(ALLIANCE_CB):]  # e.g. "CREATE", "JOIN"..."
    
    # If the user is not in alliance
    if action == "CREATE":
        await query.edit_message_text(
            "🛠️ *Create Alliance*\n\n"
            "Please enter your desired alliance name:\n"
            "(2000 💰 gold, 1500 🪵 wood, 1500 🪨 stone, 1000 🥖 food)",
            parse_mode=constants.ParseMode.MARKDOWN # Markdown not V2 for input prompts
        )
        context.user_data["alliance_next"] = "create"
    elif action == "SEARCH":
        await query.edit_message_text(
            "🔍 *Search Alliance*\n\n"
            "Please enter the name of the alliance you wish to search for:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "search"
    elif action == "LIST": # Changed from TOP
        await query.edit_message_text(
            "📈 *Top Alliances*\n\n"
            "(This feature is under development. Here you would see a list of top alliances.)",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    elif action == "JOIN": # This was for /alliance join, now it's for button
        await query.edit_message_text(
            "🔍 *Join Alliance*\n\n"
            "Please enter the exact alliance name you wish to join:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "join"
    
    # If the user is in alliance
    elif action == "VIEW_MEMBERS":
        await query.edit_message_text(
            "👥 *Alliance Members*\n\n"
            "(This feature is under development. Here you would see a list of alliance members.)",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    elif action == "CHAT":
        await query.edit_message_text(
            "💬 *Alliance Chat*\n\n"
            "(This feature is under development. Here you would see alliance chat options.)",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    elif action == "INFO": # This will now call the unified handler
        await alliance_handler(update, context)
    elif action == "WAR":
        await query.edit_message_text(
            "⚔️ *Declare War*\n\n"
            "Please enter the enemy alliance name to declare war on:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "war"
    elif action == "ZONES":
        await zones_main(update, context) 
    elif action == "BACK":
        await base_handler(update, context)
    elif action == "MENU":  # Handle the ALLIANCE_MENU callback from base_ui
        await alliance_handler(update, context) # Re-route to unified handler
    elif action == "INVITE": # Changed from INVITE_MEMBER
        await query.edit_message_text(
            "✨ *Invite Member*\n\n"
            "(This feature is under development. Here you would invite members.)",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    elif action == "LEAVE": # Changed from LEAVE_ALLIANCE
        await query.edit_message_text(
            "❌ *Leave Alliance*\n\n"
            "(This feature is under development. Here you would confirm leaving the alliance.)",
            parse_mode=constants.ParseMode.MARKDOWN
        )

async def alliance_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive text after a submenu button was pressed."""
    user = update.effective_user
    text = update.message.text.strip()
    next_action = context.user_data.get("alliance_next")
    
    if not next_action:
        await update.message.reply_text("❌ Please use /alliance to start.")
        return
        
    try:
        if next_action == "create":
            await alliance_create(update, context, [text])
        elif next_action == "join":
            await alliance_join(update, context, [text])
        elif next_action == "war":
            await alliance_war(update, context, [text])
    finally:
        # Clear the next action regardless of success/failure
        context.user_data.pop("alliance_next", None)

def setup_alliance_system(app: Application) -> None:
    app.add_handler(CommandHandler("alliance", alliance_handler)) # Unified handler
    app.add_handler(CallbackQueryHandler(alliance_callback, pattern=f"^{ALLIANCE_CB}"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.USER, 
        alliance_text_router
    ))