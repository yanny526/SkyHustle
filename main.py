# main.py — SkyHustle Unified Version (Part 1 of X)
import os
import json
import time
import base64
import random
import logging
import datetime
# ── Load Environment Credentials ────────────────────────────────
BASE64\_CREDS = os.environ.get("BASE64\_CREDS")
print("ENV:", os.environ)
print("BASE64\_CREDS:", BASE64\_CREDS)
if not BASE64\_CREDS:
    raise ValueError("❌ Environment variable BASE64\_CREDS is missing.")

creds\_json = json.loads(base64.b64decode(BASE64\_CREDS.strip()).decode())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

import gspread
from oauth2client.service\_account import ServiceAccountCredentials

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(\_\_name\_\_)

# ── Environment Variables ───────────────────────────────────────
TOKEN = os.getenv("BOT\_TOKEN")
SHEET\_KEY = os.getenv("SHEET\_KEY")
BASE64\_CREDS = os.environ.get("BASE64\_CREDS")
# ── Google Sheets Setup ─────────────────────────────────────────
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
if not BASE64\_CREDS:
    raise ValueError("❌ Environment variable BASE64\_CREDS is missing for Google Sheets.")
creds\_json = json.loads(base64.b64decode(BASE64\_CREDS.strip()).decode())
creds = ServiceAccountCredentials.from\_json\_keyfile\_dict(creds\_json, scope)
sheet = gspread.authorize(creds).open\_by\_key(SHEET\_KEY)


# ── Utility: Get Player Name by ID ──────────────────────────────
def get\_player\_name(user\_id: str):
    try:
        row = players\_sheet.find(user\_id).row
        return players\_sheet.cell(row, 2).value or user\_id
    except:
        return user\_id

# ── Utility: Get or Create Worksheet ────────────────────────────
def get\_or\_create\_worksheet(sheet, title, headers):
    try:
        ws = sheet.worksheet(title)
    except:
        ws = sheet.add\_worksheet(title=title, rows="1000", cols=str(len(headers)))
        ws.append\_row(headers)
    return ws

# ── Core Worksheets ─────────────────────────────────────────────
resources\_sheet = get\_or\_create\_worksheet(sheet, "Resources", ["ID", "gold", "iron", "tech", "crystals"])
players\_sheet = get\_or\_create\_worksheet(sheet, "Players", ["ID", "name", "faction"])
buildings\_sheet = get\_or\_create\_worksheet(sheet, "Buildings", ["ID", "mine", "barracks", "lab"])
army\_sheet = get\_or\_create\_worksheet(sheet, "Army", ["ID", "infantry", "sniper", "tank"])
research\_sheet = get\_or\_create\_worksheet(sheet, "Research", ["ID", "power", "production"])
zones\_sheet = get\_or\_create\_worksheet(sheet, "Zones", ["zone", "owner\_id"])
mission\_sheet = get\_or\_create\_worksheet(sheet, "Missions", ["ID", "build", "train", "attack", "capture"])
base\_sheet = get\_or\_create\_worksheet(sheet, "Bases", ["ID", "base\_level"])
daily\_sheet = get\_or\_create\_worksheet(sheet, "Daily", ["ID", "last\_claim"])
boss\_sheet = get\_or\_create\_worksheet(sheet, "RaidBoss", ["boss\_name", "hp"])
inbox\_sheet = get\_or\_create\_worksheet(sheet, "Inbox", ["ID", "message"])
event\_sheet = get\_or\_create\_worksheet(sheet, "Events", ["name", "description", "active"])
rank\_sheet = get\_or\_create\_worksheet(sheet, "Ranks", ["ID", "score"])
faction\_sheet = get\_or\_create\_worksheet(sheet, "Factions", ["Faction", "Points"])
trade\_sheet = get\_or\_create\_worksheet(sheet, "Trades", ["From", "To", "Resource", "Amount"])
# main.py — SkyHustle Unified Version (Part 2 of X)
# ── Player Registration ─────────────────────────────────────────
def register\_player(user\_id: int, username: str):
    try:
        players\_sheet.find(str(user\_id))
    except:
        players\_sheet.append\_row([str(user\_id), username or "Unknown", "none"])
        resources\_sheet.append\_row([str(user\_id), "500", "300", "0", "0"])
        buildings\_sheet.append\_row([str(user\_id), "1", "1", "1"])
        army\_sheet.append\_row([str(user\_id), "0", "0", "0"])
        research\_sheet.append\_row([str(user\_id), "0", "0"])
        mission\_sheet.append\_row([str(user\_id), "0", "0", "0", "0"])
        base\_sheet.append\_row([str(user\_id), "1"])
        daily\_sheet.append\_row([str(user\_id), "2000-01-01"])
        rank\_sheet.append\_row([str(user\_id), "0"])

# ── /start Command ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user = update.effective\_user
    register\_player(user.id, user.username)

    keyboard = [[InlineKeyboardButton("Enter SkyHustle 🌌", callback\_data="main\_menu")]]
    reply\_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply\_text(
        f"Welcome Commander \*{user.first\_name}\*\n\nYour empire begins now. 🌍\nChoose your path wisely.","
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=reply\_markup
    )

# ── Main Menu Callback ──────────────────────────────────────────
async def main\_menu(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🏗 Build", callback\_data="build\_menu"),
         InlineKeyboardButton("🧑‍✈️ Train", callback\_data="train\_menu")],
        [InlineKeyboardButton("⚔️ Attack", callback\_data="attack\_menu"),
         InlineKeyboardButton("🧪 Research", callback\_data="research\_menu")],
        [InlineKeyboardButton("🏙 Zones", callback\_data="zone\_menu"),
         InlineKeyboardButton("🛒 Store", callback\_data="store\_menu")],
        [InlineKeyboardButton("🎯 Missions", callback\_data="mission\_menu"),
         InlineKeyboardButton("📬 Inbox", callback\_data="inbox\_menu")],
        [InlineKeyboardButton("💼 Faction", callback\_data="faction\_menu"),
         InlineKeyboardButton("🌐 Events", callback\_data="event\_menu")],
        [InlineKeyboardButton("🗺 Base", callback\_data="base\_menu"),
         InlineKeyboardButton("👑 Leaderboard", callback\_data="rank\_menu")],
    ]
    await query.edit\_message\_text(
        "📟 \*Command Panel\*\nChoose your next action:",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 3 of X)
# ── Building Upgrade Logic ──────────────────────────────────────
def upgrade\_building(user\_id: int, building: str):
    col\_map = {"mine": 2, "barracks": 3, "lab": 4}
    if building not in col\_map:
        return False, "Invalid building."

    row = buildings\_sheet.find(str(user\_id)).row
    current\_level = int(buildings\_sheet.cell(row, col\_map[building]).value)
    cost = current\_level \* 100

    res\_row = resources\_sheet.find(str(user\_id)).row
    gold = int(resources\_sheet.cell(res\_row, 2).value)
    if gold < cost:
        return False, "Not enough gold."

    resources\_sheet.update\_cell(res\_row, 2, gold - cost)
    buildings\_sheet.update\_cell(row, col\_map[building], current\_level + 1)

    mark\_mission(user\_id, "build")
    update\_score(user\_id, 10)

    return True, f"{building.capitalize()} upgraded to level {current\_level + 1}!"

# ── Build Menu ──────────────────────────────────────────────────
async def build\_menu(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Upgrade Mine", callback\_data="build\_mine")],
        [InlineKeyboardButton("Upgrade Barracks", callback\_data="build\_barracks")],
        [InlineKeyboardButton("Upgrade Lab", callback\_data="build\_lab")],
        [InlineKeyboardButton("⬅️ Back", callback\_data="main\_menu")],
    ]
    await query.edit\_message\_text(
        "🏗 \*Choose a building to upgrade:\*",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Build Action Handler ────────────────────────────────────────
async def handle\_build\_action(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    user\_id = query.from\_user.id
    building = query.data.replace("build\_", "")
    success, msg = upgrade\_building(user\_id, building)
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback\_data="build\_menu")]]
    await query.edit\_message\_text(
        f"🏗 {msg}",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 4 of X)
# ── Training Logic ──────────────────────────────────────────────
def train\_unit(user\_id: int, unit: str):
    costs = {"infantry": 50, "sniper": 100, "tank": 200}
    col\_map = {"infantry": 2, "sniper": 3, "tank": 4}

    if unit not in costs:
        return False, "Invalid unit."

    res\_row = resources\_sheet.find(str(user\_id)).row
    gold = int(resources\_sheet.cell(res\_row, 2).value)
    if gold < costs[unit]:
        return False, "Not enough gold."

    army\_row = army\_sheet.find(str(user\_id)).row
    current = int(army\_sheet.cell(army\_row, col\_map[unit]).value)

    resources\_sheet.update\_cell(res\_row, 2, gold - costs[unit])
    army\_sheet.update\_cell(army\_row, col\_map[unit], current + 1)

    mark\_mission(user\_id, "train")
    update\_score(user\_id, 5)

    return True, f"Trained 1 {unit.capitalize()} successfully."

# ── Train Menu ──────────────────────────────────────────────────
async def train\_menu(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Train Infantry (50g)", callback\_data="train\_infantry")],
        [InlineKeyboardButton("Train Sniper (100g)", callback\_data="train\_sniper")],
        [InlineKeyboardButton("Train Tank (200g)", callback\_data="train\_tank")],
        [InlineKeyboardButton("⬅️ Back", callback\_data="main\_menu")],
    ]
    await query.edit\_message\_text(
        "🧑‍✈️ \*Choose a unit to train:\*",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Train Action Handler ────────────────────────────────────────
async def handle\_train\_action(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    user\_id = query.from\_user.id
    unit = query.data.replace("train\_", "")
    success, msg = train\_unit(user\_id, unit)
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback\_data="train\_menu")]]
    await query.edit\_message\_text(
        f"🧑‍✈️ {msg}",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )
# main.py — SkyHustle Unified Version (Part 5 of X)
# ── Combat Power Calculation ────────────────────────────────────
def get\_combat\_power(user\_id: int):
    try:
        row = army\_sheet.find(str(user\_id)).row
        infantry = int(army\_sheet.cell(row, 2).value)
        sniper = int(army\_sheet.cell(row, 3).value)
        tank = int(army\_sheet.cell(row, 4).value)
        return infantry \* 1 + sniper \* 3 + tank \* 5
    except:
        return 0

# ── Attack Menu ─────────────────────────────────────────────────
async def attack\_menu(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    await query.edit\_message\_text(
        "⚔️ Send /attack <user\_id> to initiate battle.",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback\_data="main\_menu")]])
    )

# ── /attack Command ─────────────────────────────────────────────
async def attack(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    attacker\_id = update.effective\_user.id
    if not context.args:
        return await update.message.reply\_text("Usage: /attack <user\_id>")

    try:
        target\_id = int(context.args[0])
    except ValueError:
        return await update.message.reply\_text("❌ Invalid ID format.")

    attacker\_power = get\_combat\_power(attacker\_id)
    defender\_power = get\_combat\_power(target\_id)

    if attacker\_power == 0:
        return await update.message.reply\_text("⚠️ You have no troops to send.")

    if defender\_power == 0:
        result = "Victory! 🏆 Enemy had no defense."
        mark\_mission(attacker\_id, "attack")
        update\_score(attacker\_id, 20)
    elif attacker\_power > defender\_power:
        result = "Victory! 🏆 You overpowered the enemy."
        mark\_mission(attacker\_id, "attack")
        update\_score(attacker\_id, 20)
    elif attacker\_power == defender\_power:
        result = "Draw ⚔️ Equal strength."
    else:
        result = "Defeat! 💀 The enemy was stronger."

    await update.message.reply\_text(
        f"⚔️ Combat Result:\nYou: {attacker\_power} vs Enemy: {defender\_power}\n\n{result}",
        parse\_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 6 of X)
# ── /research Command ───────────────────────────────────────────
async def research(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    try:
        row = research\_sheet.find(str(user\_id)).row
    except:
        research\_sheet.append\_row([str(user\_id), "0", "0"])
        row = research\_sheet.find(str(user\_id)).row

    power = int(research\_sheet.cell(row, 2).value)
    prod = int(research\_sheet.cell(row, 3).value)
    new\_power = power + 1
    new\_prod = prod + 1

    research\_sheet.update\_cell(row, 2, new\_power)
    research\_sheet.update\_cell(row, 3, new\_prod)

    await update.message.reply\_text(
        f"🔬 Research complete!\n+1 Power Bonus, +1 Production Bonus\n\n"
        f"Current Power: {new\_power}\nCurrent Production: {new\_prod}",
        parse\_mode=ParseMode.MARKDOWN
    )

# ── Passive Resource Generation ─────────────────────────────────
def generate\_resources():
    all\_ids = [cell.value for cell in resources\_sheet.col\_values(1)[1:]]
    for user\_id in all\_ids:
        try:
            row = resources\_sheet.find(user\_id).row
            prod\_row = research\_sheet.find(user\_id).row
            prod\_bonus = int(research\_sheet.cell(prod\_row, 3).value)

            gold = int(resources\_sheet.cell(row, 2).value)
            iron = int(resources\_sheet.cell(row, 3).value)
            tech = int(resources\_sheet.cell(row, 4).value)

            resources\_sheet.update\_cell(row, 2, gold + 10 + prod\_bonus)
            resources\_sheet.update\_cell(row, 3, iron + 5 + prod\_bonus)
            resources\_sheet.update\_cell(row, 4, tech + 2 + prod\_bonus)
        except Exception as e:
            logger.warning(f"Failed to update resources for {user\_id}: {e}")

# ── /collect Command ────────────────────────────────────────────
async def collect(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    generate\_resources()
    await update.message.reply\_text("💰 Resources generated for all users.")
# main.py — SkyHustle Unified Version (Part 7 of X)
# ── Zone List ───────────────────────────────────────────────────
ZONE\_LIST = ["Alpha", "Bravo", "Charlie", "Delta"]

# ── Capture Zone Utility ────────────────────────────────────────
def capture\_zone(zone: str, user\_id: int):
    try:
        cell = zones\_sheet.find(zone)
        zones\_sheet.update\_cell(cell.row, 2, str(user\_id))
    except:
        zones\_sheet.append\_row([zone, str(user\_id)])
    mark\_mission(user\_id, "capture")
    update\_score(user\_id, 15)

# ── /zones Command ──────────────────────────────────────────────
async def zones(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    message = "🌍 \*Zone Control Overview\*\n\n"
    for zone in ZONE\_LIST:
        try:
            cell = zones\_sheet.find(zone)
            owner\_id = zones\_sheet.cell(cell.row, 2).value
            message += f"▪️ {zone}: Controlled by \`{owner\_id}\`\n"
        except:
            message += f"▪️ {zone}: \_Unclaimed\_\n"
    await update.message.reply\_text(message, parse\_mode=ParseMode.MARKDOWN)

# ── /capture Command ────────────────────────────────────────────
async def capture(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    if not context.args:
        return await update.message.reply\_text("Usage: /capture <zone\_name>")

    zone = context.args[0].capitalize()
    if zone not in ZONE\_LIST:
        return await update.message.reply\_text("❌ Invalid zone.")

    capture\_zone(zone, user\_id)
    await update.message.reply\_text(f"✅ You have claimed zone \*{zone}\*.", parse\_mode=ParseMode.MARKDOWN)"
# main.py — SkyHustle Unified Version (Part 8 of X)
# ── Missions Setup ──────────────────────────────────────────────
MISSIONS = {
    "build": {"desc": "Upgrade any building", "reward": 100},
    "train": {"desc": "Train any unit", "reward": 80},
    "attack": {"desc": "Win a battle", "reward": 120},
    "capture": {"desc": "Claim a zone", "reward": 90},
}

# ── Ensure Mission Row Exists ───────────────────────────────────
def ensure\_mission\_row(user\_id):
    try:
        mission\_sheet.find(str(user\_id))
    except:
        mission\_sheet.append\_row([str(user\_id), "0", "0", "0", "0"])

# ── Mark Mission Complete ───────────────────────────────────────
def mark\_mission(user\_id, mission\_key):
    ensure\_mission\_row(user\_id)
    row = mission\_sheet.find(str(user\_id)).row
    col = list(MISSIONS.keys()).index(mission\_key) + 2
    mission\_sheet.update\_cell(row, col, "1")

# ── /missions Command ───────────────────────────────────────────
async def missions(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    ensure\_mission\_row(user\_id)
    row = mission\_sheet.find(str(user\_id)).row
    msg = "📋 \*Mission Progress:\*\n"
    for idx, key in enumerate(MISSIONS):
        status = mission\_sheet.cell(row, idx + 2).value
        check = "✅" if status == "1" else "⬜"
        msg += f"{check} {MISSIONS[key]['desc']}\n"
    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)

# ── /claim Command ──────────────────────────────────────────────
async def claim(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    ensure\_mission\_row(user\_id)
    row = mission\_sheet.find(str(user\_id)).row
    res\_row = resources\_sheet.find(str(user\_id)).row
    total = 0

    for idx, key in enumerate(MISSIONS):
        completed = mission\_sheet.cell(row, idx + 2).value
        if completed == "1":
            total += MISSIONS[key]['reward']
            mission\_sheet.update\_cell(row, idx + 2, "0")

    if total > 0:
        current\_gold = int(resources\_sheet.cell(res\_row, 2).value)
        resources\_sheet.update\_cell(res\_row, 2, current\_gold + total)
        await update.message.reply\_text(f"🎉 Claimed {total} gold from completed missions!", parse\_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply\_text("❌ No missions completed.", parse\_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 9 of X)
# ── Faction Setup ───────────────────────────────────────────────
FACTIONS = {
    "faction\_tech": "Techlords",
    "faction\_guard": "Guardians",
    "faction\_war": "Warlords",
}

# ── /faction Command ────────────────────────────────────────────
async def faction(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚙️ Techlords", callback\_data="faction\_tech")],
        [InlineKeyboardButton("🛡 Guardians", callback\_data="faction\_guard")],
        [InlineKeyboardButton("💣 Warlords", callback\_data="faction\_war")],
        [InlineKeyboardButton("⬅️ Back", callback\_data="main\_menu")]
    ]
    await update.message.reply\_text(
        "🏳 Choose your Faction:",
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Handle Faction Selection ────────────────────────────────────
async def handle\_faction\_choice(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    user\_id = query.from\_user.id
    chosen = FACTIONS.get(query.data)

    if not chosen:
        return await query.edit\_message\_text("❌ Invalid faction.")

    row = players\_sheet.find(str(user\_id)).row
    players\_sheet.update\_cell(row, 3, chosen)
    await query.edit\_message\_text(f"✅ You joined the \*{chosen}\* faction!", parse\_mode=ParseMode.MARKDOWN)"
# main.py — SkyHustle Unified Version (Part 10 of X)
# ── Ensure Base Row ─────────────────────────────────────────────
def ensure\_base\_row(user\_id):
    try:
        base\_sheet.find(str(user\_id))
    except:
        base\_sheet.append\_row([str(user\_id), "1"])

# ── /base Command ───────────────────────────────────────────────
async def base(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    ensure\_base\_row(user\_id)
    row = base\_sheet.find(str(user\_id)).row
    level = int(base\_sheet.cell(row, 2).value)
    await update.message.reply\_text(f"🏗 Your base is currently at level {level}.")

# ── /expand Command ─────────────────────────────────────────────
async def expand(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    ensure\_base\_row(user\_id)
    row = base\_sheet.find(str(user\_id)).row
    res\_row = resources\_sheet.find(str(user\_id)).row

    level = int(base\_sheet.cell(row, 2).value)
    gold = int(resources\_sheet.cell(res\_row, 2).value)
    cost = 200 \* level

    if gold < cost:
        return await update.message.reply\_text("❌ Not enough gold to expand base.")

    resources\_sheet.update\_cell(res\_row, 2, gold - cost)
    base\_sheet.update\_cell(row, 2, level + 1)
    update\_score(user\_id, 15)

    await update.message.reply\_text(f"🎉 Base expanded to level {level + 1}! Cost: {cost} gold.")
# main.py — SkyHustle Unified Version (Part 11 of X)
# ── /daily Command ──────────────────────────────────────────────
async def daily(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    today = datetime.datetime.utcnow().date()

    try:
        cell = daily\_sheet.find(user\_id)
        row = cell.row
        last\_claim\_str = daily\_sheet.cell(row, 2).value
        last\_claim = datetime.datetime.strptime(last\_claim\_str, "%Y-%m-%d").date()

        if last\_claim == today:
            return await update.message.reply\_text("🕐 You've already claimed today's reward.")

        daily\_sheet.update\_cell(row, 2, today.isoformat())
    except:
        daily\_sheet.append\_row([user\_id, today.isoformat()])

    res\_row = resources\_sheet.find(user\_id).row
    current\_gold = int(resources\_sheet.cell(res\_row, 2).value)
    bonus = 150

    resources\_sheet.update\_cell(res\_row, 2, current\_gold + bonus)
    update\_score(user\_id, 10)

    await update.message.reply\_text(f"🎁 You received your daily reward: {bonus} gold! Come back tomorrow.")
# main.py — SkyHustle Unified Version (Part 12 of X)
# ── Black Market Item Config ───────────────────────────────────
BLACK\_MARKET\_ITEMS = {
    "revive": {"name": "Revive Boost", "desc": "Revive all troops.", "cost": 500},
    "shield": {"name": "Shield Generator", "desc": "Block next attack.", "cost": 400},
    "emp": {"name": "EMP Device", "desc": "Weaken enemy defenses.", "cost": 300},
}

# ── /blackmarket Command ────────────────────────────────────────
async def blackmarket(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    keyboard = []
    for key, item in BLACK\_MARKET\_ITEMS.items():
        btn\_text = f"{item['name']} - {item['cost']}g"
        keyboard.append([InlineKeyboardButton(btn\_text, callback\_data=f"bm\_{key}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback\_data="main\_menu")])

    await update.message.reply\_text(
        "🛒 \*Black Market Items:\*",
        parse\_mode=ParseMode.MARKDOWN,
        reply\_markup=InlineKeyboardMarkup(keyboard)
    )

# ── Handle Black Market Purchase ────────────────────────────────
async def handle\_blackmarket(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    query = update.callback\_query
    await query.answer()
    user\_id = query.from\_user.id
    item\_key = query.data.replace("bm\_", "")
    item = BLACK\_MARKET\_ITEMS.get(item\_key)

    if not item:
        return await query.edit\_message\_text("❌ Invalid item.")

    row = resources\_sheet.find(str(user\_id)).row
    gold = int(resources\_sheet.cell(row, 2).value)

    if gold < item['cost']:
        return await query.edit\_message\_text("❌ Not enough gold.")

    resources\_sheet.update\_cell(row, 2, gold - item['cost'])
    update\_score(user\_id, 10)

    await query.edit\_message\_text(
        f"✅ You bought \*{item['name']}\*\n\_{item['desc']}\_","
        parse\_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 13 of X)
# ── Inbox Utility ───────────────────────────────────────────────
def send\_inbox(user\_id: str, message: str):
    inbox\_sheet.append\_row([user\_id, message])

# ── /inbox Command ──────────────────────────────────────────────
async def inbox(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    rows = inbox\_sheet.get\_all\_records()
    messages = [row["message"] for row in rows if row["ID"] == user\_id]

    if not messages:
        return await update.message.reply\_text("📭 Your inbox is empty.")

    text = "📬 \*Inbox Messages:\*\n\n" + "\n".join(f"▪️ {msg}" for msg in messages[-10:])
    await update.message.reply\_text(text, parse\_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 14 of X)
# ── PvE Boss Setup ──────────────────────────────────────────────
boss\_data = {"Titan": 5000, "Overlord": 8000}

# ── /raid Command ───────────────────────────────────────────────
async def raid(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    msg = "🛡 \*Available PvE Raids:\*\n\n"
    for name, hp in boss\_data.items():
        try:
            row = boss\_sheet.find(name).row
            current = int(boss\_sheet.cell(row, 2).value)
        except:
            boss\_sheet.append\_row([name, str(hp)])
            current = hp
        msg += f"▪️ {name} - {current} HP\n"
    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)

# ── /fight Command ──────────────────────────────────────────────
async def fight(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    if not context.args:
        return await update.message.reply\_text("Usage: /fight <boss\_name>")

    boss\_name = context.args[0].capitalize()
    if boss\_name not in boss\_data:
        return await update.message.reply\_text("❌ Invalid boss.")

    user\_id = update.effective\_user.id
    power = get\_combat\_power(user\_id)

    if power == 0:
        return await update.message.reply\_text("⚠️ You have no units to attack with.")

    try:
        row = boss\_sheet.find(boss\_name).row
        hp = int(boss\_sheet.cell(row, 2).value)
    except:
        row = boss\_sheet.append\_row([boss\_name, str(boss\_data[boss\_name])]).row
        hp = boss\_data[boss\_name]

    new\_hp = max(0, hp - power)
    boss\_sheet.update\_cell(row, 2, new\_hp)
    result = "🩸 Survived" if new\_hp > 0 else "☠️ Defeated"

    reward = 100 if new\_hp == 0 else 30
    res\_row = resources\_sheet.find(str(user\_id)).row
    current\_gold = int(resources\_sheet.cell(res\_row, 2).value)
    resources\_sheet.update\_cell(res\_row, 2, current\_gold + reward)

    log\_msg = f"You fought {boss\_name}, dealt {power} damage. Result: {result}. +{reward} gold."
    send\_inbox(str(user\_id), log\_msg)
    update\_score(user\_id, reward)

    await update.message.reply\_text(
        f"⚔️ You attacked \*{boss\_name}\* dealing \*{power}\* damage!\n"
        f"Current HP: {new\_hp}\nResult: {result}\nReward: +{reward} gold",
        parse\_mode=ParseMode.MARKDOWN
    )
# main.py — SkyHustle Unified Version (Part 15 of X)
# ── World Event Definitions ─────────────────────────────────────
events = [
    {"name": "Radiation Storm", "desc": "Mining yields halved for 1h"},
    {"name": "Meteor Shower", "desc": "+50% PvE gold for 30 min"},
    {"name": "War Cry", "desc": "Unit power doubled for 15 min"},
]

# ── /event Command ──────────────────────────────────────────────
async def event(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    msg = "🌐 \*Active World Events:\*\n\n"
    rows = event\_sheet.get\_all\_records()
    active = [row for row in rows if row['active'] == '1']

    if not active:
        msg += "No events currently active."
    else:
        for e in active:
            msg += f"▪️ \*{e['name']}\* — \_{e['description']}\_\n"

    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)

# ── /trigger\_event Command ──────────────────────────────────────
async def trigger\_event(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    if not context.args:
        return await update.message.reply\_text("Usage: /trigger\_event <event\_name>")

    name = " ".join(context.args).title()
    found = next((e for e in events if e["name"] == name), None)

    if not found:
        return await update.message.reply\_text("❌ Unknown event name.")

    try:
        row = event\_sheet.find(name).row
        event\_sheet.update\_cell(row, 3, "1")
    except:
        event\_sheet.append\_row([name, found["desc"], "1"])

    await update.message.reply\_text(f"🌟 \*{name}\* triggered successfully!", parse\_mode=ParseMode.MARKDOWN)"
# main.py — SkyHustle Unified Version (Part 16 of X)
# ── Update Player Score ─────────────────────────────────────────
def update\_score(user\_id: int, amount: int):
    try:
        row = rank\_sheet.find(str(user\_id)).row
        current = int(rank\_sheet.cell(row, 2).value)
        rank\_sheet.update\_cell(row, 2, current + amount)
    except:
        rank\_sheet.append\_row([str(user\_id), str(amount)])

# ── /leaderboard Command ────────────────────────────────────────
async def leaderboard(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    rows = rank\_sheet.get\_all\_records()
    top = sorted(rows, key=lambda x: int(x['score']), reverse=True)[:10]
    msg = "🏆 \*Top Players:\*\n\n"
    for i, row in enumerate(top, 1):
        msg += f"{i}. \`{row['ID']}\` — {row['score']} pts\n"
    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 17 of X)
# ── /spy Command ────────────────────────────────────────────────
async def spy(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    if not context.args:
        return await update.message.reply\_text("Usage: /spy <user\_id>")

    try:
        target\_id = int(context.args[0])
        army\_row = army\_sheet.find(str(target\_id)).row
        infantry = army\_sheet.cell(army\_row, 2).value
        sniper = army\_sheet.cell(army\_row, 3).value
        tank = army\_sheet.cell(army\_row, 4).value

        await update.message.reply\_text(
            f"🕵️ Spy Report on \`{target\_id}\`:\n"
            f"Infantry: {infantry}\nSniper: {sniper}\nTank: {tank}",
            parse\_mode=ParseMode.MARKDOWN
        )
    except:
        await update.message.reply\_text("❌ Failed to retrieve spy data.")
# main.py — SkyHustle Unified Version (Part 18 of X)
# ── /trade Command ───────────────────────────────────────────────
async def trade(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    if len(context.args) != 3:
        return await update.message.reply\_text("Usage: /trade <user\_id> <resource> <amount>")

    sender\_id = str(update.effective\_user.id)
    target\_id, resource, amount = context.args
    resource = resource.lower()

    if resource not in ["gold", "iron", "tech"]:
        return await update.message.reply\_text("❌ Invalid resource. Use: gold, iron, tech.")

    try:
        amount = int(amount)
        if amount <= 0:
            raise ValueError
    except:
        return await update.message.reply\_text("❌ Amount must be a positive number.")

    try:
        # Deduct from sender
        sender\_row = resources\_sheet.find(sender\_id).row
        col\_map = {"gold": 2, "iron": 3, "tech": 4}
        sender\_current = int(resources\_sheet.cell(sender\_row, col\_map[resource]).value)

        if sender\_current < amount:
            return await update.message.reply\_text("❌ You don't have enough resources.")

        resources\_sheet.update\_cell(sender\_row, col\_map[resource], sender\_current - amount)

        # Add to receiver
        receiver\_row = resources\_sheet.find(str(target\_id)).row
        receiver\_current = int(resources\_sheet.cell(receiver\_row, col\_map[resource]).value)
        resources\_sheet.update\_cell(receiver\_row, col\_map[resource], receiver\_current + amount)

        # Log trade
        trade\_sheet.append\_row([sender\_id, target\_id, resource, str(amount)])
        update\_score(int(sender\_id), 5)

        await update.message.reply\_text(f"✅ You sent {amount} {resource} to \`{target\_id}\`.", parse\_mode=ParseMode.MARKDOWN)
    except:
        return await update.message.reply\_text("❌ Failed to complete trade.")
# main.py — SkyHustle Unified Version (Part 19 of X)
# ── Admin Setup ─────────────────────────────────────────────────
ADMIN\_IDS = ["7737016510"]  # Replace with your actual Telegram ID

def is\_admin(user\_id):
    return str(user\_id) in ADMIN\_IDS

# ── /give\_gold Command ──────────────────────────────────────────
async def give\_gold(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = update.effective\_user.id
    if not is\_admin(user\_id):
        return await update.message.reply\_text("❌ Unauthorized.")

    if len(context.args) != 2:
        return await update.message.reply\_text("Usage: /give\_gold <user\_id> <amount>")

    try:
        target\_id = str(context.args[0])
        amount = int(context.args[1])

        row = resources\_sheet.find(target\_id).row
        current = int(resources\_sheet.cell(row, 2).value)
        resources\_sheet.update\_cell(row, 2, current + amount)

        await update.message.reply\_text(f"✅ Gave {amount} gold to \`{target\_id}\`.", parse\_mode=ParseMode.MARKDOWN)
    except:
        await update.message.reply\_text("❌ Failed to process command.")
# main.py — SkyHustle Unified Version (Part 20 of X)
# ── Add Faction Points ──────────────────────────────────────────
def add\_faction\_points(faction: str, points: int):
    try:
        row = faction\_sheet.find(faction).row
        current = int(faction\_sheet.cell(row, 2).value)
        faction\_sheet.update\_cell(row, 2, current + points)
    except:
        faction\_sheet.append\_row([faction, str(points)])

# ── /faction\_war Command ────────────────────────────────────────
async def faction\_war(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    records = faction\_sheet.get\_all\_records()
    msg = "⚔️ \*Faction War Standings:\*\n\n"

    if not records:
        for name in FACTIONS.values():
            faction\_sheet.append\_row([name, "0"])
            msg += f"▪️ {name} — 0 pts\n"
    else:
        sorted\_factions = sorted(records, key=lambda x: int(x["Points"]), reverse=True)
        for row in sorted\_factions:
            msg += f"▪️ {row['Faction']} — {row['Points']} pts\n"

    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 21 of 21)
# ── Command + Callback Registration ─────────────────────────────
# main.py — SkyHustle Unified Version (Part 22 of X)

# ── PvP Logs Sheet ─────────────────────────────────────────────
pvp\_log\_sheet = get\_or\_create\_worksheet(sheet, "PvPLogs", ["Attacker", "Defender", "Power", "Result", "Timestamp"])

# ── Utility: Log PvP Battle ─────────────────────────────────────
def log\_battle(attacker\_id, defender\_id, power, result):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    pvp\_log\_sheet.append\_row([str(attacker\_id), str(defender\_id), str(power), result, timestamp])


# ── /my\_battles Command ─────────────────────────────────────────
async def my\_battles(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    logs = pvp\_log\_sheet.get\_all\_records()
    filtered = [log for log in logs if log["Attacker"] == user\_id or log["Defender"] == user\_id]

    if not filtered:
        return await update.message.reply\_text("⚔️ No recent PvP activity found.")

    msg = "📜 \*Your Recent Battles:\*\n\n"
    for log in filtered[-10:][::-1]:
        msg += (f"▪️ [{log['Timestamp']}] {log['Attacker']} vs {log['Defender']} "
                f"({log['Power']} power) → \*{log['Result']}\*\n")"
    await update.message.reply\_text(msg, parse\_mode=ParseMode.MARKDOWN)
# main.py — SkyHustle Unified Version (Part 23 of X)
# ── Referrals Sheet ─────────────────────────────────────────────
referral\_sheet = get\_or\_create\_worksheet(sheet, "Referrals", ["Referrer", "Referred"])

# ── /refer Command ──────────────────────────────────────────────
async def refer(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)

    if not context.args:
        return await update.message.reply\_text("Usage: /refer <referrer\_user\_id>")

    referrer = context.args[0]
    if referrer == user\_id:
        return await update.message.reply\_text("❌ You cannot refer yourself.")

    # Prevent duplicate referrals
    rows = referral\_sheet.get\_all\_records()
    if any(row["Referred"] == user\_id for row in rows):
        return await update.message.reply\_text("⚠️ Referral already used.")

    referral\_sheet.append\_row([referrer, user\_id])

    # Reward both players
    for uid in [referrer, user\_id]:
        try:
            row = resources\_sheet.find(str(uid)).row
            current = int(resources\_sheet.cell(row, 2).value)
            resources\_sheet.update\_cell(row, 2, current + 100)
            update\_score(int(uid), 5)
        except:
            continue

    await update.message.reply\_text("🎉 Referral successful! Both users received 100 gold.")
# main.py — SkyHustle Unified Version (Part 24 of X)
# ── Timers Sheet for Construction ───────────────────────────────
timer\_sheet = get\_or\_create\_worksheet(sheet, "Timers", ["ID", "Name", "EndsAt"])

# ── /build <name> <duration\_in\_min> ─────────────────────────────
async def build\_timer(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    if len(context.args) != 2:
        return await update.message.reply\_text("Usage: /build <building\_name> <duration\_in\_minutes>")

    name = context.args[0]
    try:
        duration = int(context.args[1])
    except ValueError:
        return await update.message.reply\_text("❌ Invalid duration.")

    end\_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
    timestamp = end\_time.isoformat()

    # Remove old timer if exists
    try:
        row = timer\_sheet.find(user\_id).row
        timer\_sheet.delete\_rows(row)
    except:
        pass

    timer\_sheet.append\_row([user\_id, name, timestamp])
    await update.message.reply\_text(f"🔧 Building \*{name}\* started. Ends in {duration} min.", parse\_mode=ParseMode.MARKDOWN)"

# ── /status Command ─────────────────────────────────────────────
async def status(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    try:
        row = timer\_sheet.find(user\_id).row
        name = timer\_sheet.cell(row, 2).value
        ends\_at = datetime.datetime.fromisoformat(timer\_sheet.cell(row, 3).value)
        now = datetime.datetime.utcnow()
        remaining = (ends\_at - now).total\_seconds()

        if remaining <= 0:
            timer\_sheet.delete\_rows(row)
            await update.message.reply\_text(f"✅ \*{name}\* construction completed!", parse\_mode=ParseMode.MARKDOWN)"
        else:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply\_text(
                f"⏳ \*{name}\* will complete in {mins}m {secs}s.","
                parse\_mode=ParseMode.MARKDOWN
            )
    except:
        await update.message.reply\_text("📭 No active construction timer.")
# main.py — SkyHustle Unified Version (Part 25 of X)
# ── BM Crate Logic ──────────────────────────────────────────────
BM\_CRATE\_REWARDS = [
    {"type": "gold", "amount": 200},
    {"type": "iron", "amount": 150},
    {"type": "tech", "amount": 100},
    {"type": "infantry", "amount": 3},
    {"type": "sniper", "amount": 2},
    {"type": "tank", "amount": 1},
]


# ── /setname Command ─────────────────────────────────────────────
async def setname(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)

    if not context.args:
        return await update.message.reply\_text("Usage: /setname <your\_name>")

    new\_name = " ".join(context.args).strip()[:20]  # limit to 20 characters

    try:
        row = players\_sheet.find(user\_id).row
        players\_sheet.update\_cell(row, 2, new\_name)
        await update.message.reply\_text(f"✅ Name set to \*{new\_name}\*!", parse\_mode=ParseMode.MARKDOWN)"
    except:
        await update.message.reply\_text("❌ Could not update your name.")

# ── /bmcrate Command ────────────────────────────────────────────
async def bmcrate(update: Update, context: ContextTypes.DEFAULT\_TYPE):
    user\_id = str(update.effective\_user.id)
    reward = random.choice(BM\_CRATE\_REWARDS)

    if reward["type"] in ["gold", "iron", "tech"]:
        row = resources\_sheet.find(user\_id).row
        col\_map = {"gold": 2, "iron": 3, "tech": 4}
        col = col\_map[reward["type"]]
        current = int(resources\_sheet.cell(row, col).value)
        resources\_sheet.update\_cell(row, col, current + reward["amount"])
    else:
        row = army\_sheet.find(user\_id).row
        col\_map = {"infantry": 2, "sniper": 3, "tank": 4}
        col = col\_map[reward["type"]]
        current = int(army\_sheet.cell(row, col).value)
        army\_sheet.update\_cell(row, col, current + reward["amount"])

    await update.message.reply\_text(
        f"🎁 You opened a BM Crate and received:\n+{reward['amount']} {reward['type'].capitalize()}!",
        parse\_mode=ParseMode.MARKDOWN
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add\_handler(CommandHandler("start", start))
    app.add\_handler(CommandHandler("attack", attack))
    app.add\_handler(CommandHandler("research", research))
    app.add\_handler(CommandHandler("collect", collect))
    app.add\_handler(CommandHandler("zones", zones))
    app.add\_handler(CommandHandler("capture", capture))
    app.add\_handler(CommandHandler("missions", missions))
    app.add\_handler(CommandHandler("claim", claim))
    app.add\_handler(CommandHandler("faction", faction))
    app.add\_handler(CommandHandler("base", base))
    app.add\_handler(CommandHandler("expand", expand))
    app.add\_handler(CommandHandler("daily", daily))
    app.add\_handler(CommandHandler("blackmarket", blackmarket))
    app.add\_handler(CommandHandler("spy", spy))
    app.add\_handler(CommandHandler("inbox", inbox))
    app.add\_handler(CommandHandler("raid", raid))
    app.add\_handler(CommandHandler("fight", fight))
    app.add\_handler(CommandHandler("event", event))
    app.add\_handler(CommandHandler("trigger\_event", trigger\_event))
    app.add\_handler(CommandHandler("leaderboard", leaderboard))
    app.add\_handler(CommandHandler("trade", trade))
    app.add\_handler(CommandHandler("give\_gold", give\_gold))
    app.add\_handler(CommandHandler("faction\_war", faction\_war))

    # Callback Queries
    app.add\_handler(CallbackQueryHandler(main\_menu, pattern="^main\_menu$"))
    app.add\_handler(CallbackQueryHandler(build\_menu, pattern="^build\_menu$"))
    app.add\_handler(CallbackQueryHandler(handle\_build\_action, pattern="^build\_"))
    app.add\_handler(CallbackQueryHandler(train\_menu, pattern="^train\_menu$"))
    app.add\_handler(CallbackQueryHandler(handle\_train\_action, pattern="^train\_"))
    app.add\_handler(CallbackQueryHandler(attack\_menu, pattern="^attack\_menu$"))
    app.add\_handler(CallbackQueryHandler(faction, pattern="^faction\_menu$"))
    app.add\_handler(CallbackQueryHandler(handle\_faction\_choice, pattern="^faction\_"))
    app.add\_handler(CallbackQueryHandler(blackmarket, pattern="^store\_menu$"))
    app.add\_handler(CallbackQueryHandler(handle\_blackmarket, pattern="^bm\_"))
    app.add\_handler(CallbackQueryHandler(missions, pattern="^mission\_menu$"))
    app.add\_handler(CallbackQueryHandler(inbox, pattern="^inbox\_menu$"))
    app.add\_handler(CallbackQueryHandler(event, pattern="^event\_menu$"))
    app.add\_handler(CallbackQueryHandler(base, pattern="^base\_menu$"))
    app.add\_handler(CallbackQueryHandler(leaderboard, pattern="^rank\_menu$"))
    app.add\_handler(CallbackQueryHandler(zones, pattern="^zone\_menu$"))
    app.add\_handler(CallbackQueryHandler(research, pattern="^research\_menu$"))

    app.add\_handler(CommandHandler("setname", setname))
    app.add\_handler(CommandHandler("bmcrate", bmcrate))
    app.add\_handler(CommandHandler("my\_battles", my\_battles))

    
    app.add\_handler(CallbackQueryHandler(zones, pattern="^zone\_menu$"))
    app.add\_handler(CallbackQueryHandler(attack\_menu, pattern="^attack\_menu$"))
    app.add\_handler(CallbackQueryHandler(research, pattern="^research\_menu$"))
    app.add\_handler(CallbackQueryHandler(blackmarket, pattern="^store\_menu$"))
    app.add\_handler(CallbackQueryHandler(missions, pattern="^mission\_menu$"))
    app.add\_handler(CallbackQueryHandler(inbox, pattern="^inbox\_menu$"))
    app.add\_handler(CallbackQueryHandler(faction, pattern="^faction\_menu$"))
    app.add\_handler(CallbackQueryHandler(event, pattern="^event\_menu$"))
    app.add\_handler(CallbackQueryHandler(base, pattern="^base\_menu$"))
    app.add\_handler(CallbackQueryHandler(leaderboard, pattern="^rank\_menu$"))

    app.run\_polling()

# ── Launch Bot ──────────────────────────────────────────────────
if \_\_name\_\_ == "\_\_main\_\_":
    main()
















