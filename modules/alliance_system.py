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

# Callback data prefixes
ALLIANCE_CB = "ALLIANCE_"

ZONES = [
    {"id":"greenvale","name":"🌲 Greenvale","def":4000,"bonus":"+10% Wood"},
    {"id":"stonecrack","name":"🪨 Stonecrack","def":4500,"bonus":"+10% Stone"},
    {"id":"riverbend","name":"🌊 Riverbend","def":3800,"bonus":"+10% Food"},
    {"id":"goldmine","name":"💰 Goldmine","def":5000,"bonus":"+10% Gold"},
    {"id":"ironpeak","name":"🔩 Ironpeak","def":4200,"bonus":"+10% Iron"}, # Assuming iron is a resource too, add if not
    {"id":"crystalcaverns","name":"💎 Crystal Caverns","def":4800,"bonus":"+10% Diamonds"},
    {"id":"barrenlands","name":"🏜️ Barren Lands","def":3500,"bonus":"+5% XP"},
    {"id":"whisperingwoods","name":"🌳 Whispering Woods","def":3700,"bonus":"+5% Energy"},
    {"id":"shadowfen","name":"🌑 Shadowfen","def":4100,"bonus":"+5% Power"},
    {"id":"sunstoneplateau","name":"☀️ Sunstone Plateau","def":4300,"bonus":"+5% Prestige"},
    {"id":"frostbitemountains","name":"🏔️ Frostbite Mountains","def":4600,"bonus":"+10% Building Speed"},
    {"id":"ancientruins","name":"🏛️ Ancient Ruins","def":4900,"bonus":"+10% Research Speed"},
    {"id":"strategic_outpost1","name":"📡 Strategic Outpost Alpha","def":6000,"bonus":"Unlock Alpha Zone"},
    {"id":"strategic_outpost2","name":"📡 Strategic Outpost Beta","def":6200,"bonus":"Unlock Beta Zone"},
    {"id":"strategic_outpost3","name":"📡 Strategic Outpost Gamma","def":6400,"bonus":"Unlock Gamma Zone"},
    {"id":"strategic_outpost4","name":"📡 Strategic Outpost Delta","def":6600,"bonus":"Unlock Delta Zone"},
    {"id":"strategic_outpost5","name":"📡 Strategic Outpost Epsilon","def":6800,"bonus":"Unlock Epsilon Zone"},
    {"id":"strategic_outpost6","name":"📡 Strategic Outpost Zeta","def":7000,"bonus":"Unlock Zeta Zone"},
    {"id":"radiation_zone1","name":"☣️ Radiation Zone I","def":7500,"bonus":"Unique Resource A"},
    {"id":"radiation_zone2","name":"☣️ Radiation Zone II","def":7800,"bonus":"Unique Resource B"},
    {"id":"radiation_zone3","name":"☣️ Radiation Zone III","def":8000,"bonus":"Unique Resource C"},
    {"id":"capital_city","name":"👑 Capital City","def":10000,"bonus":"Global Buffs"},
]


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
    await context.bot.send_message(chat_id,f"✅ You joined alliance *{name}*.", parse_mode=constants.ParseMode.MARKDOWN)

async def alliance_info(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    user=update.effective_user; chat_id=update.effective_chat.id
    data=get_player_data(user.id)
    name=data.get("alliance_name")
    if not name:
        return await context.bot.send_message(chat_id,"❌ You're not in an alliance.")
    members=[p for p in list_all_players() if p.get("alliance_name")==name]
    total_power=sum(p.get("power",0) for p in members)
    text=f"🤝 *Alliance: {name}*  \nMembers: {len(members)}  \nPower: {total_power}\n\n👥 Member list:\n"
    for p in members:
        text+=f"• {p['game_name']} — {p.get('power',0)}\n"
    await context.bot.send_message(chat_id,text,parse_mode=constants.ParseMode.MARKDOWN)

async def zones_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id=update.effective_chat.id; data=get_player_data(update.effective_user.id)
    text="🗺️ *Zone Control Panel*\n\n"
    for z in ZONES:
        owner="– Unclaimed"
        # find which alliance holds it: scan members whose data.get("controlled_zone")==z["id"]
        # for simplicity skip owner for now
        text+=f"{z['name']} — Def: {z['def']} — Bonus: {z['bonus']}\n"
    buttons=[[InlineKeyboardButton("🏠 Back to Base",callback_data="Z_CANCEL")]]
    await context.bot.send_message(chat_id,text,parse_mode=constants.ParseMode.MARKDOWN,reply_markup=InlineKeyboardMarkup(buttons))

async def alliance_war(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    user=update.effective_user; chat_id=update.effective_chat.id
    data=get_player_data(user.id)
    if data.get("alliance_role")!="leader":
        return await context.bot.send_message(chat_id,"❌ Only alliance leaders can schedule zone attacks.")
    if not args:
        return await context.bot.send_message(chat_id,"Usage: /alliance war <zone_id>")
    zid=args[0]; zone=next((z for z in ZONES if z["id"]==zid),None)
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
    await context.bot.send_message(chat_id,f"✅ Zone {zone['name']} attack scheduled for 6h from now.")

async def alliance_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show alliance menu with inline buttons based on player's alliance status."""
    user = update.effective_user
    player_data = get_player_data(user.id)
    alliance_name = player_data.get("alliance_name")

    if not alliance_name:
        # Scenario 1: Not in an alliance
        msg = (
            "🤝 *[ ALLIANCE COMMAND CENTER ]*\n\n"
            "You are not currently a member of any alliance.\n\n"
            "🔹 *Create a New Alliance*\n"
            "   Cost: 2000 💰 Gold, 1500 🪵 Wood, 1500 🪨 Stone, 1000 🥖 Food\n"
            "   [🛠 Create Alliance]\n\n"
            "🔹 *Join an Existing Alliance*\n"
            "   Search by name or browse the top alliances\n"
            "   [🔍 Search Alliance]   [📈 Top Alliances]\n"
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
            f"🏛️ *[ {alliance_name.upper()} HQ ]*\n"
            f"👑 Leader: {alliance_leader}\n"
            f"👥 Members: {num_members} / 20\n"
            f"🛡️ Total Power: {total_power}\n"
            f"🌐 Zones Controlled: {zones_controlled}\n"
            f"⏳ War Status: {war_status}\n\n"
            f"🎯 *Alliance Actions:*\n"
        )
        keyboard = [
            [InlineKeyboardButton("👥 View Members", callback_data=f"{ALLIANCE_CB}VIEW_MEMBERS"),
             InlineKeyboardButton("💬 Chat", callback_data=f"{ALLIANCE_CB}CHAT"),
             InlineKeyboardButton("📊 Info", callback_data=f"{ALLIANCE_CB}INFO")],
            [InlineKeyboardButton("⚔️ Declare War", callback_data=f"{ALLIANCE_CB}WAR"),
             InlineKeyboardButton("🗺️ Zones", callback_data=f"{ALLIANCE_CB}ZONES"),
             InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ALLIANCE_CB}BACK")]
        ]

    await update.message.reply_text(
        msg,
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def alliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dispatch the alliance submenu buttons."""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith(ALLIANCE_CB):
        return # Ignore callbacks not starting with ALLIANCE_CB
        
    action = query.data[len(ALLIANCE_CB):]  # e.g. "CREATE", "JOIN"...
    
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
        await handle_alliance_info(query, context)
    elif action == "WAR":
        await query.edit_message_text(
            "⚔️ *Declare War*\n\n"
            "Please enter the enemy alliance name to declare war on:",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        context.user_data["alliance_next"] = "war"
    elif action == "ZONES":
        from modules.zone_system import zones_main
        await zones_main(query, context)
    elif action == "BACK":
        from modules.base_ui import base_handler
        await base_handler(update, context)
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

async def handle_alliance_info(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle alliance info display in callback context."""
    user = query.from_user
    data = get_player_data(user.id)
    name = data.get("alliance_name")
    if not name:
        await query.edit_message_text("❌ You're not in an alliance.")
        return
    members = [p for p in list_all_players() if p.get("alliance_name")==name]
    total_power = sum(p.get("power",0) for p in members)
    text = f"🤝 *Alliance: {name}*\nMembers: {len(members)}\nPower: {total_power}\n\n👥 Member list:\n"
    for p in members:
        text += f"• {p['game_name']} — {p.get('power',0)}\n"
    await query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN)

def setup_alliance_system(app: Application) -> None:
    app.add_handler(CommandHandler("alliance", alliance_main))
    app.add_handler(CallbackQueryHandler(alliance_callback, pattern=f"^{ALLIANCE_CB}"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.USER, 
        alliance_text_router
    ))
    app.add_handler(CommandHandler("zones", zones_list))
    app.add_handler(CallbackQueryHandler(lambda u,c: c.bot.send_message(u.effective_chat.id,"🏠 Back to Base"), pattern="^Z_CANCEL$")) 