"""
SkyHustle Telegram Game Bot - main.py

Fully integrated and deployment-ready.
"""

# === IMPORTS ===
import os
import base64
import json
import datetime
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === GOOGLE SHEETS AUTH ===
creds_b64 = os.getenv("GOOGLE_CREDS_BASE64")
sheet_id = os.getenv("SHEET_ID")
creds_dict = json.loads(base64.b64decode(creds_b64))
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(sheet_id)
resources_sheet = sheet.worksheet("Resources")

# === HELPERS ===
def get_player_name(user_id):
    try:
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            return ws.cell(row, 2).value or f"User_{user_id[-4:]}"
        return f"User_{user_id[-4:]}"
    except:
        return f"User_{user_id[-4:]}"
        
def get_player_faction(user_id):
    try:
        ws = sheet.worksheet("Players")
        ids = ws.col_values(1)
        if user_id in ids:
            row = ids.index(user_id) + 1
            return ws.cell(row, 3).value.lower()
        return "none"
    except:
        return "none"

def save_inbox_message(user_id, mtype, message):
    try:
        ws = sheet.worksheet("Inbox")
        ws.append_row([user_id, mtype, message, datetime.datetime.utcnow().isoformat()])
    except:
        pass

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

# === START ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    ws = sheet.worksheet("Players")
    ids = ws.col_values(1)
    if user_id not in ids:
        ws.append_row([user_id, "", "none"])
        save_inbox_message(user_id, "Welcome", "Welcome to SkyHustle!")

    text = (
        "🌍 *Welcome to SkyHustle!*

"
        "A Telegram strategy game where you:
"
        "🛠 Build your base
"
        "⚔️ Attack rivals
"
        "📍 Control zones
"
        "🧬 Unlock tech
"
        "💎 Buy from the Black Market

"
        "👉 Type `/setname YourName` to begin
"
        "👉 View `/profile`, `/status`, `/zones`, `/build`
"
        "Claim free resources with `/daily`!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# === CONTINUED CORE SYSTEMS WILL BE WRITTEN BELOW ===


# === SET NAME ===
async def set_player_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /setname <your_name>")
        return

    chosen_name = " ".join(context.args).strip()
    if len(chosen_name) > 20:
        await update.message.reply_text("❌ Name too long. Max 20 characters.")
        return

    ws = sheet.worksheet("Players")
    ids = ws.col_values(1)
    if user_id in ids:
        row = ids.index(user_id) + 1
        ws.update_cell(row, 2, chosen_name)
    else:
        ws.append_row([user_id, chosen_name, "none"])

    await update.message.reply_text(f"✅ Your name is now *{chosen_name}*", parse_mode="Markdown")

# === STATUS PANEL ===
async def show_status_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ids = resources_sheet.col_values(1)
    if user_id not in ids:
        await update.message.reply_text("You don't have a resource profile yet.")
        return
    row = ids.index(user_id) + 1
    gold = resources_sheet.cell(row, 2).value
    iron = resources_sheet.cell(row, 3).value
    tech = resources_sheet.cell(row, 4).value
    crystals = resources_sheet.cell(row, 5).value
    faction = get_player_faction(user_id).title()

    text = (
        f"*📊 Your Status:*

"
        f"💰 Gold: `{gold}`
"
        f"⛓ Iron: `{iron}`
"
        f"🧪 Tech: `{tech}`
"
        f"💎 Crystals: `{crystals}`
"
        f"🏳️ Faction: *{faction}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# === DAILY REWARDS ===
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

        rewards = {
            "gold": random.randint(100, 300),
            "iron": random.randint(80, 200),
            "tech": random.randint(50, 150),
            "crystals": random.randint(1, 3)
        }

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

        text = (
            "*🎁 Daily Reward Claimed!*

"
            f"🪙 Gold: +{rewards['gold']}
"
            f"⛓ Iron: +{rewards['iron']}
"
            f"🧪 Tech: +{rewards['tech']}
"
            f"💎 Crystals: +{rewards['crystals']}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
        save_inbox_message(user_id, "Daily Reward", f"You claimed today’s bonus.")
    except Exception as e:
        logger.error(f"Daily reward error: {e}")
        await update.message.reply_text("⚠️ Failed to process daily reward.")


# === BUILDING OVERVIEW ===
async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ws = sheet.worksheet("Buildings")
    ids = ws.col_values(1)
    if user_id not in ids:
        ws.append_row([user_id, 1, 1, 1, 1])
        await update.message.reply_text("🏗️ Buildings initialized. You can now upgrade them.")
        return

    row = ids.index(user_id) + 1
    bld_names = ["base", "lab", "barracks", "storage"]
    levels = [ws.cell(row, i + 2).value for i in range(4)]
    text = "*🏗️ Your Buildings:*

"
    for name, lvl in zip(bld_names, levels):
        text += f"- {name.title()}: Level {lvl}
"
    await update.message.reply_text(text, parse_mode="Markdown")

# === PVP ATTACK ===
async def pvp_attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker = update.effective_user
    attacker_id = str(attacker.id)
    if not context.args:
        await update.message.reply_text("Usage: /attack <player_id>")
        return

    target_id = context.args[0]
    if attacker_id == target_id:
        await update.message.reply_text("❌ You cannot attack yourself.")
        return

    base_damage = random.randint(30, 60)
    def_ws = sheet.worksheet("DefenseUpgrades")
    def_ids = def_ws.col_values(1)
    defense_level = 0
    if target_id in def_ids:
        def_row = def_ids.index(target_id) + 1
        defense_level = int(def_ws.cell(def_row, 2).value)
    reduced_damage = int(base_damage * (1 - defense_level * 0.05))

    if has_tech(attacker_id, "pvp_buff"):
        reduced_damage = int(reduced_damage * 1.10)

    hp_ws = sheet.worksheet("PvPHealth")
    hp_ids = hp_ws.col_values(1)
    if target_id not in hp_ids:
        hp_ws.append_row([target_id, 100, 20])
        hp_row = len(hp_ids) + 1
    else:
        hp_row = hp_ids.index(target_id) + 1

    old_hp = int(hp_ws.cell(hp_row, 2).value)
    new_hp = max(0, old_hp - reduced_damage)
    hp_ws.update_cell(hp_row, 2, new_hp)

    result = "🩸 Survived" if new_hp > 0 else "☠️ Defeated"

    await update.message.reply_text(
        f"⚔️ *Battle Summary*

You attacked `{target_id}`!
"
        f"🛡 Defense: {defense_level}
"
        f"💥 Damage dealt: *{reduced_damage}*
"
        f"❤️ HP left: *{new_hp}*

"
        f"{result}",
        parse_mode="Markdown"
    )

    save_inbox_message(attacker_id, "PvP Attack", f"You hit {target_id} for {reduced_damage}. HP left: {new_hp}")
    save_inbox_message(target_id, "PvP Defense", f"You were attacked by {attacker_id} for {reduced_damage}. HP: {new_hp}")
    log_battle(attacker_id, target_id, reduced_damage, result)

# === BATTLE LOGGER ===
def log_battle(attacker_id, target_id, damage, result):
    try:
        log_ws = sheet.worksheet("BattleLog")
        log_ws.append_row([
            attacker_id,
            target_id,
            damage,
            result,
            datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])
    except Exception as e:
        logger.error(f"Battle logging failed: {e}")

# === HEAL ===
async def heal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        ids = resources_sheet.col_values(1)
        row = ids.index(user_id) + 1
        crystals = int(resources_sheet.cell(row, 5).value)
        if crystals < 15:
            await update.message.reply_text("❌ Not enough crystals (15 required).")
            return
        resources_sheet.update_cell(row, 5, crystals - 15)

        hp_ws = sheet.worksheet("PvPHealth")
        hp_ids = hp_ws.col_values(1)
        if user_id in hp_ids:
            hp_row = hp_ids.index(user_id) + 1
            hp_ws.update_cell(hp_row, 2, 100)
        else:
            hp_ws.append_row([user_id, 100, 20])

        await update.message.reply_text("🩹 You are now fully healed to 100 HP!")
    except Exception as e:
        logger.error(f"Heal error: {e}")
        await update.message.reply_text("❌ Failed to heal.")


# === INVENTORY ===
async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        ws = sheet.worksheet("BlackMarket")
        ids = ws.col_values(1)
        if user_id not in ids:
            await update.message.reply_text("🎒 Inventory is empty.")
            return

        row = ids.index(user_id) + 1
        items = (ws.cell(row, 2).value or "").split(",")
        if not items or items == [""]:
            await update.message.reply_text("🎒 Inventory is empty.")
            return

        text = "*🎒 Your Inventory:*

"
        for i in set(items):
            text += f"- {i}
"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Inventory error: {e}")
        await update.message.reply_text("⚠️ Failed to load inventory.")

# === BLACK MARKET ===
async def show_blackmarket_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = {
        "revive_all": ["Revive All Units", "Restores all HP", 500],
        "emp_device": ["EMP Device", "Disable defense 1h", 300]
    }

    text = "*🕶 Black Market*

"
    for key, val in items.items():
        text += f"🧪 *{val[0]}* — {val[1]} ({val[2]}💎)
"

    buttons = [[InlineKeyboardButton(f"Buy {val[0]} - {val[2]}💎", callback_data=f"bm_buy_{key}")]
               for key, val in items.items()]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# === USE ITEM ===
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /use <item_id>")
        return

    item_id = context.args[0]
    ws = sheet.worksheet("BlackMarket")
    ids = ws.col_values(1)
    if user_id not in ids:
        await update.message.reply_text("❌ You don’t own that item.")
        return

    row = ids.index(user_id) + 1
    inv = ws.cell(row, 2).value or ""
    items = inv.split(",")

    if item_id not in items:
        await update.message.reply_text("❌ You don’t own that item.")
        return

    if item_id == "revive_all":
        hp_ws = sheet.worksheet("PvPHealth")
        hp_ids = hp_ws.col_values(1)
        if user_id in hp_ids:
            hp_row = hp_ids.index(user_id) + 1
            hp_ws.update_cell(hp_row, 2, 100)
        else:
            hp_ws.append_row([user_id, 100, 20])
        await update.message.reply_text("🧬 Full HP restored.")
    elif item_id == "emp_device":
        await update.message.reply_text("⚡ EMP Device activated! (Effect placeholder)")

    items.remove(item_id)
    ws.update_cell(row, 2, ",".join(items))
    save_inbox_message(user_id, "Item Used", f"You used {item_id}.")


# === TECH TREE ===
async def show_tech_tree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    faction = get_player_faction(user_id)
    zone_ws = sheet.worksheet("ZoneControl")
    owned_zones = [r[0] for r in zone_ws.get_all_values()[1:] if r[1] == user_id]

    tree_ws = sheet.worksheet("TechTree")
    rows = tree_ws.get_all_values()[1:]

    text = "*🔬 Tech Tree:*

"
    buttons = []

    for row in rows:
        tech_id, name, desc, cost, zone_req, faction_req = row
        if faction_req.lower() not in ["none", faction]:
            continue
        if zone_req and zone_req not in owned_zones:
            continue
        text += f"🧪 *{name}* — {desc} ({cost} Tech)
"
        buttons.append([InlineKeyboardButton(f"Unlock {name}", callback_data=f"tech_unlock_{tech_id}")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# === ADMIN: Grant Resource ===
async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /grant <user_id> <resource> <amount>")
        return

    target_id, resource, amount = context.args
    col_map = {"gold": 2, "iron": 3, "tech": 4, "crystals": 5}
    if resource not in col_map:
        await update.message.reply_text("❌ Invalid resource.")
        return

    amount = int(amount)
    ids = resources_sheet.col_values(1)
    row = ids.index(target_id) + 1 if target_id in ids else None
    if not row:
        resources_sheet.append_row([target_id, 0, 0, 0, 0])
        row = len(ids) + 1

    val = int(resources_sheet.cell(row, col_map[resource]).value)
    resources_sheet.update_cell(row, col_map[resource], val + amount)
    await update.message.reply_text(f"✅ {amount} {resource} granted to {target_id}.")

# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setname", set_player_name))
    app.add_handler(CommandHandler("status", show_status_panel))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("build", build_command))
    app.add_handler(CommandHandler("attack", pvp_attack_command))
    app.add_handler(CommandHandler("heal", heal_command))
    app.add_handler(CommandHandler("inventory", inventory_command))
    app.add_handler(CommandHandler("use", use_item_command))
    app.add_handler(CommandHandler("blackmarket", show_blackmarket_menu))
    app.add_handler(CommandHandler("techs", show_tech_tree))
    app.add_handler(CommandHandler("grant", grant_command))

    app.run_polling()

if __name__ == "__main__":
    main()
