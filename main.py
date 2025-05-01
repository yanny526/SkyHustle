import os
import json
import base64
import datetime
import asyncio
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
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

sheet = auth_sheets()
players_sheet = sheet.worksheet("Players")
resources_sheet = sheet.worksheet("Resources")

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
    ]
    await update.message.reply_text(
        "🏛 *Welcome to your Command Center!*\n\nSelect an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
# ── Handle Command Center Buttons ─────────────────────────────
async def command_center_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cmd_resources":
        await query.edit_message_text("💰 *Resources Panel* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_build":
        await query.edit_message_text("🛠 *Build Menu* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_research":
        await query.edit_message_text("🧬 *Research Menu* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_train":
        await query.edit_message_text("🧑‍✈️ *Train Troops* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_spy":
        await query.edit_message_text("🔍 *Spy Operations* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_attack":
        await query.edit_message_text("⚔️ *Attack Nearby Player* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_store":
        await query.edit_message_text("🏪 *Game Store* (Coming soon...)", parse_mode="Markdown")
    elif data == "cmd_status":
        await query.edit_message_text("📈 *Status Panel* (Coming soon...)", parse_mode="Markdown")
    else:
        await query.edit_message_text("❓ Unknown command.")

# ── Helper: Initialize Player on First Start ─────────────────────
def register_player(user):
    try:
        players = players_sheet.col_values(1)
        if str(user.id) not in players:
            players_sheet.append_row([str(user.id), user.first_name, "None", "0"])
            resources_sheet.append_row([str(user.id), 1000, 500, 100, 0])  # Gold, Iron, Tech, Crystals
            logger.info(f"Registered new player: {user.id}")
    except Exception as e:
        logger.error(f"Error registering player: {e}")

# ── /start Command ───────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_player(user)

    await update.message.reply_text(
        f"👋 Welcome, *{user.first_name}!* Your empire awaits.\n\nTap below to open your Command Center:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏛 Open Command Center", callback_data="open_center")]]),
        parse_mode="Markdown"
    )
# ── Handle 'Open Command Center' Callback ─────────────────────
async def open_command_center_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await command_center(update, context)

# ── Main Function ─────────────────────────────────────────────
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise Exception("BOT_TOKEN not found in environment.")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("use", use_blackmarket_item))
    application.add_handler(CommandHandler("inventory", show_inventory))
    application.add_handler(CommandHandler("zones", show_zone_list))
    application.add_handler(CommandHandler("myzones", show_my_zones))
    application.add_handler(CommandHandler("status", show_status_panel))
    application.add_handler(CommandHandler("attack", pvp_attack_command))
    application.add_handler(CommandHandler("heal", heal_command))
    application.add_handler(CommandHandler("battlelog", show_battle_log))
    # ... all other handlers and startup logic


# ── Zone Buff Rewards Mapping ─────────────────────────────────
ZONE_REWARDS = {
    "desert_outpost": {"iron": 20},
    "tech_ruins": {"tech": 10},
    "warlord_gate": {"pvp_buff": 1}  # Flag for PvP bonus in combat
}

# ── Apply Passive Zone Rewards (Runs Hourly) ──────────────────
async def zone_income_loop(app):
    await asyncio.sleep(10)
    while True:
        try:
            zone_ws = sheet.worksheet("ZoneControl")
            res_ws = sheet.worksheet("Resources")
            inbox_ws = sheet.worksheet("Inbox")

            zone_rows = zone_ws.get_all_values()
            res_ids = res_ws.col_values(1)

            for row in zone_rows[1:]:  # skip header
                zone_key, user_id, _ = row
                reward = ZONE_REWARDS.get(zone_key, {})

                if not reward or user_id not in res_ids:
                    continue

                res_row = res_ids.index(user_id) + 1

                # Apply income
                for res_type, amt in reward.items():
                    if res_type in ["gold", "iron", "tech", "crystals"]:
                        col = {"gold": 2, "iron": 3, "tech": 4, "crystals": 5}[res_type]
                        current = int(res_ws.cell(res_row, col).value)
                        res_ws.update_cell(res_row, col, current + amt)

                        save_inbox_message(user_id, "Zone Reward",
                                           f"Passive income from {ZONES[zone_key]['name']}: +{amt} {res_type.title()}")
        except Exception as e:
            logger.error(f"Zone income loop failed: {e}")

        await asyncio.sleep(3600)  # Run hourly
# ── /status Command — Show Player Overview ────────────────────
async def show_status_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    try:
        # Load faction
        faction = get_player_faction(user_id).title()
        if faction == "None":
            faction = "❓ Not selected"

        # Load resources
        res_ids = resources_sheet.col_values(1)
        row = res_ids.index(user_id) + 1
        gold = int(resources_sheet.cell(row, 2).value)
        iron = int(resources_sheet.cell(row, 3).value)
        tech = int(resources_sheet.cell(row, 4).value)
        crystals = int(resources_sheet.cell(row, 5).value)

        # Load zones
        zone_ws = sheet.worksheet("ZoneControl")
        zone_rows = zone_ws.get_all_values()
        my_zones = [r[0] for r in zone_rows[1:] if r[1] == user_id]

        buffs = []
        if faction == "Technocrats":
            buffs.append("🧠 20% cheaper upgrades")
        elif faction == "Nomads":
            buffs.append("🐺 20% faster training")
        elif faction == "Warlords":
            buffs.append("⚔️ 20% PvP damage boost")

        for z in my_zones:
            zone_buff = ZONE_REWARDS.get(z, {})
            if "iron" in zone_buff:
                buffs.append("⛓ +20 Iron/hr")
            if "tech" in zone_buff:
                buffs.append("🧪 +10 Tech/hr")
            if "pvp_buff" in zone_buff:
                buffs.append("⚔️ +5% PvP damage (zone)")

        buff_list = "\n".join(buffs) if buffs else "None"

        zone_names = "\n".join([ZONES[z]["name"] for z in my_zones]) if my_zones else "None"

        text = (
            f"*📊 Status Panel — {user.first_name}*\n\n"
            f"🏳️ Faction: *{faction}*\n"
            f"📍 Controlled Zones:\n{zone_names}\n\n"
            f"💰 Resources:\n"
            f"🪙 Gold: `{gold}`\n"
            f"⛓ Iron: `{iron}`\n"
            f"🧪 Tech: `{tech}`\n"
            f"💎 Crystals: `{crystals}`\n\n"
            f"🔋 Active Buffs:\n{buff_list}"
        )

        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Status panel error for {user_id}: {e}")
        await update.message.reply_text("⚠️ Failed to load status panel.")
# ── /attack <player_id> Command — PvP Entry ───────────────────
async def heal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def pvp_attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker = update.effective_user
    attacker_id = str(attacker.id)
    if not has_player_name(attacker_id):
        await update.message.reply_text("⚠️ You must set a name before attacking. Use:\n/setname <your_name>")
        return

    if not context.args:
        await update.message.reply_text("Usage: /attack <enemy_id>")
        return

    target_id = context.args[0]

    if attacker_id == target_id:
        await update.message.reply_text("❌ You can't attack yourself.")
        return

    try:
        # Base damage
        base_damage = 100

        # Apply Warlords faction buff
        attacker_faction = get_player_faction(attacker_id)
        if attacker_faction == "warlords":
            base_damage = int(base_damage * 1.2)

        # Apply Warlord Gate zone bonus
        try:
            zone_ws = sheet.worksheet("ZoneControl")
            rows = zone_ws.get_all_values()
            for r in rows[1:]:
                if r[0] == "warlord_gate" and r[1] == attacker_id:
                    base_damage = int(base_damage * 1.05)
        except Exception as e:
            logger.warning(f"Warlord zone bonus check failed: {e}")

        # Apply damage (stub — replace with your real unit/building logic)
            # Calculate base_damage (with faction/zone buffs) ...
        try:
    
            # Load defender stats
            stats = get_pvp_stats(target_id)
            old_hp = stats["hp"]
            defense = stats["def"]

            reduced_damage = max(0, base_damage - defense)
            new_hp = max(0, old_hp - reduced_damage)
            update_pvp_hp(target_id, new_hp)
        except Exception as e:
            logger.warning(f"Damage phase failed: {e}")

result = "🩸 Survived" if new_hp > 0 else "☠️ Defeated"
await update.message.reply_text(
f"⚔️ *Battle Summary*\n\nYou attacked `{target_id}`!\n"
f"🛡 Defense: {defense}\n"
f"💥 Damage dealt: *{reduced_damage}*\n"
        f"❤️ HP left: *{new_hp}*\n\n"
        f"{result}",
        parse_mode="Markdown"
    )

    save_inbox_message(attacker_id, "PvP Attack", f"You hit {target_id} for {reduced_damage}. HP left: {new_hp}")
    save_inbox_message(target_id, "PvP Defense", f"You were attacked by {attacker_id} — {reduced_damage} dmg. HP: {new_hp}")
log_battle(attacker_id, target_id, reduced_damage, result)


        # Log to inbox
        save_inbox_message(attacker_id, "PvP Attack", f"You attacked {target_id} for {base_damage} damage.")
        save_inbox_message(target_id, "PvP Defense", f"You were attacked by {attacker_id} — damage: {base_damage}.")

    except Exception as e:
        logger.error(f"PvP error: {e}")
        await update.message.reply_text("⚠️ PvP attack failed.")
# ── Simple Health System Sheet: PvPHealth ─────────────────────
# Columns: [user_id, hp, def]

def get_pvp_stats(user_id):
    try:
        ws = sheet.worksheet("PvPHealth")
        ids = ws.col_values(1)
        if user_id not in ids:
            ws.append_row([user_id, 100, 20])  # default: 100 HP, 20 defense
            return {"hp": 100, "def": 20, "row": len(ids) + 1}
        row = ids.index(user_id) + 1
        hp = int(ws.cell(row, 2).value)
        defense = int(ws.cell(row, 3).value)
        return {"hp": hp, "def": defense, "row": row}
    except Exception as e:
        logger.error(f"PvP stat load failed for {user_id}: {e}")
        return {"hp": 100, "def": 0, "row": -1}

def update_pvp_hp(user_id, new_hp):
    try:
        ws = sheet.worksheet("PvPHealth")
        ids = ws.col_values(1)
        row = ids.index(user_id) + 1
        ws.update_cell(row, 2, max(0, new_hp))
    except Exception as e:
        logger.error(f"PvP HP update failed: {e}")
# ── /heal Command ─────────────────────────────────────────────
async def heal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    try:
        # Check current HP
        stats = get_pvp_stats(user_id)
        if stats["hp"] >= 100:
            await update.message.reply_text("🩺 You're already at full HP.")
            return

        # Resource cost
        cost = {"iron": 50, "tech": 20}
        ids = resources_sheet.col_values(1)
        if user_id not in ids:
            await update.message.reply_text("❌ Resource profile not found.")
            return

        row = ids.index(user_id) + 1
        iron = int(resources_sheet.cell(row, 3).value)
        tech = int(resources_sheet.cell(row, 4).value)

        if iron < cost["iron"] or tech < cost["tech"]:
            await update.message.reply_text("❌ Not enough resources to heal.\nRequires 50 Iron + 20 Tech.")
            return

        # Deduct
        resources_sheet.update_cell(row, 3, iron - cost["iron"])
        resources_sheet.update_cell(row, 4, tech - cost["tech"])
        update_pvp_hp(user_id, 100)

        await update.message.reply_text("🩺 You've been healed to full HP!")
        save_inbox_message(user_id, "Healing", "You spent 50 Iron + 20 Tech to heal to full HP.")

    except Exception as e:
        logger.error(f"Heal command failed for {user_id}: {e}")
        await update.message.reply_text("⚠️ Healing failed.")
# ── Log PvP to BattleLog Sheet ────────────────────────────────
def log_battle(attacker_id, target_id, damage, result):
    try:
        log_ws = sheet.worksheet("BattleLog")
        log_ws.append_row([
            str(attacker_id),
            str(target_id),
            int(damage),
            result,
            datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])
    except Exception as e:
        logger.error(f"Failed to log battle: {e}")
# ── /battlelog Command — View PvP History ─────────────────────
async def show_battle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        log_ws = sheet.worksheet("BattleLog")
        rows = log_ws.get_all_values()[1:]  # Skip header

        recent = [r for r in rows if r[0] == user_id or r[1] == user_id][-10:]

        if not recent:
            await update.message.reply_text("🗂 Your battle log is empty.")
            return

        text = "*📜 Battle Log (Recent 10)*\n\n"
                for r in recent:
            attacker, target, dmg, result, time = r
            attacker_name = get_player_name(attacker)
            target_name = get_player_name(target)

            if attacker == user_id:
                you = "You"
                vs = f"→ {target_name}"
            elif target == user_id:
                you = "You"
                vs = f"← {attacker_name}"
            else:
                you = attacker_name
                vs = f"→ {target_name}"

            text += f"{time} — {you} {vs}\n💥 Damage: {dmg} — {result}\n\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Battle log error: {e}")
        await update.message.reply_text("⚠️ Failed to load battle log.")
# ── /rankings Command — PvP Leaderboard ───────────────────────
async def show_rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        log_ws = sheet.worksheet("BattleLog")
        rows = log_ws.get_all_values()[1:]  # Skip header

        # Aggregate damage per attacker
        scores = {}
        for r in rows:
            attacker, _, dmg, _, _ = r
            dmg = int(dmg)
            scores[attacker] = scores.get(attacker, 0) + dmg

        # Sort by total damage
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

        if not top:
            await update.message.reply_text("🏆 No battles have been recorded yet.")
            return

        text = "*🏆 Top 10 Attackers — PvP Rankings*\n\n"
        for i, (uid, dmg) in enumerate(top, 1):
            label = "👑" if i == 1 else f"{i}."
            text += f"{label} *{get_player_name(uid)}* — `{dmg}` damage\n"


        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"PvP rankings error: {e}")
        await update.message.reply_text("⚠️ Failed to load rankings.")

application.add_handler(CommandHandler("rankings", show_rankings))

# ── /setname <your_name> ──────────────────────────────────────
async def set_player_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("Usage: /setname <your_name>\nExample: /setname ShadowWolf")
        return

    chosen_name = " ".join(context.args).strip()
    if len(chosen_name) > 20:
        await update.message.reply_text("❌ Name too long. Max 20 characters.")
        return

    try:
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            ws.update_cell(row, 2, chosen_name)
        else:
            ws.append_row([user_id, chosen_name, "None"])  # Default: no faction

        await update.message.reply_text(f"✅ Your name has been set to *{chosen_name}*!", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to set name: {e}")
        await update.message.reply_text("⚠️ Failed to save name.")
def get_player_name(user_id):
    try:
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            name = ws.cell(row, 2).value
            return name or f"User_{user_id[-4:]}"
        return f"User_{user_id[-4:]}"
    except:
        return f"User_{user_id[-4:]}"
application.add_handler(CommandHandler("setname", set_player_name))

def has_player_name(user_id):
    try:
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            name = ws.cell(row, 2).value
            return bool(name and len(name.strip()) > 1)
        return False
    except:
        return False
async def show_tech_tree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    faction = get_player_faction(user_id)
    zone_ws = sheet.worksheet("ZoneControl")
    owned_zones = [r[0] for r in zone_ws.get_all_values()[1:] if r[1] == user_id]

    tree_ws = sheet.worksheet("TechTree")
    rows = tree_ws.get_all_values()[1:]

    text = "*🔬 Tech Tree — Available Research:*\n\n"
    buttons = []

    for row in rows:
        tech_id, name, desc, cost, zone_req, faction_req = row
        if faction_req.lower() not in ["none", faction]:
            continue
        if zone_req and zone_req not in owned_zones:
            continue
        text += f"🧪 *{name}* — {desc}\n💰 Cost: {cost} Tech\n\n"
        buttons.append([InlineKeyboardButton(f"Unlock {name}", callback_data=f"tech_unlock_{tech_id}")])

    if not buttons:
        text += "_No available techs. Claim zones or meet faction requirements._"

    buttons.append([InlineKeyboardButton("⬅️ Back to Command Center", callback_data="open_center")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

application.add_handler(CommandHandler("techs", show_tech_tree))


def setup_game_sheets():
    sheet_titles = {
        "Players": ["user_id", "name", "faction"],
        "Resources": ["user_id", "gold", "iron", "tech", "crystals"],
        "Buildings": ["user_id", "base", "lab", "barracks", "storage"],
        "Inbox": ["user_id", "type", "message", "timestamp"],
        "BuildQueue": ["user_id", "building", "start_time"],
        "Events": ["event_name", "start_time", "end_time", "status", "participants"],
        "BlackMarket": ["user_id", "items"],
        "PvPHealth": ["user_id", "hp", "def"],
        "BattleLog": ["attacker", "defender", "damage", "result", "timestamp"],
        "ZoneControl": ["zone_id", "user_id", "claim_time"],
        "TechTree": ["tech_id", "name", "desc", "cost_tech", "required_zone", 
        "faction_lock"]
        "TechUnlocks": ["user_id", "unlocked_techs"]

    }

    for title, headers in sheet_titles.items():
        try:
            sheet.worksheet(title)
            print(f"✅ Sheet exists: {title}")
        except:
            sheet.add_worksheet(title=title, rows=100, cols=20)
            ws = sheet.worksheet(title)
            ws.append_row(headers)
            print(f"🆕 Created sheet: {title}")
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != "YOUR_TELEGRAM_ID":  # Replace with your real Telegram ID
        await update.message.reply_text("❌ Only the admin can run this command.")
        return

    try:
        setup_game_sheets()
        await update.message.reply_text("✅ Game sheets initialized successfully.")
    except Exception as e:
        logger.error(f"Setup error: {e}")
        await update.message.reply_text("⚠️ Failed to setup sheets.")
application.add_handler(CommandHandler("setup", setup_command))

async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # 🔐 Replace this with YOUR Telegram user ID (as a string)
    ADMIN_ID = "7737016510"  

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can run this setup.")
        return

    try:
        setup_game_sheets()
        await update.message.reply_text("✅ All game sheets have been created and initialized.")
    except Exception as e:
        logger.error(f"Sheet setup failed: {e}")
        await update.message.reply_text("⚠️ Sheet setup failed. Check logs.")
# ── Handle Unlock Button Press ────────────────────────────────
async def handle_tech_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    tech_id = query.data.replace("tech_unlock_", "")
    tree_ws = sheet.worksheet("TechTree")
    rows = tree_ws.get_all_values()[1:]

    tech_row = next((r for r in rows if r[0] == tech_id), None)
    if not tech_row:
        await query.edit_message_text("❌ Tech not found.")
        return

    _, name, desc, cost, zone_req, faction_req = tech_row
    cost = int(cost)

    # Check faction requirement
    faction = get_player_faction(user_id)
    if faction_req.lower() != "none" and faction != faction_req.lower():
        await query.edit_message_text(f"❌ Requires faction: {faction_req.title()}")
        return

    # Check zone control
    zone_ws = sheet.worksheet("ZoneControl")
    owned_zones = [r[0] for r in zone_ws.get_all_values()[1:] if r[1] == user_id]
    if zone_req and zone_req not in owned_zones:
        await query.edit_message_text(f"❌ Requires control of: {ZONES[zone_req]['name']}")
        return

    # Check tech points
    ids = resources_sheet.col_values(1)
    row = ids.index(user_id) + 1
    tech_points = int(resources_sheet.cell(row, 4).value)
    if tech_points < cost:
        await query.edit_message_text("❌ Not enough Tech points.")
        return

    # Check already unlocked
    unlock_ws = sheet.worksheet("TechUnlocks")
    unlock_ids = unlock_ws.col_values(1)
    if user_id in unlock_ids:
        u_row = unlock_ids.index(user_id) + 1
        current = unlock_ws.cell(u_row, 2).value or ""
        if tech_id in current.split(","):
            await query.edit_message_text("⚠️ You’ve already unlocked this tech.")
            return
        updated = current + f",{tech_id}"
        unlock_ws.update_cell(u_row, 2, updated)
    else:
        unlock_ws.append_row([user_id, tech_id])

    # Deduct cost
    resources_sheet.update_cell(row, 4, tech_points - cost)

    await query.edit_message_text(
        f"✅ *{name}* unlocked!\n\n_{desc}_",
        parse_mode="Markdown"
    )

    save_inbox_message(user_id, "Tech Unlock", f"You unlocked {name} for {cost} Tech points.")
elif data.startswith("tech_unlock_"):
    await handle_tech_unlock(update, context)
async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"  # Replace with your Telegram ID
    user_id = str(update.effective_user.id)

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can use this command.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /grant <target_id> <resource> <amount>\nExample: /grant 123456 gold 1000")
        return

    target_id, resource, amount = context.args
    resource = resource.lower()
    try:
        amount = int(amount)
    except:
        await update.message.reply_text("❌ Amount must be a number.")
        return

    # Check resource type
    valid_resources = {"gold": 2, "iron": 3, "tech": 4, "crystals": 5}
    if resource not in valid_resources:
        await update.message.reply_text("❌ Invalid resource. Use: gold, iron, tech, crystals")
        return

    try:
        ids = resources_sheet.col_values(1)
        if target_id not in ids:
            resources_sheet.append_row([target_id, 0, 0, 0, 0])
            row = len(ids) + 1
        else:
            row = ids.index(target_id) + 1

        col = valid_resources[resource]
        current = int(resources_sheet.cell(row, col).value)
        resources_sheet.update_cell(row, col, current + amount)

        await update.message.reply_text(f"✅ Granted {amount} {resource} to {get_player_name(target_id)}.")
        save_inbox_message(target_id, "Admin", f"You received +{amount} {resource} from admin.")
    except Exception as e:
        logger.error(f"Grant failed: {e}")
        await update.message.reply_text("⚠️ Failed to grant resource.")

application.add_handler(CommandHandler("grant", grant_command))

import random
import datetime

# ── /daily Command — Claim Login Reward ───────────────────────
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    try:
        ws = sheet.worksheet("DailyClaims")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            last_claim = ws.cell(row, 2).value
            if last_claim == now:
                await update.message.reply_text("⏳ You’ve already claimed today’s reward.")
                return
            ws.update_cell(row, 2, now)
        else:
            ws.append_row([user_id, now])

        # Reward (randomized)
        rewards = {
            "gold": random.randint(100, 300),
            "iron": random.randint(80, 200),
            "tech": random.randint(50, 150),
            "crystals": random.randint(1, 3)
        }

        # Add to player resources
        res_ids = resources_sheet.col_values(1)
        if user_id not in res_ids:
            resources_sheet.append_row([user_id, 0, 0, 0, 0])
            res_row = len(res_ids) + 1
        else:
            res_row = res_ids.index(user_id) + 1

        resources_sheet.update_cell(res_row, 2, int(resources_sheet.cell(res_row, 2).value) + rewards["gold"])
        resources_sheet.update_cell(res_row, 3, int(resources_sheet.cell(res_row, 3).value) + rewards["iron"])
        resources_sheet.update_cell(res_row, 4, int(resources_sheet.cell(res_row, 4).value) + rewards["tech"])
        resources_sheet.update_cell(res_row, 5, int(resources_sheet.cell(res_row, 5).value) + rewards["crystals"])

        # Send reward summary
        text = (
            "*🎁 Daily Reward Claimed!*\n\n"
            f"🪙 Gold: +{rewards['gold']}\n"
            f"⛓ Iron: +{rewards['iron']}\n"
            f"🧪 Tech: +{rewards['tech']}\n"
            f"💎 Crystals: +{rewards['crystals']}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

        save_inbox_message(user_id, "Daily Reward", f"You claimed today’s bonus: +{rewards['gold']} gold, +{rewards['crystals']} crystals, etc.")
    except Exception as e:
        logger.error(f"Daily reward error: {e}")
        await update.message.reply_text("⚠️ Failed to process daily reward.")

application.add_handler(CommandHandler("daily", daily_command))

"DailyClaims": ["user_id", "last_claim_date"]

def has_tech(user_id, tech_id):
    try:
        ws = sheet.worksheet("TechUnlocks")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            unlocked = ws.cell(row, 2).value or ""
            return tech_id in unlocked.split(",")
        return False
    except:
        return False

# Example: if they unlocked auto_mine, give +10% iron
if has_tech(user_id, "auto_mine") and "iron" in reward:
    bonus = int(reward["iron"] * 0.1)
    res_ws.update_cell(res_row, 3, int(res_ws.cell(res_row, 3).value) + bonus)
    save_inbox_message(user_id, "Tech Bonus", f"Auto Mine bonus: +{bonus} Iron.")

# After other damage boosts:
if has_tech(attacker_id, "pvp_buff"):
    base_damage = int(base_damage * 1.10)

if has_tech(user_id, "builder_discount"):
    for k in cost:
        cost[k] = int(cost[k] * 0.9)
if has_tech(user_id, "fast_training"):
    duration = int(duration * 0.85)


async def wipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"  # Replace with your real Telegram ID
    user_id = str(update.effective_user.id)

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You do not have permission to use this command.")
        return

    try:
        wipe_targets = [
            "Players", "Resources", "Buildings", "Inbox", "PvPHealth",
            "TechUnlocks", "ZoneControl", "BattleLog", "BlackMarket", "DailyClaims"
        ]

        for sheet_name in wipe_targets:
            ws = sheet.worksheet(sheet_name)
            data = ws.get_all_values()
            if data:
                headers = data[0]
                ws.clear()
                ws.append_row(headers)

        await update.message.reply_text("🧼 All game data has been wiped. The game is now reset.")
    except Exception as e:
        logger.error(f"Wipe failed: {e}")
        await update.message.reply_text("⚠️ Wipe failed. Check logs.")

application.add_handler(CommandHandler("wipe", wipe_command))

application.add_handler(CommandHandler("wipe", wipe_command))

def init_building_hp(user_id):
    try:
        ws = sheet.worksheet("BuildingHP")
        ids = ws.col_values(1)
        if user_id not in ids:
            ws.append_row([user_id, 100, 100, 100, 100])
    except Exception as e:
        logger.error(f"Failed to init Building HP for {user_id}: {e}")

# Pick a random building to damage
import random

buildings = ["base", "lab", "barracks", "storage"]
damaged = random.choice(buildings)

ws = sheet.worksheet("BuildingHP")
ids = ws.col_values(1)
if target_id not in ids:
    ws.append_row([target_id, 100, 100, 100, 100])
    row = len(ids) + 1
else:
    row = ids.index(target_id) + 1

# Column index for that building
col = {"base": 2, "lab": 3, "barracks": 4, "storage": 5}[damaged]
current_hp = int(ws.cell(row, col).value)
new_hp = max(0, current_hp - reduced_damage // 2)  # Half damage to structure
ws.update_cell(row, col, new_hp)

# Inbox & summary
save_inbox_message(target_id, "Building Damaged", f"{damaged.title()} damaged: {current_hp} → {new_hp}")
await update.message.reply_text(f"🏚 {damaged.title()} of the target was damaged!")

def get_building_hp(user_id, bld):
    try:
        ws = sheet.worksheet("BuildingHP")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            col = {"base": 2, "lab": 3, "barracks": 4, "storage": 5}[bld]
            return int(ws.cell(row, col).value)
    except:
        return 100

async def repair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if not args or args[0] not in ["base", "lab", "barracks", "storage"]:
        await update.message.reply_text("Usage: /repair <base|lab|barracks|storage>")
        return

    bld = args[0]
    col_map = {"base": 2, "lab": 3, "barracks": 4, "storage": 5}

    try:
        ws = sheet.worksheet("BuildingHP")
        ids = ws.col_values(1)
        if user_id not in ids:
            ws.append_row([user_id, 100, 100, 100, 100])
            row = len(ids) + 1
        else:
            row = ids.index(user_id) + 1

        col = col_map[bld]
        current_hp = int(ws.cell(row, col).value)

        if current_hp >= 100:
            await update.message.reply_text(f"✅ Your {bld} is already at full health.")
            return

        # Repair cost
        hp_needed = 100 - current_hp
        gold_cost = hp_needed * 5
        crystal_cost = 1 if hp_needed >= 50 else 0

        # Check resources
        res_ids = resources_sheet.col_values(1)
        res_row = res_ids.index(user_id) + 1
        gold = int(resources_sheet.cell(res_row, 2).value)
        crystals = int(resources_sheet.cell(res_row, 5).value)

        if gold < gold_cost or crystals < crystal_cost:
            await update.message.reply_text(
                f"❌ You need {gold_cost} Gold and {crystal_cost} Crystals to repair {bld}."
            )
            return

        # Deduct resources
        resources_sheet.update_cell(res_row, 2, gold - gold_cost)
        if crystal_cost:
            resources_sheet.update_cell(res_row, 5, crystals - crystal_cost)

        # Apply repair
        ws.update_cell(row, col, 100)

        await update.message.reply_text(
            f"🛠️ Your {bld.title()} has been fully repaired!\n💰 Spent: {gold_cost} Gold + {crystal_cost} Crystals"
        )
        save_inbox_message(user_id, "Repair Complete", f"{bld.title()} restored to 100 HP.")
    except Exception as e:
        logger.error(f"Repair failed for {user_id}: {e}")
        await update.message.reply_text("⚠️ Failed to repair building.")

application.add_handler(CommandHandler("repair", repair_command))


"DefenseUpgrades": ["user_id", "level"]


async def defend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    try:
        ws = sheet.worksheet("DefenseUpgrades")
        ids = ws.col_values(1)

        # Get current level
        if user_id in ids:
            row = ids.index(user_id) + 1
            level = int(ws.cell(row, 2).value)
        else:
            ws.append_row([user_id, 0])
            level = 0
            row = len(ids) + 1

        # Calculate upgrade cost
        next_level = level + 1
        gold_cost = 500 * next_level
        tech_cost = 100 * next_level

        # Check resources
        res_ids = resources_sheet.col_values(1)
        res_row = res_ids.index(user_id) + 1
        gold = int(resources_sheet.cell(res_row, 2).value)
        tech = int(resources_sheet.cell(res_row, 4).value)

        if gold < gold_cost or tech < tech_cost:
            await update.message.reply_text(
                f"❌ You need {gold_cost} Gold and {tech_cost} Tech to upgrade defense to level {next_level}."
            )
            return

        # Deduct
        resources_sheet.update_cell(res_row, 2, gold - gold_cost)
        resources_sheet.update_cell(res_row, 4, tech - tech_cost)

        # Save upgrade
        ws.update_cell(row, 2, next_level)

        await update.message.reply_text(
            f"🛡️ Defense upgraded to level {next_level}!\n"
            f"Each level reduces incoming PvP damage by 5%."
        )
        save_inbox_message(user_id, "Defense Upgrade", f"Your base defense is now level {next_level}.")
    except Exception as e:
        logger.error(f"Defense upgrade failed: {e}")
        await update.message.reply_text("⚠️ Failed to upgrade defense.")


application.add_handler(CommandHandler("defend", defend_command))

# Defense reduction from upgrades
def_ws = sheet.worksheet("DefenseUpgrades")
def_ids = def_ws.col_values(1)
if target_id in def_ids:
    def_row = def_ids.index(target_id) + 1
    level = int(def_ws.cell(def_row, 2).value)
    reduced_damage = int(reduced_damage * (1 - level * 0.05))

# Defense reduction from upgrades
def_ws = sheet.worksheet("DefenseUpgrades")
def_ids = def_ws.col_values(1)
if target_id in def_ids:
    def_row = def_ids.index(target_id) + 1
    level = int(def_ws.cell(def_row, 2).value)
    reduced_damage = int(reduced_damage * (1 - level * 0.05))

def run_weekly_rewards():
    try:
        log_ws = sheet.worksheet("BattleLog")
        rows = log_ws.get_all_values()[1:]  # Skip header

        # Filter by last 7 days
        one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        weekly_rows = [r for r in rows if datetime.datetime.strptime(r[4], "%Y-%m-%d %H:%M:%S") >= one_week_ago]

        scores = {}
        for r in weekly_rows:
            attacker, _, dmg, _, _ = r
            dmg = int(dmg)
            scores[attacker] = scores.get(attacker, 0) + dmg

        # Sort top 3
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        reward_ws = sheet.worksheet("WeeklyWinners")
        week_tag = datetime.datetime.utcnow().strftime("%Y-W%U")

        for rank, (uid, total) in enumerate(top, 1):
            reward = {1: 100, 2: 60, 3: 40}[rank]
            reward_ws.append_row([week_tag, uid, rank, total, reward])

            # Grant crystals
            ids = resources_sheet.col_values(1)
            if uid not in ids:
                resources_sheet.append_row([uid, 0, 0, 0, 0])
                row = len(ids) + 1
            else:
                row = ids.index(uid) + 1
            old = int(resources_sheet.cell(row, 5).value)
            resources_sheet.update_cell(row, 5, old + reward)

            save_inbox_message(uid, "🏆 Weekly PvP Reward", f"You ranked #{rank} in PvP and earned {reward} 💎 Crystals!")

        print(f"✅ Weekly rewards distributed for {week_tag}")
    except Exception as e:
        logger.error(f"Weekly reward error: {e}")


from datetime import time as dtime
job_queue = application.job_queue
job_queue.run_daily(lambda ctx: run_weekly_rewards(), time=dtime(hour=12), days=(6,))


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    name = get_player_name(user_id)
    faction = get_player_faction(user_id).title()

    try:
        # PvP stats from BattleLog
        log_ws = sheet.worksheet("BattleLog")
        logs = [r for r in log_ws.get_all_values()[1:] if r[0] == user_id]
        total_dmg = sum(int(r[2]) for r in logs)
        kills = sum(1 for r in logs if r[3] == "☠️ Defeated")

        # Zone count
        zones = sheet.worksheet("ZoneControl").get_all_values()[1:]
        owned_zones = [z[0] for z in zones if z[1] == user_id]

        # Defense level
        def_ws = sheet.worksheet("DefenseUpgrades")
        def_lvl = "0"
        if user_id in def_ws.col_values(1):
            row = def_ws.col_values(1).index(user_id) + 1
            def_lvl = def_ws.cell(row, 2).value

        # Techs unlocked
        tech_ws = sheet.worksheet("TechUnlocks")
        techs = []
        if user_id in tech_ws.col_values(1):
            t_row = tech_ws.col_values(1).index(user_id) + 1
            techs = (tech_ws.cell(t_row, 2).value or "").split(",")

        text = (
            f"*👤 Player Profile: {name}*\n\n"
            f"🏳️ Faction: *{faction}*\n"
            f"⚔️ PvP Damage: `{total_dmg}`\n"
            f"💀 PvP Kills: `{kills}`\n"
            f"📍 Zones Owned: `{len(owned_zones)}`\n"
            f"🛡️ Defense Level: `{def_lvl}`\n"
            f"🧪 Techs Unlocked: `{len([t for t in techs if t])}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Profile error for {user_id}: {e}")
        await update.message.reply_text("⚠️ Failed to load profile.")


application.add_handler(CommandHandler("profile", profile_command))


"Titles": ["user_id", "title"]


def get_player_title(user_id):
    try:
        ws = sheet.worksheet("Titles")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            return ws.cell(row, 2).value or ""
        return ""
    except:
        return ""


name = get_player_name(user_id)

title = get_player_title(user_id)
name = f"{title} {name}" if title else name


async def set_title_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can assign titles.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /title <target_id> <emoji/title>")
        return

    target_id = context.args[0]
    title = " ".join(context.args[1:])

    try:
        ws = sheet.worksheet("Titles")
        ids = ws.col_values(1)
        if target_id in ids:
            row = ids.index(target_id) + 1
            ws.update_cell(row, 2, title)
        else:
            ws.append_row([target_id, title])

        await update.message.reply_text(f"✅ Title set for {get_player_name(target_id)}: {title}")
        save_inbox_message(target_id, "🎖 Title Awarded", f"You received the title: {title}")
    except Exception as e:
        logger.error(f"Title error: {e}")
        await update.message.reply_text("⚠️ Failed to assign title.")


application.add_handler(CommandHandler("profile", profile_command))
application.add_handler(CommandHandler("title", set_title_command))

async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"  # Replace with your Telegram user ID
    user_id = str(update.effective_user.id)

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /announce <your message here>")
        return

    message = "📢 *Global Announcement*\n\n" + " ".join(context.args)

    try:
        players_ws = sheet.worksheet("Players")
        user_ids = players_ws.col_values(1)[1:]  # Skip header

        sent = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message, parse_mode="Markdown")
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to {uid}: {e}")
        await update.message.reply_text(f"✅ Announcement sent to {sent} players.")
    except Exception as e:
        logger.error(f"Announce failed: {e}")
        await update.message.reply_text("⚠️ Announcement failed.")

application.add_handler(CommandHandler("announce", announce_command))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    try:
        # Auto-create player row if needed
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id not in ids:
            ws.append_row([user_id, "", "none"])
            save_inbox_message(user_id, "👋 Welcome!", "You've joined SkyHustle. Start building your empire!")
        
        text = (
            "*🌍 Welcome to SkyHustle!*\n\n"
            "A Telegram empire-building game where you:\n"
            "🛠 Build and upgrade your base\n"
            "⚔️ Attack rivals in PvP\n"
            "📈 Unlock techs to dominate\n"
            "💎 Buy rare gear from the Black Market\n"
            "🧠 Choose a faction and control zones\n\n"
            "*🔑 Getting Started:*\n"
            "1️⃣ Set your name: `/setname CommanderX`\n"
            "2️⃣ View your stats: `/profile`\n"
            "3️⃣ Claim a zone: `/zones`\n"
            "4️⃣ Train, build, and upgrade to grow\n"
            "5️⃣ Use `/attack <player_id>` to conquer enemies\n\n"
            "🏛 Use `/status` to see your resources\n"
            "🎁 Claim free rewards daily with `/daily`\n"
            "👑 Top players earn weekly crystal rewards!\n\n"
            "Type `/help` or `/profile` anytime to see where you stand.\n"
            "_Game powered by strategy, resource control, and pure hustle._"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"/start failed for {user_id}: {e}")
        await update.message.reply_text("⚠️ Error starting the game.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*🆘 SkyHustle Command Guide*\n\n"
        "*🧑‍🚀 Player Basics*\n"
        "`/setname <name>` — Set your player name\n"
        "`/profile` — View your full stats and title\n"
        "`/status` — See resources, buffs, and zone effects\n"
        "`/daily` — Claim your free daily reward\n\n"
        "*🏗 Base & Buildings*\n"
        "`/build` — View or upgrade your buildings\n"
        "`/repair <building>` — Fix a damaged structure\n"
        "`/defend` — Upgrade your base defense\n\n"
        "*⚔️ Combat & PvP*\n"
        "`/attack <player_id>` — Attack another player\n"
        "`/heal` — Restore your HP (costs crystals)\n"
        "`/battlelog` — See your recent fights\n"
        "`/rankings` — View the PvP leaderboard\n\n"
        "*🧠 Tech & Factions*\n"
        "`/faction` — Choose a faction with special buffs\n"
        "`/techs` — View and unlock new technologies\n\n"
        "*📍 Zone Control*\n"
        "`/zones` — View available zones\n"
        "`/myzones` — See which zones you control\n\n"
        "*🎒 Store & Items*\n"
        "`/store` — Buy boosts with crystals\n"
        "`/blackmarket` — Buy rare one-time items\n"
        "`/inventory` — See and use owned items\n"
        "`/use <item_id>` — Activate a Black Market item\n\n"
        "*👑 Prestige & Progression*\n"
        "`/title` — (admin only) Assign a title to a player\n"
        "`/profile` — Shows unlocked techs, kills, zones, etc.\n"
        "`/start` — Restart the welcome message\n\n"
        "_Type `/profile` to check your power. Rule the map!_"
    )

    await update.message.reply_text(text, parse_mode="Markdown")

application.add_handler(CommandHandler("help", help_command))
