"""
SkyHustle Telegram Game - main.py

This unified file includes:
- Command handlers
- Google Sheets integration
- PvP, Buildings, Zones, Tech Tree, Combat, Rewards
"""

import os
import datetime
import random
import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Google Sheets Setup ───────────────────────────────────────
import base64
import json

creds_b64 = os.getenv("GOOGLE_CREDS_BASE64")
sheet_id = os.getenv("SHEET_ID")

creds_json = base64.b64decode(creds_b64).decode("utf-8")
creds_dict = json.loads(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(sheet_id)

resources_sheet = sheet.worksheet("Resources")


# ── Helper Functions ──────────────────────────────────────────
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

# ── Command Handlers (Examples) ───────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    ws = sheet.worksheet("Players")
    ids = ws.col_values(1)
    if user_id not in ids:
        ws.append_row([user_id, "", "none"])
        save_inbox_message(user_id, "Welcome", "Welcome to SkyHustle!")

    await update.message.reply_text(
    "🌍 *Welcome to SkyHustle!*\n\n"
    "A Telegram strategy game where you:\n"
    "🛠 Build your base\n"
    "⚔️ Attack rivals\n"
    "📍 Control zones\n"
    "🧬 Unlock tech\n"
    "💎 Buy from the Black Market\n\n"
    "👉 Type `/setname YourName` to begin\n"
    "👉 View `/profile`, `/status`, `/zones`, `/build`\n"
    "Claim free resources with `/daily`!",
    parse_mode="Markdown"
)


# Add your full handler logic here...


# ── /setname Command ───────────────────────────────────────────
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

# ── /status Command ────────────────────────────────────────────
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

# ── /zones and /myzones Commands ───────────────────────────────
async def show_zone_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ws = sheet.worksheet("ZoneControl")
    rows = ws.get_all_values()[1:]
    claimed = {r[0]: r[1] for r in rows}

    all_zones = ["desert_outpost", "tech_hub", "warlord_gate"]
    btns = []

    for z in all_zones:
        owner = claimed.get(z, None)
        label = f"{z} — Claimed" if owner else f"{z} — Available"
        btns.append([InlineKeyboardButton(label, callback_data=f"zone_claim_{z}")])

    await update.message.reply_text(
        "*🌍 Zones:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(btns)
    )

async def show_my_zones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ws = sheet.worksheet("ZoneControl")
    rows = ws.get_all_values()[1:]
    owned = [r[0] for r in rows if r[1] == user_id]

    if not owned:
        await update.message.reply_text("You don't control any zones yet.")
        return

    text = "*📍 Your Zones:*
" + "
".join([f"- {z}" for z in owned])
    await update.message.reply_text(text, parse_mode="Markdown")


# ── PvP Attack Command ─────────────────────────────────────────
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

    # Damage logic (simplified for this segment)
    base_damage = random.randint(30, 60)

    # Load target defense level
    def_ws = sheet.worksheet("DefenseUpgrades")
    def_ids = def_ws.col_values(1)
    defense_level = 0
    if target_id in def_ids:
        def_row = def_ids.index(target_id) + 1
        defense_level = int(def_ws.cell(def_row, 2).value)
    reduced_damage = int(base_damage * (1 - defense_level * 0.05))

    # Load defender HP
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
        f"⚔️ You attacked {get_player_name(target_id)}!
"
        f"💥 Damage: {reduced_damage}
"
        f"❤️ HP Remaining: {new_hp}
"
        f"{result}"
    )

    # Log and inbox
    save_inbox_message(attacker_id, "PvP Attack", f"You hit {get_player_name(target_id)} for {reduced_damage}.")
    save_inbox_message(target_id, "PvP Defense", f"You were attacked by {get_player_name(attacker_id)} for {reduced_damage}.")
    log_battle(attacker_id, target_id, reduced_damage, result)

# ── Heal Command ───────────────────────────────────────────────
async def heal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        ids = resources_sheet.col_values(1)
        row = ids.index(user_id) + 1
        crystals = int(resources_sheet.cell(row, 5).value)
        if crystals < 15:
            await update.message.reply_text("❌ Not enough crystals.")
            return
        resources_sheet.update_cell(row, 5, crystals - 15)

        hp_ws = sheet.worksheet("PvPHealth")
        hp_ids = hp_ws.col_values(1)
        if user_id in hp_ids:
            hp_row = hp_ids.index(user_id) + 1
            hp_ws.update_cell(hp_row, 2, 100)
        else:
            hp_ws.append_row([user_id, 100, 20])

        await update.message.reply_text("🩹 Fully healed to 100 HP.")
    except Exception as e:
        logger.error(f"Heal error: {e}")
        await update.message.reply_text("Failed to heal.")

# ── Battle Log View ────────────────────────────────────────────
async def show_battle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        log_ws = sheet.worksheet("BattleLog")
        rows = log_ws.get_all_values()[1:]
        recent = [r for r in rows if r[0] == user_id or r[1] == user_id][-10:]
        if not recent:
            await update.message.reply_text("🗂 No battle history.")
            return

        text = "*📜 Battle Log:*

"
        for r in recent:
            attacker, target, dmg, result, time = r
            text += f"{time} — {get_player_name(attacker)} vs {get_player_name(target)}
💥 {dmg} — {result}

"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Log error: {e}")
        await update.message.reply_text("Could not load logs.")

# ── PvP Logger ────────────────────────────────────────────────
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


# ── Store Menu ────────────────────────────────────────────────
async def show_store_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "*🛒 Store Menu:*

"
    text += "💡 Boosts and utility items to help you grow.

"
    text += "- Builder Boost (50 💎)
"
    text += "- Training Pass (40 💎)
"
    text += "- XP Boost (25 💎)
"

    buttons = [
        [InlineKeyboardButton("Buy Builder Boost - 50💎", callback_data="buy_boost_builder")],
        [InlineKeyboardButton("Buy Training Pass - 40💎", callback_data="buy_boost_train")],
        [InlineKeyboardButton("Buy XP Boost - 25💎", callback_data="buy_boost_xp")]
    ]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# ── Black Market Menu ─────────────────────────────────────────
async def show_blackmarket_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = {
        "revive_all": ["Revive All Units", "Restore all buildings/units", 500],
        "scout_adv": ["Advanced Scout", "Reveal enemy zones", 300],
        "emp_device": ["EMP Device", "Disable enemy defense", 350]
    }

    text = "*🕶 Black Market*

"
    for key, val in items.items():
        text += f"🧪 *{val[0]}* — {val[1]} ({val[2]}💎)
"

    buttons = [[InlineKeyboardButton(f"Buy {val[0]} - {val[2]}💎", callback_data=f"bm_buy_{key}")]
               for key, val in items.items()]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# ── Handle Black Market Purchase ──────────────────────────────
async def handle_blackmarket_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    item_id = query.data.replace("bm_buy_", "")

    item_map = {
        "revive_all": ("Revive All Units", 500),
        "scout_adv": ("Advanced Scout", 300),
        "emp_device": ("EMP Device", 350)
    }

    if item_id not in item_map:
        await query.edit_message_text("❌ Item not found.")
        return

    name, cost = item_map[item_id]

    ids = resources_sheet.col_values(1)
    row = ids.index(user_id) + 1
    crystals = int(resources_sheet.cell(row, 5).value)
    if crystals < cost:
        await query.edit_message_text("❌ Not enough Crystals.")
        return

    # Deduct and record
    resources_sheet.update_cell(row, 5, crystals - cost)
    ws = sheet.worksheet("BlackMarket")
    ids = ws.col_values(1)
    if user_id in ids:
        row = ids.index(user_id) + 1
        current = ws.cell(row, 2).value or ""
        updated = current + "," + item_id if current else item_id
        ws.update_cell(row, 2, updated)
    else:
        ws.append_row([user_id, item_id])

    await query.edit_message_text(f"✅ {name} purchased!")
    save_inbox_message(user_id, "Black Market", f"You bought {name}.")

# ── /inventory Command ────────────────────────────────────────
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

# ── /use Command ──────────────────────────────────────────────
async def use_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /use <item_id>")
        return

    item_id = context.args[0]
    ws = sheet.worksheet("BlackMarket")
    ids = ws.col_values(1)
    if user_id not in ids:
        await update.message.reply_text("❌ No inventory found.")
        return

    row = ids.index(user_id) + 1
    inv = ws.cell(row, 2).value or ""
    items = inv.split(",")

    if item_id not in items:
        await update.message.reply_text("❌ You don't own that item.")
        return

    if item_id == "revive_all":
        hp_ws = sheet.worksheet("PvPHealth")
        hp_ids = hp_ws.col_values(1)
        if user_id in hp_ids:
            hp_row = hp_ids.index(user_id) + 1
            hp_ws.update_cell(hp_row, 2, 100)
        await update.message.reply_text("🧬 Revived to full HP!")

    # Remove used item
    items.remove(item_id)
    ws.update_cell(row, 2, ",".join(items))
    save_inbox_message(user_id, "Item Used", f"You used {item_id}.")


# ── /build Command ─────────────────────────────────────────────
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

# ── /upgrade <building> ───────────────────────────────────────
async def handle_building_upgrade(data, update, context):
    user_id = str(update.effective_user.id)
    bld = data.replace("upg_", "")
    col_map = {"base": 2, "lab": 3, "barracks": 4, "storage": 5}
    if bld not in col_map:
        await update.message.reply_text("❌ Invalid building.")
        return

    ws = sheet.worksheet("Buildings")
    ids = ws.col_values(1)
    if user_id not in ids:
        ws.append_row([user_id, 1, 1, 1, 1])
        row = len(ids) + 1
    else:
        row = ids.index(user_id) + 1

    col = col_map[bld]
    current_lvl = int(ws.cell(row, col).value)
    next_lvl = current_lvl + 1

    # Cost calculation
    gold_cost = 100 * next_lvl
    iron_cost = 80 * next_lvl
    tech_cost = 50 * next_lvl

    # Check resources
    res_ids = resources_sheet.col_values(1)
    res_row = res_ids.index(user_id) + 1
    gold = int(resources_sheet.cell(res_row, 2).value)
    iron = int(resources_sheet.cell(res_row, 3).value)
    tech = int(resources_sheet.cell(res_row, 4).value)

    if gold < gold_cost or iron < iron_cost or tech < tech_cost:
        await update.message.reply_text("❌ Not enough resources.")
        return

    # Deduct and upgrade
    resources_sheet.update_cell(res_row, 2, gold - gold_cost)
    resources_sheet.update_cell(res_row, 3, iron - iron_cost)
    resources_sheet.update_cell(res_row, 4, tech - tech_cost)
    ws.update_cell(row, col, next_lvl)

    await update.message.reply_text(
        f"✅ {bld.title()} upgraded to Level {next_lvl}!
"
        f"Cost: {gold_cost} Gold, {iron_cost} Iron, {tech_cost} Tech"
    )

# ── /repair <building> ────────────────────────────────────────
async def repair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args or args[0] not in ["base", "lab", "barracks", "storage"]:
        await update.message.reply_text("Usage: /repair <base|lab|barracks|storage>")
        return

    bld = args[0]
    col_map = {"base": 2, "lab": 3, "barracks": 4, "storage": 5}

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
        await update.message.reply_text(f"{bld.title()} is already fully repaired.")
        return

    hp_needed = 100 - current_hp
    gold_cost = hp_needed * 5
    crystal_cost = 1 if hp_needed >= 50 else 0

    res_ids = resources_sheet.col_values(1)
    res_row = res_ids.index(user_id) + 1
    gold = int(resources_sheet.cell(res_row, 2).value)
    crystals = int(resources_sheet.cell(res_row, 5).value)

    if gold < gold_cost or crystals < crystal_cost:
        await update.message.reply_text("❌ Not enough resources to repair.")
        return

    resources_sheet.update_cell(res_row, 2, gold - gold_cost)
    if crystal_cost:
        resources_sheet.update_cell(res_row, 5, crystals - crystal_cost)
    ws.update_cell(row, col, 100)

    await update.message.reply_text(
        f"🛠️ {bld.title()} repaired to full.
Cost: {gold_cost} Gold, {crystal_cost} Crystals"
    )
    save_inbox_message(user_id, "Repair", f"{bld.title()} restored to full HP.")


# ── /techs Command ─────────────────────────────────────────────
async def show_tech_tree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    faction = get_player_faction(user_id)
    zone_ws = sheet.worksheet("ZoneControl")
    owned_zones = [r[0] for r in zone_ws.get_all_values()[1:] if r[1] == user_id]

    tree_ws = sheet.worksheet("TechTree")
    rows = tree_ws.get_all_values()[1:]

    text = "*🔬 Tech Tree — Available Research:*

"
    buttons = []

    for row in rows:
        tech_id, name, desc, cost, zone_req, faction_req = row
        if faction_req.lower() not in ["none", faction]:
            continue
        if zone_req and zone_req not in owned_zones:
            continue
        text += f"🧪 *{name}* — {desc}
💰 Cost: {cost} Tech

"
        buttons.append([InlineKeyboardButton(f"Unlock {name}", callback_data=f"tech_unlock_{tech_id}")])

    buttons.append([InlineKeyboardButton("⬅️ Back to Command Center", callback_data="open_center")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# ── Tech Unlock Handler ───────────────────────────────────────
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

    faction = get_player_faction(user_id)
    if faction_req.lower() != "none" and faction != faction_req.lower():
        await query.edit_message_text(f"❌ Requires faction: {faction_req.title()}")
        return

    zone_ws = sheet.worksheet("ZoneControl")
    owned_zones = [r[0] for r in zone_ws.get_all_values()[1:] if r[1] == user_id]
    if zone_req and zone_req not in owned_zones:
        await query.edit_message_text(f"❌ Requires control of: {zone_req}")
        return

    ids = resources_sheet.col_values(1)
    row = ids.index(user_id) + 1
    tech_points = int(resources_sheet.cell(row, 4).value)
    if tech_points < cost:
        await query.edit_message_text("❌ Not enough Tech points.")
        return

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

    resources_sheet.update_cell(row, 4, tech_points - cost)
    await query.edit_message_text(f"✅ *{name}* unlocked!

_{desc}_", parse_mode="Markdown")
    save_inbox_message(user_id, "Tech Unlock", f"You unlocked {name} for {cost} Tech points.")

# ── Tech Check Helper ─────────────────────────────────────────
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


# ── Zone Claim Handler ─────────────────────────────────────────
async def handle_zone_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    zone_id = query.data.replace("zone_claim_", "")

    ws = sheet.worksheet("ZoneControl")
    rows = ws.get_all_values()[1:]
    for i, r in enumerate(rows):
        if r[0] == zone_id:
            if r[1] == user_id:
                await query.edit_message_text("⚠️ You already control this zone.")
                return
            else:
                ws.update_cell(i + 2, 2, user_id)
                ws.update_cell(i + 2, 3, datetime.datetime.utcnow().isoformat())
                break
    else:
        ws.append_row([zone_id, user_id, datetime.datetime.utcnow().isoformat()])

    await query.edit_message_text(f"✅ You claimed zone: *{zone_id}*", parse_mode="Markdown")
    save_inbox_message(user_id, "Zone Claimed", f"You claimed {zone_id}.")

# ── /daily Command ─────────────────────────────────────────────
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

# ── Weekly PvP Rewards ────────────────────────────────────────
def run_weekly_rewards():
    try:
        log_ws = sheet.worksheet("BattleLog")
        rows = log_ws.get_all_values()[1:]
        one_week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        weekly_rows = [r for r in rows if datetime.datetime.strptime(r[4], "%Y-%m-%d %H:%M:%S") >= one_week_ago]

        scores = {}
        for r in weekly_rows:
            attacker, _, dmg, _, _ = r
            dmg = int(dmg)
            scores[attacker] = scores.get(attacker, 0) + dmg

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        reward_ws = sheet.worksheet("WeeklyWinners")
        week_tag = datetime.datetime.utcnow().strftime("%Y-W%U")

        for rank, (uid, total) in enumerate(top, 1):
            reward = {1: 100, 2: 60, 3: 40}[rank]
            reward_ws.append_row([week_tag, uid, rank, total, reward])
            ids = resources_sheet.col_values(1)
            if uid not in ids:
                resources_sheet.append_row([uid, 0, 0, 0, 0])
                row = len(ids) + 1
            else:
                row = ids.index(uid) + 1
            old = int(resources_sheet.cell(row, 5).value)
            resources_sheet.update_cell(row, 5, old + reward)
            save_inbox_message(uid, "🏆 Weekly PvP Reward", f"You ranked #{rank} in PvP and earned {reward} 💎 Crystals!")
    except Exception as e:
        logger.error(f"Weekly reward error: {e}")


# ── /grant Command (Admin) ─────────────────────────────────────
async def grant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can use this.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /grant <target_id> <resource> <amount>")
        return

    target_id, resource, amount = context.args
    valid_resources = {"gold": 2, "iron": 3, "tech": 4, "crystals": 5}
    if resource not in valid_resources:
        await update.message.reply_text("Invalid resource type.")
        return

    try:
        amount = int(amount)
        ids = resources_sheet.col_values(1)
        if target_id not in ids:
            resources_sheet.append_row([target_id, 0, 0, 0, 0])
            row = len(ids) + 1
        else:
            row = ids.index(target_id) + 1
        col = valid_resources[resource]
        old_val = int(resources_sheet.cell(row, col).value)
        resources_sheet.update_cell(row, col, old_val + amount)
        await update.message.reply_text(f"✅ Granted {amount} {resource} to {get_player_name(target_id)}.")
    except Exception as e:
        logger.error(f"Grant failed: {e}")
        await update.message.reply_text("Failed to grant resource.")

# ── /title Command (Admin) ─────────────────────────────────────
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
        await update.message.reply_text(f"✅ Title set: {title}")
    except Exception as e:
        logger.error(f"Title error: {e}")
        await update.message.reply_text("❌ Failed to assign title.")

# ── /announce Command (Admin) ──────────────────────────────────
async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    message = "📢 *Announcement:*

" + " ".join(context.args)
    try:
        ws = sheet.worksheet("Players")
        user_ids = ws.col_values(1)[1:]
        sent = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message, parse_mode="Markdown")
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Announcement sent to {sent} users.")
    except Exception as e:
        logger.error(f"Announce error: {e}")
        await update.message.reply_text("⚠️ Failed to announce.")

# ── /wipe Command (Admin) ─────────────────────────────────────
async def wipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = "7737016510"
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    try:
        wipe_targets = [
            "Players", "Resources", "Buildings", "Inbox", "PvPHealth",
            "TechUnlocks", "ZoneControl", "BattleLog", "BlackMarket",
            "DailyClaims", "Titles"
        ]
        for sheet_name in wipe_targets:
            ws = sheet.worksheet(sheet_name)
            data = ws.get_all_values()
            if data:
                headers = data[0]
                ws.clear()
                ws.append_row(headers)
        await update.message.reply_text("🧼 All game data wiped.")
    except Exception as e:
        logger.error(f"Wipe error: {e}")
        await update.message.reply_text("⚠️ Wipe failed.")

# ── Bot Startup ───────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setname", set_player_name))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("status", show_status_panel))
    app.add_handler(CommandHandler("zones", show_zone_list))
    app.add_handler(CommandHandler("myzones", show_my_zones))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("repair", repair_command))
    app.add_handler(CommandHandler("heal", heal_command))
    app.add_handler(CommandHandler("battlelog", show_battle_log))
    app.add_handler(CommandHandler("defend", defend_command))
    app.add_handler(CommandHandler("inventory", inventory_command))
    app.add_handler(CommandHandler("use", use_item_command))
    app.add_handler(CommandHandler("store", show_store_menu))
    app.add_handler(CommandHandler("blackmarket", show_blackmarket_menu))
    app.add_handler(CommandHandler("techs", show_tech_tree))
    app.add_handler(CommandHandler("attack", pvp_attack_command))
    app.add_handler(CommandHandler("grant", grant_command))
    app.add_handler(CommandHandler("title", set_title_command))
    app.add_handler(CommandHandler("announce", announce_command))
    app.add_handler(CommandHandler("wipe", wipe_command))
    app.add_handler(CallbackQueryHandler(command_center_buttons))

    app.run_polling()

if __name__ == "__main__":
    main()
