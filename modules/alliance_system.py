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

async def alliance_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show alliance info based on player's alliance status."""
    user = update.effective_user
    player_data = get_player_data(user.id)
    alliance_name = player_data.get("alliance_name")
    
    msg = ""
    keyboard = []

    if not alliance_name:
        # Scenario 1: Not in an alliance
        msg = (
            "🤝 \*[ALLIANCE INFO]*  \n"
            "You are not currently a member of any alliance."
        )
        keyboard = [
            [InlineKeyboardButton("🛠 Create Alliance", callback_data=f"{ALLIANCE_CB}CREATE")],
            [InlineKeyboardButton("🔍 Search Alliance", callback_data=f"{ALLIANCE_CB}SEARCH")],
            [InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")]
        ]
    else:
        # Scenario 2: In an alliance
        # Fetch alliance details
        all_players = list_all_players()
        leader_name = "N/A"
        for p in all_players:
            if p.get("alliance_name") == alliance_name and p.get("alliance_role") == "leader":
                leader_name = p.get("game_name", "N/A")
                break

        members_in_alliance = [p for p in all_players if p.get("alliance_name") == alliance_name]
        num_members = len(members_in_alliance)
        total_power = sum(p.get("power", 0) for p in members_in_alliance)
        
        controlled_zones_ids = set()
        for p in members_in_alliance:
            if p.get("controlled_zone"):
                controlled_zones_ids.add(p["controlled_zone"])
        
        zones_str = ", ".join(list(controlled_zones_ids)) if controlled_zones_ids else "None"

        alliance_role = player_data.get("alliance_role", "Member")

        # Escape special characters for MarkdownV2
        escaped_alliance_name = escape_markdown_v2(alliance_name)
        escaped_alliance_role = escape_markdown_v2(alliance_role)
        escaped_zones_str = escape_markdown_v2(zones_str)

        msg = (
            f"🤝 \*[ALLIANCE INFO]*  \n"
            f"🛡 Alliance: \*{escaped_alliance_name}\*  \n"
            f"👑 Leader: {escape_markdown_v2(leader_name)}  \n"
            f"👤 Role: {escaped_alliance_role}  \n"
            f"👥 Members: {num_members}/20  \n"
            f"📈 Power: {total_power}  \n"
            f"🌐 Zones: {escaped_zones_str}"
        )
        keyboard = [
            [InlineKeyboardButton("✨ Invite Member", callback_data=f"{ALLIANCE_CB}INVITE_MEMBER"),
             InlineKeyboardButton("⚔️ Declare War", callback_data=f"{ALLIANCE_CB}WAR"),
             InlineKeyboardButton("❌ Leave Alliance", callback_data=f"{ALLIANCE_CB}LEAVE_ALLIANCE")],
            [InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        # Fallback for unexpected update types
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text="An unexpected error occurred. Please try again.",
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

async def alliance_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show alliance menu with inline buttons based on player's alliance status."""
    user = update.effective_user
    player_data = get_player_data(user.id)
    alliance_name = player_data.get("alliance_name")

    msg = ""
    keyboard = []

    if not alliance_name:
        # Scenario 1: Not in an alliance
        msg = (
            "🤝 \*[ALLIANCE COMMAND CENTER]*  \n\n"
            "You are not currently a member of any alliance.\n\n"
            "🔹 \*Create a New Alliance\*  \n"
            "   Cost: 2000 💰 Gold, 1500 🪵 Wood, 1500 🪨 Stone, 1000 🥖 Food  \n"
            "   \[🛠 Create Alliance\]\n\n"
            "🔹 \*Join an Existing Alliance\*  \n"
            "   Search by name or browse the top alliances  \n"
            "   \[🔍 Search Alliance\]   \[📈 Top Alliances\]\n"
        )
        keyboard = [
            [InlineKeyboardButton("🛠 Create Alliance", callback_data=f"{ALLIANCE_CB}CREATE")],
            [InlineKeyboardButton("🔍 Search Alliance", callback_data=f"{ALLIANCE_CB}SEARCH")],
            [InlineKeyboardButton("📈 Top Alliances", callback_data=f"{ALLIANCE_CB}TOP")],
            [InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")]
        ]
    else:
        # Scenario 2: In an alliance
        # Fetch alliance details (stubs for now)
        alliance_leader = "CommanderYanny" # This needs to be fetched from sheets, likely a separate alliance sheet or by scanning players
        num_members = 12 # This needs to be calculated
        total_power = 42100 # This needs to be calculated
        zones_controlled = 2 # This needs to be fetched
        war_status = "None" # This needs to be fetched

        msg = (
            f"🏛️ \*[ {escape_markdown_v2(alliance_name.upper())} HQ ]*\n"
            f"👑 Leader: {escape_markdown_v2(alliance_leader)}\n"
            f"👥 Members: {num_members} / 20\n"
            f"🛡️ Total Power: {total_power}\n"
            f"🌐 Zones Controlled: {zones_controlled}\n"
            f"⏳ War Status: {war_status}\n\n"
            f"🎯 \*Alliance Actions:\*\n"
        )
        keyboard = [
            [InlineKeyboardButton("👥 View Members", callback_data=f"{ALLIANCE_CB}VIEW_MEMBERS"),
             InlineKeyboardButton("💬 Chat", callback_data=f"{ALLIANCE_CB}CHAT"),
             InlineKeyboardButton("📊 Info", callback_data=f"{ALLIANCE_CB}INFO")],
            [InlineKeyboardButton("⚔️ Declare War", callback_data=f"{ALLIANCE_CB}WAR"),
             InlineKeyboardButton("🗺️ Zones", callback_data=f"{ALLIANCE_CB}ZONES"),
             InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            msg,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        print("Error: alliance_main received an update without message or callback_query.")

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
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "create"
    elif action == "SEARCH":
        await query.edit_message_text(
            "🔍 *Search Alliance*\n\n"
            "Please enter the name of the alliance you wish to search for:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "search"
    elif action == "TOP":
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
    elif action == "INFO":
        await alliance_info_handler(update, context) # Changed to call new handler
    elif action == "WAR":
        await query.edit_message_text(
            "⚔️ *Declare War*\n\n"
            "Please enter the enemy alliance name to declare war on:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "war"
    elif action == "ZONES":
        await zones_main(update, context) # Pass update directly, not query
    elif action == "BACK":
        await base_handler(update, context) # Pass update directly, not query
    elif action == "MENU":  # Handle the ALLIANCE_MENU callback from base_ui
        # This action now re-routes to alliance_main to handle the display logic based on alliance status
        await alliance_main(update, context)

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
    app.add_handler(CommandHandler("alliance", alliance_main))
    app.add_handler(CommandHandler("alliance_info", alliance_info_handler)) # Added for direct command
    app.add_handler(CallbackQueryHandler(alliance_callback, pattern=f"^{ALLIANCE_CB}"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.USER, 
        alliance_text_router
    ))