import os
import json
import base64
import datetime
import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── Setup Logging ─────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Google Sheets Auth ───────────────────────────────────
def auth_sheets():
    creds_b64 = os.getenv("GOOGLE_CREDS_BASE64")
    sheet_id = os.getenv("SHEET_ID")
    if not creds_b64 or not sheet_id:
        raise Exception("Environment variables missing.")
    creds_json = base64.b64decode(creds_b64).decode("utf-8")
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_id)


def get_or_create_worksheet(sheet, name, headers):
    try:
        return sheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows="100", cols="20")
        ws.append_row(headers)
        return ws


sheet = auth_sheets()
players_sheet = get_or_create_worksheet(sheet, "Players", ["ID", "Name", "Faction", "Level"])
resources_sheet = get_or_create_worksheet(sheet, "Resources", ["ID", "Gold", "Iron", "Tech", "Crystals"])

# ── Command Center UI ─────────────────────────────────────
async def command_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Resources", callback_data="cmd_resources"),
         InlineKeyboardButton("🛠 Build", callback_data="cmd_build")],
        [InlineKeyboardButton("🧬 Research", callback_data="cmd_research"),
         InlineKeyboardButton("🧑‍✈️ Train", callback_data="cmd_train")],
        [InlineKeyboardButton("🔍 Spy", callback_data="cmd_spy"),
         InlineKeyboardButton("⚔️ Attack", callback_data="cmd_attack")],
        [InlineKeyboardButton("🏪 Store", callback_data="cmd_store"),
         InlineKeyboardButton("📈 Status Panel", callback_data="cmd_status")],
        [InlineKeyboardButton("📬 Inbox", callback_data="inbox_1"),
         InlineKeyboardButton("🌐 Faction", callback_data="choose_faction")]
    ]
    
    # Check for active event
    try:
        events_ws = sheet.worksheet("Events")
        rows = events_ws.get_all_values()
        now = datetime.datetime.utcnow()
        for row in rows[1:]:
            start, end, status = row[1], row[2], row[3]
            if status == "active":
                end_dt = datetime.datetime.fromisoformat(end)
                if now <= end_dt:
                    keyboard.append([InlineKeyboardButton("🎯 Join Event", callback_data="join_event")])
                    break
    except Exception as e:
        logger.error(f"Event check failed: {e}")

    await update.message.reply_text(
        "🏛 *Welcome to your Command Center!*\n\nSelect an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ── Player Registration ──────────────────────────────────
def register_player(user):
    try:
        players = players_sheet.col_values(1)
        resources = resources_sheet.col_values(1)
        if str(user.id) not in players:
            players_sheet.append_row([str(user.id), user.first_name, "None", "0"])
        if str(user.id) not in resources:
            resources_sheet.append_row([str(user.id), 1000, 500, 100, 0])  # Gold, Iron, Tech, Crystals
            logger.info(f"Registered new player: {user.id}")
    except Exception as e:
        logger.error(f"Error registering player: {e}")

# ── /start Command ───────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_player(user)

    await update.message.reply_text(
        f"👋 Welcome, *{user.first_name}!* Your empire awaits.\n\nTap below to open your Command Center:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏛 Open Command Center", callback_data="open_center")]]),
        parse_mode="Markdown"
    )

# ── Main Application Setup ────────────────────────────────
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("BOT_TOKEN not found in environment.")

    application = ApplicationBuilder().token(TOKEN).build()

    # Core Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(open_command_center_callback, pattern="^open_center$"))
    application.add_handler(CallbackQueryHandler(command_center_buttons))

    # Start background jobs
    application.job_queue.run_once(lambda ctx: asyncio.create_task(upgrade_checker(application)), when=1)
    application.job_queue.run_once(lambda ctx: asyncio.create_task(event_scheduler(application)), when=3)
    application.job_queue.run_once(lambda ctx: asyncio.create_task(zone_income_loop(application)), when=5)

    logger.info("SkyHustle bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()

# ── Resource Management ──────────────────────────────────
def load_player_resources(user_id):
    try:
        ids = resources_sheet.col_values(1)
        if str(user_id) in ids:
            row = ids.index(str(user_id)) + 1
            data = resources_sheet.row_values(row)
            return {
                "gold": int(data[1]),
                "iron": int(data[2]),
                "tech": int(data[3]),
                "crystals": int(data[4]),
            }
        return {"gold": 0, "iron": 0, "tech": 0, "crystals": 0}
    except Exception as e:
        logger.error(f"Error loading resources: {e}")
        return {"gold": 0, "iron": 0, "tech": 0, "crystals": 0}

async def show_resource_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    res = load_player_resources(user_id)

    text = (
        "💰 *Your Resources*\n\n"
        f"🪙 Gold: `{res['gold']}`\n"
        f"⛓ Iron: `{res['iron']}`\n"
        f"🧪 Tech: `{res['tech']}`\n"
        f"💎 Crystals: `{res['crystals']}`\n"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="open_center")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ── Building System ──────────────────────────────────────
def load_building_levels(user_id):
    try:
        buildings_ws = sheet.worksheet("Buildings")
        ids = buildings_ws.col_values(1)
        if str(user_id) in ids:
            row = ids.index(str(user_id)) + 1
            data = buildings_ws.row_values(row)
            return {
                "base": int(data[1]),
                "lab": int(data[2]),
                "barracks": int(data[3]),
                "storage": int(data[4]),
            }
        return {"base": 1, "lab": 0, "barracks": 0, "storage": 0}
    except Exception as e:
        logger.error(f"Error loading buildings: {e}")
        return {"base": 1, "lab": 0, "barracks": 0, "storage": 0}

async def show_build_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    levels = load_building_levels(user_id)

    text = (
        "🛠 *Your Buildings*\n\n"
        f"🏰 Base: Level {levels['base']}\n"
        f"🔬 Lab: Level {levels['lab']}\n"
        f"🏋️ Barracks: Level {levels['barracks']}\n"
        f"📦 Storage: Level {levels['storage']}\n\n"
        "Select a building to upgrade:"
    )
    keyboard = [
        [InlineKeyboardButton("⬆️ Upgrade Base", callback_data="upg_base")],
        [InlineKeyboardButton("⬆️ Upgrade Lab", callback_data="upg_lab")],
        [InlineKeyboardButton("⬆️ Barracks", callback_data="upg_barracks")],
        [InlineKeyboardButton("⬆️ Storage", callback_data="upg_storage")],
        [InlineKeyboardButton("⬅️ Back", callback_data="open_center")]
    ]
# ── Event System ─────────────────────────────────────────
async def trigger_event(event_name, duration_min=10, app=None):
    try:
        events_ws = sheet.worksheet("Events")
        now = datetime.datetime.utcnow()
        end = now + datetime.timedelta(minutes=duration_min)
        events_ws.append_row([
            event_name,
            now.isoformat(),
            end.isoformat(),
            "active",
            ""
        ])

        event_info = {
            "pirate": ("💣 Pirate Invasion", "Defend against pirate raids for bonuses!"),
            "meteor": ("🚀 Meteor Rush", "Mine rare resources from falling meteors!"),
            "radiation": ("☢️ Radiation Storm", "Survive for tech bonuses!")
        }

        title, desc = event_info[event_name]
        await broadcast_message(
            f"{title}\n{desc}\n⏳ Ends in {duration_min} minutes!",
            app
        )
    except Exception as e:
        logger.error(f"Event trigger failed: {e}")

async def join_active_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    try:
        events_ws = sheet.worksheet("Events")
        rows = events_ws.get_all_values()
        
        for idx, row in enumerate(rows[1:], start=2):
            if row[3] == "active":
                participants = row[4].split(",") if row[4] else []
                if user_id not in participants:
                    participants.append(user_id)
                    events_ws.update_cell(idx, 5, ",".join(participants))
                    await query.edit_message_text("✅ Joined event! Check inbox for updates.")
                    return
        await query.edit_message_text("❌ No active events")
    except Exception as e:
        logger.error(f"Event join error: {e}")

# ── Faction System ───────────────────────────────────────
async def show_faction_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "🌐 *Choose Your Faction*\n\n"
        "1. 🐺 Nomads - Faster troop training\n"
        "2. 🧠 Technocrats - Cheaper research\n"
        "3. ⚔️ Warlords - Combat bonuses\n\n"
        "This choice is permanent!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🐺 Join Nomads", callback_data="faction_nomads")],
        [InlineKeyboardButton("🧠 Join Technocrats", callback_data="faction_technocrats")],
        [InlineKeyboardButton("⚔️ Join Warlords", callback_data="faction_warlords")],
        [InlineKeyboardButton("⬅️ Back", callback_data="open_center")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def set_faction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    faction = query.data.replace("faction_", "").title()

    try:
        players_ws = sheet.worksheet("Players")
        ids = players_ws.col_values(1)
        row = ids.index(user_id) + 1
        players_ws.update_cell(row, 3, faction)
        await query.edit_message_text(f"✅ Joined {faction} faction!")
        save_inbox_message(user_id, "Faction", f"You joined the {faction} faction")
    except Exception as e:
        logger.error(f"Faction error: {e}")
        await query.edit_message_text("❌ Faction selection failed")

# ── Enhanced Callback Handler ────────────────────────────
async def command_center_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Core commands
    if data == "cmd_resources":
        await show_resource_panel(update, context)
    elif data == "cmd_build":
        await show_build_menu(update, context)
    elif data.startswith("upg_"):
        await handle_building_upgrade(data, update, context)
    
    # Event system
    elif data == "join_event":
        await join_active_event(update, context)
    
    # Faction system
    elif data == "choose_faction":
        await show_faction_menu(update, context)
    elif data.startswith("faction_"):
        await set_faction(update, context)
    
    else:
        await query.edit_message_text("🚧 Feature in development")

# ── Background Tasks ─────────────────────────────────────
async def event_scheduler(app):
    await asyncio.sleep(10)
    while True:
        try:
            events_ws = sheet.worksheet("Events")
            active_events = [e for e in events_ws.get_all_values()[1:] if e[3] == "active"]
            
            if not active_events:
                await trigger_event(random.choice(["pirate", "meteor", "radiation"]), app)
            
            await asyncio.sleep(3600)  # Check hourly
        except Exception as e:
            logger.error(f"Event scheduler error: {e}")
            await asyncio.sleep(60)

async def broadcast_message(text, app):
    try:
        player_ids = players_sheet.col_values(1)[1:]  # Skip header
        for pid in player_ids:
            try:
                await app.bot.send_message(chat_id=pid, text=text, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Broadcast failed to {pid}: {e}")
    except Exception as e:
        logger.error(f"Broadcast failed: {e}")

def save_inbox_message(user_id, msg_type, content):
    try:
        inbox_ws = sheet.worksheet("Inbox")
        inbox_ws.append_row([
            str(user_id),
            datetime.datetime.utcnow().isoformat(),
            msg_type,
            content
        ])
    except Exception as e:
        logger.error(f"Inbox save failed: {e}")

# ── PvP Combat Core ──────────────────────────────────────
def init_pvp_profile(user_id):
    try:
        pvp_ws = sheet.worksheet("PvPHealth")
        if str(user_id) not in pvp_ws.col_values(1):
            pvp_ws.append_row([str(user_id), 100, 20])  # HP, Defense
    except Exception as e:
        logger.error(f"PvP init error: {e}")

def calculate_damage(attacker_id, defender_id, base_dmg=100):
    try:
        # Faction bonuses
        attacker_faction = get_player_faction(attacker_id)
        if attacker_faction == "warlords":
            base_dmg *= 1.2

        # Defense calculation
        pvp_ws = sheet.worksheet("PvPHealth")
        defender_def = int(pvp_ws.find(str(defender_id)).row_values(3)[1])
        return max(0, base_dmg - defender_def)
    except Exception as e:
        logger.error(f"Damage calc error: {e}")
        return 100

async def pvp_attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        attacker_id = str(update.effective_user.id)
        defender_id = context.args[0]
        
        if attacker_id == defender_id:
            await update.message.reply_text("❌ Can't attack yourself!")
            return

        damage = calculate_damage(attacker_id, defender_id)
        
        # Update defender HP
        pvp_ws = sheet.worksheet("PvPHealth")
        defender_row = pvp_ws.find(defender_id).row
        current_hp = int(pvp_ws.cell(defender_row, 2).value)
        pvp_ws.update_cell(defender_row, 2, max(0, current_hp - damage))

        # Log battle
        log_ws = sheet.worksheet("BattleLog")
        log_ws.append_row([
            attacker_id,
            defender_id,
            damage,
            "survived" if (current_hp - damage) > 0 else "defeated",
            datetime.datetime.utcnow().isoformat()
        ])

        # Send notifications
        result_msg = (
            f"⚔️ *Combat Report*\n"
            f"Attacker: {get_player_name(attacker_id)}\n"
            f"Damage: {damage}\n"
            f"Defender HP: {max(0, current_hp - damage)}/100"
        )
        await update.message.reply_text(result_msg, parse_mode="Markdown")
        save_inbox_message(defender_id, "⚔️ Attacked", 
                          f"You were attacked by {get_player_name(attacker_id)}!")

    except Exception as e:
        logger.error(f"Attack error: {e}")
        await update.message.reply_text("⚠️ Attack failed")

# ── Store System ─────────────────────────────────────────
STORE_ITEMS = {
    "resource_pack": {
        "name": "📦 Resource Pack",
        "cost": 50,
        "effect": {"gold": 500, "iron": 300}
    },
    "instant_build": {
        "name": "⚡ Instant Build",
        "cost": 100,
        "effect": "skip_build_time"
    }
}

async def show_store_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🏪 *Game Store*\n\n"
    buttons = []
    
    for item_id, item in STORE_ITEMS.items():
        text += f"{item['name']} - 💎{item['cost']}\n"
        buttons.append([InlineKeyboardButton(
            f"Buy {item['name']}", 
            callback_data=f"buy_{item_id}"
        )])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="open_center")])
    await query.edit_message_text(text, 
                                reply_markup=InlineKeyboardMarkup(buttons),
                                parse_mode="Markdown")

async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.split("_")[1]
    user_id = str(query.from_user.id)
    
    try:
        item = STORE_ITEMS[item_id]
        res_ws = sheet.worksheet("Resources")
        user_row = res_ws.find(user_id).row
        crystals = int(res_ws.cell(user_row, 5).value)
        
        if crystals < item["cost"]:
            await query.edit_message_text("❌ Not enough crystals!")
            return
            
        # Process transaction
        res_ws.update_cell(user_row, 5, crystals - item["cost"])
        
        # Apply effect
        if isinstance(item["effect"], dict):
            for res, amt in item["effect"].items():
                col = {"gold":2, "iron":3, "tech":4}[res]
                current = int(res_ws.cell(user_row, col).value)
                res_ws.update_cell(user_row, col, current + amt)
        
        await query.edit_message_text(f"✅ Purchased {item['name']}!")
        save_inbox_message(user_id, "🛒 Purchase", 
                          f"Bought {item['name']} for 💎{item['cost']}")

    except Exception as e:
        logger.error(f"Purchase error: {e}")
        await query.edit_message_text("⚠️ Purchase failed")

# ── Enhanced Callback Handler ────────────────────────────
async def command_center_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Existing handlers...
    
    # Combat system
    if data.startswith("attack_"):
        await handle_special_attack(update, context)
    
    # Store system
    elif data == "cmd_store":
        await show_store_menu(update, context)
    elif data.startswith("buy_"):
        await handle_purchase(update, context)
    
    # Add remaining handlers...

# ── Support Commands ─────────────────────────────────────
async def heal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        res_ws = sheet.worksheet("Resources")
        pvp_ws = sheet.worksheet("PvPHealth")
        
        # Check resources
        user_row = res_ws.find(user_id).row
        tech = int(res_ws.cell(user_row, 4).value)
        if tech < 50:
            await update.message.reply_text("❌ Need 50 Tech to heal!")
            return
            
        # Update HP and resources
        pvp_row = pvp_ws.find(user_id).row
        pvp_ws.update_cell(pvp_row, 2, 100)
        res_ws.update_cell(user_row, 4, tech - 50)
        
        await update.message.reply_text("💉 Fully healed!")
        save_inbox_message(user_id, "❤️ Healed", "Used 50 Tech to heal")
        
    except Exception as e:
        logger.error(f"Heal error: {e}")
        await update.message.reply_text("⚠️ Heal failed")

async def battle_log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        log_ws = sheet.worksheet("BattleLog")
        battles = [row for row in log_ws.get_all_values()[1:] 
                 if row[0] == user_id or row[1] == user_id]
        
        text = "📜 *Battle History*\n\n"
        for battle in battles[-5:]:  # Show last 5
            text += f"{battle[4]}: {'Won' if battle[3] == 'defeated' else 'Fought'}\n"
            
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Battle log error: {e}")
        await update.message.reply_text("⚠️ Couldn't load history")

# Add to main application setup
def main():
    # Existing setup...
    
    # New command handlers
    application.add_handler(CommandHandler("attack", pvp_attack_command))
    application.add_handler(CommandHandler("heal", heal_command))
    application.add_handler(CommandHandler("battles", battle_log_command))
# ── Black Market System ──────────────────────────────────
BLACK_MARKET_ITEMS = {
    "emp_device": {
        "name": "⚡ EMP Device",
        "cost": 200,
        "effect": "disable_defenses",
        "duration": 3600
    },
    "clone_army": {
        "name": "👥 Clone Army",
        "cost": 500,
        "effect": "instant_troops"
    }
}

async def show_blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🕶 *Black Market*\n\n"
    buttons = []
    for item_id, item in BLACK_MARKET_ITEMS.items():
        text += f"{item['name']} - 💎{item['cost']}\n"
        buttons.append([InlineKeyboardButton(
            f"Buy {item['name']}", 
            callback_data=f"bm_buy_{item_id}"
        )])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="cmd_store")])
    await query.edit_message_text(text, 
                                reply_markup=InlineKeyboardMarkup(buttons),
                                parse_mode="Markdown")

async def handle_blackmarket_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    item_id = query.data.split("_")[-1]

    try:
        # Verify purchase
        item = BLACK_MARKET_ITEMS[item_id]
        res_ws = sheet.worksheet("Resources")
        row = res_ws.find(user_id).row
        crystals = int(res_ws.cell(row, 5).value)
        
        if crystals < item["cost"]:
            await query.edit_message_text("❌ Not enough crystals!")
            return
            
        # Process transaction
        res_ws.update_cell(row, 5, crystals - item["cost"])
        
        # Add to inventory
        bm_ws = sheet.worksheet("BlackMarket")
        try:
            bm_row = bm_ws.find(user_id).row
            current = bm_ws.cell(bm_row, 2).value
            bm_ws.update_cell(bm_row, 2, f"{current},{item_id}")
        except gspread.exceptions.CellNotFound:
            bm_ws.append_row([user_id, item_id])

        await query.edit_message_text(f"✅ Acquired {item['name']}!")
        save_inbox_message(user_id, "🕶 Black Market", 
                          f"Purchased {item['name']}")

    except Exception as e:
        logger.error(f"BM purchase failed: {e}")
        await query.edit_message_text("⚠️ Transaction failed")

# ── Item Usage System ────────────────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        args = context.args
        
        if not args:
            await update.message.reply_text("Usage: /use <item>")
            return
            
        item_id = args[0]
        bm_ws = sheet.worksheet("BlackMarket")
        user_row = bm_ws.find(user_id).row
        items = bm_ws.cell(user_row, 2).value.split(",")
        
        if item_id not in items:
            await update.message.reply_text("❌ You don't own this item")
            return
            
        # Apply item effect
        item = BLACK_MARKET_ITEMS[item_id]
        if item["effect"] == "disable_defenses":
            await disable_defenses(user_id, item["duration"])
        elif item["effect"] == "instant_troops":
            await instant_troops(user_id)
            
        # Remove from inventory
        items.remove(item_id)
        bm_ws.update_cell(user_row, 2, ",".join(items))
        
        await update.message.reply_text(f"⚡ Used {item['name']}!")

    except Exception as e:
        logger.error(f"Item use error: {e}")
        await update.message.reply_text("⚠️ Failed to use item")

# ── Admin Commands ───────────────────────────────────────
async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"  # Replace with your ID
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
        
    try:
        target_id = context.args[0]
        resource = context.args[1]
        amount = int(context.args[2])
        
        res_ws = sheet.worksheet("Resources")
        row = res_ws.find(target_id).row
        col = {"gold":2, "iron":3, "tech":4, "crystals":5}[resource]
        current = int(res_ws.cell(row, col).value)
        res_ws.update_cell(row, col, current + amount)
        
        await update.message.reply_text(f"✅ Granted {amount} {resource}")
        save_inbox_message(target_id, "🎁 Admin Grant",
                          f"Received {amount} {resource}")

    except Exception as e:
        logger.error(f"Grant error: {e}")
        await update.message.reply_text("⚠️ Grant failed")

async def wipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
        
    try:
        sheets_to_wipe = ["Players", "Resources", "Buildings", "PvPHealth"]
        for sheet_name in sheets_to_wipe:
            ws = sheet.worksheet(sheet_name)
            ws.clear()
            ws.append_row(ws.row_values(1))  # Keep headers
            
        await update.message.reply_text("🧹 Full game reset complete!")
    except Exception as e:
        logger.error(f"Wipe error: {e}")
        await update.message.reply_text("⚠️ Reset failed")

# ── Final Application Setup ──────────────────────────────

# ── Missing Command Handlers (STUBS) ─────────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧪 Use Item command triggered. [TODO]")

async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 Grant command triggered. [TODO]")

async def wipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Wipe command triggered. [TODO]")

async def command_center_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("🛠 Command button clicked. [TODO]")

async def open_command_center_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("🏛 Opening Command Center... [TODO]")

def check_ongoing_events():
    logger.info("⏱ Checking ongoing events... [TODO]")

def award_daily_bonuses():
    logger.info("🎉 Awarding daily bonuses... [TODO]")


def main():
    TOKEN = os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    # Core commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("use", use_item_command))
    application.add_handler(CommandHandler("grant", grant_command))
    application.add_handler(CommandHandler("wipe", wipe_command))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(command_center_buttons))
    application.add_handler(CallbackQueryHandler(
        lambda u,c: open_command_center_callback(u,c), 
        pattern="^open_center$"
    ))

    # Background jobs
    application.job_queue.run_repeating(
        lambda c: check_ongoing_events(),
        interval=300,
        first=10
    )
    application.job_queue.run_daily(
        lambda c: award_daily_bonuses(),
        time=datetime.time(0, 0, 0)
    )

    logger.info("🟢 SkyHustle fully operational")
    application.run_polling()

# ── Helper Functions ─────────────────────────────────────
def get_player_faction(user_id):
    try:
        ws = sheet.worksheet("Players")
        row = ws.find(str(user_id)).row
        return ws.cell(row, 3).value.lower()
    except:
        return "none"

def save_inbox_message(user_id, category, message):
    try:
        ws = sheet.worksheet("Inbox")
        ws.append_row([
            str(user_id),
            datetime.datetime.utcnow().isoformat(),
            category,
            message
        ])
    except Exception as e:
        logger.error(f"Inbox save failed: {e}")

if __name__ == "__main__":
    main()
