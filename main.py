# ===============================
# SkyHustle: HyperClean Part 1
# ===============================

import os
import json
import base64
import asyncio
from datetime import datetime, timedelta, date

import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ===============================
# Google Sheet Connection
# ===============================

def get_sheet():
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit")

players_sheet = get_sheet().worksheet("SkyHustle")

# ===============================
# Data Loading and Saving
# ===============================

def get_all_players():
    records = players_sheet.get_all_records()
    return records

def find_player_by_chatid(cid):
    records = get_all_players()
    for idx, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = idx + 2  # because header is row 1
            row["Army"] = json.loads(row["Army"]) if row.get("Army") else {"scout":0, "tank":0, "drone":0}
            row["Items"] = json.loads(row["Items"]) if row.get("Items") else {}
            return row
    return None

def save_player(p):
    players_sheet.update(f"A{p['_row']}:L{p['_row']}", [[
        p["ChatID"],
        p["Name"],
        p["Ore"],
        p["Energy"],
        p["Credits"],
        json.dumps(p["Army"]),
        p["Zone"],
        p["ShieldUntil"],
        p["DailyStreak"],
        p["LastDaily"],
        p.get("BlackMarketUnlocked", False),
        json.dumps(p["Items"])
    ]])

def create_new_player(cid):
    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": {"scout": 0, "tank": 0, "drone": 0},
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "BlackMarketUnlocked": False,
        "Items": {}
    }
    players_sheet.append_row([
        new_player["ChatID"],
        new_player["Name"],
        new_player["Ore"],
        new_player["Energy"],
        new_player["Credits"],
        json.dumps(new_player["Army"]),
        new_player["Zone"],
        new_player["ShieldUntil"],
        new_player["DailyStreak"],
        new_player["LastDaily"],
        new_player["BlackMarketUnlocked"],
        json.dumps(new_player["Items"])
    ])
    return find_player_by_chatid(cid)

def find_or_create_player(cid):
    p = find_player_by_chatid(cid)
    if not p:
        p = create_new_player(cid)
    return p

# ===============================
# BACKGROUND SYSTEM
# ===============================

async def check_global_events():
    pass  # Placeholder for future (radiation storms, meteor strikes etc.)

# ===============================
# BACKSTORY
# ===============================

BACKSTORY = (
    "🌌 *SkyHustle Lore*\n"
    "Centuries after Earth's collapse, humanity scattered across the stars.\n"
    "You are among the daring few trying to control Hyperion — a planet rich with Ore, but riddled with dangers.\n"
    "Forge your empire, rise through technology, crush rivals, and become the ultimate Sky Lord."
)

# ===============================
# End of Part 1
# ===============================

# --- PART 2 will continue from here seamlessly ---

# Handle incoming player messages and actions
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()

    if text.startswith(",start"):
        intro = (
            "🌌 *Welcome to SkyHustle!*\n"
            "Centuries from now, the Hyperion core pulses with boundless energy.\n"
            "You are a Commander in the New Galactic Order.\n"
            "Gather ore, strengthen your army, dominate the zones.\n\n"
            "💠 Use ,name <alias> to set your callsign.\n"
            "💠 Use ,status to view your progress.\n"
            "💠 Use ,mine ore 1 to start mining resources.\n\n"
            "🛡 Glory and power await!"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠️ Usage: ,name <alias>")
        ocid, _ = find_by_name(alias)
        if ocid and ocid != cid:
            return await update.message.reply_text("❌ That alias is already taken.")
        p["Name"] = alias
        save_player(p)
        return await update.message.reply_text(f"✅ Callsign set to *{alias}*!", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p.get("Items", "{}"))
        shield = p["ShieldUntil"] if p["ShieldUntil"] else "None"
        msg = (
            f"📊 *Commander {p['Name'] or 'Unnamed'}*\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🛡 Shield Until: {shield}\n"
            f"⚔ Army: {army}\n"
            f"🎁 Items: {items or 'None'}\n"
            f"🌍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
        today = date.today()
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 You've already claimed your daily reward today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        p["Credits"] += 50
        p["Energy"] += 20
        p["DailyStreak"] = p["DailyStreak"] + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        save_player(p)
        return await update.message.reply_text(f"🎉 +50 Credits, +20 Energy! Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠️ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except ValueError:
            return await update.message.reply_text("⚠️ Count must be a number.")

        if p["Energy"] < count * 5:
            return await update.message.reply_text("⚠️ Not enough energy.")

        ore_gain = 20 * count + (p["RefineryLevel"] * 5)
        credits_gain = 10 * count
        p["Ore"] += ore_gain
        p["Credits"] += credits_gain
        p["Energy"] -= count * 5
        save_player(p)
        return await update.message.reply_text(f"⛏️ Mined {ore_gain} Ore and earned {credits_gain} Credits.")

    # If no valid command matched
    await update.message.reply_text("❓ Unknown command. Type ,help for available actions.")
    # === Army Forging and Item Use ===

    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚒️ Usage: ,forge <unit> <count>")

        unit, count = parts[1], parts[2]
        try:
            count = int(count)
        except ValueError:
            return await update.message.reply_text("⚒️ Count must be a number.")

        if unit not in ["scout", "tank", "drone"]:
            return await update.message.reply_text("⚒️ Invalid unit. Choose scout, tank, or drone.")

        cost_ore, cost_credits = {"scout": (10, 5), "tank": (30, 20), "drone": (20, 10)}[unit]
        if p["Ore"] < cost_ore * count or p["Credits"] < cost_credits * count:
            return await update.message.reply_text("⚠️ Not enough Ore or Credits.")

        army = json.loads(p["Army"])
        army[unit] = army.get(unit, 0) + count
        p["Ore"] -= cost_ore * count
        p["Credits"] -= cost_credits * count
        p["Army"] = json.dumps(army)
        save_player(p)

        return await update.message.reply_text(f"✅ Forged {count} {unit}(s)!")

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛡 Usage: ,use <item>")

        item_id = parts[1]
        items = json.loads(p.get("Items", "{}"))

        if item_id not in items or items[item_id] <= 0:
            return await update.message.reply_text("⚠️ You don't own that item.")

        # Perishable item logic
        if item_id.startswith("infinityscout") or item_id == "reviveall":
            items[item_id] -= 1
            if items[item_id] <= 0:
                del items[item_id]

        if item_id == "reviveall":
            army = json.loads(p["Army"])
            for unit in army:
                army[unit] += 5
            p["Army"] = json.dumps(army)
            await update.message.reply_text("🛡 All standard army units revived!")

        if item_id == "hazmat":
            await update.message.reply_text("☢️ Your units are now radiation-proof for zone exploration!")

        p["Items"] = json.dumps(items)
        save_player(p)
        return await update.message.reply_text(f"✅ Used {item_id}.")
        # === Black Market Unlocking and Buying ===

    if text.startswith(",unlockbm"):
        if p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("✅ Black Market already unlocked!")
        if p["Credits"] < 1000:
            return await update.message.reply_text("💳 Need 1000 credits to unlock the Black Market.")
        p["Credits"] -= 1000
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("🖤 Black Market access unlocked!")

    if text.startswith(",blackmarket"):
        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 Black Market is locked. Use ,unlockbm first.")
        shop = (
            "🖤 *Black Market Deals:*\n"
            "`,buy infinityscout1` - 100 credits\n"
            "`,buy reviveall` - 500 credits\n"
            "`,buy hazmat` - 250 credits\n"
            "\nUse `,buy <item>` to purchase."
        )
        return await update.message.reply_text(shop, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buy <item>")
        item = parts[1]

        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 Unlock Black Market first.")

        prices = {"infinityscout1": 100, "reviveall": 500, "hazmat": 250}
        if item not in prices:
            return await update.message.reply_text("❌ Item not found in Black Market.")

        if p["Credits"] < prices[item]:
            return await update.message.reply_text("💳 Not enough credits.")

        p["Credits"] -= prices[item]
        items = json.loads(p.get("Items", "{}"))
        items[item] = items.get(item, 0) + 1
        p["Items"] = json.dumps(items)
        save_player(p)

        return await update.message.reply_text(f"🛒 Purchased {item} successfully!")
        # === Item Usage System ===

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🎯 Usage: ,use <item>")
        item = parts[1]
        items = json.loads(p.get("Items", "{}"))

        if items.get(item, 0) <= 0:
            return await update.message.reply_text("❌ You don't own this item!")

        if item == "infinityscout1":
            return await use_infinityscout(p, update)
        if item == "reviveall":
            return await use_reviveall(p, update)
        if item == "hazmat":
            return await use_hazmat(p, update)

        return await update.message.reply_text("❓ Unknown item.")

# === Helper Functions for Items ===

async def use_infinityscout(player, update):
    items = json.loads(player.get("Items", "{}"))
    if items.get("infinityscout1", 0) > 0:
        items["infinityscout1"] -= 1
        player["Items"] = json.dumps(items)
        save_player(player)
        return await update.message.reply_text("👁 Infinity Scout used! Revealing target details temporarily...")
    return await update.message.reply_text("❌ No Infinity Scout available.")

async def use_reviveall(player, update):
    items = json.loads(player.get("Items", "{}"))
    if items.get("reviveall", 0) > 0:
        items["reviveall"] -= 1
        player["Items"] = json.dumps(items)
        army = json.loads(player["Army"])
        for unit in army:
            army[unit] += 5  # Revive 5 of each unit
        player["Army"] = json.dumps(army)
        save_player(player)
        return await update.message.reply_text("⚡ All standard units revived!")
    return await update.message.reply_text("❌ No Revive-All item available.")

async def use_hazmat(player, update):
    items = json.loads(player.get("Items", "{}"))
    if items.get("hazmat", 0) > 0:
        await update.message.reply_text("☢️ Hazmat Drone ready! You can now enter Radiation Zones!")
    else:
        await update.message.reply_text("❌ No Hazmat Drone owned.")
        # === Zone Control System ===

    if text.startswith(",map"):
        zones_status = "🌍 *Zone Control Map:*\n"
        for zone in enabled_zones:
            owner_id = zones.get(zone)
            if owner_id:
                owner_row = find_player_by_chatid(owner_id)
                owner_name = owner_row["Name"] if owner_row else "Unknown"
                zones_status += f"🔸 {zone}: {owner_name}\n"
            else:
                zones_status += f"🔹 {zone}: Unclaimed\n"
        return await update.message.reply_text(zones_status, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("📍 Usage: ,claim <zone>")

        zone_name = parts[1].capitalize()
        if zone_name not in enabled_zones:
            return await update.message.reply_text("❌ Invalid zone.")

        if zones.get(zone_name) is not None:
            return await update.message.reply_text("⚠️ Zone already claimed.")

        if p["Credits"] < 100:
            return await update.message.reply_text("💳 Need at least 100 credits to claim a zone.")

        zones[zone_name] = p["ChatID"]
        p["Zone"] = zone_name
        p["Credits"] -= 100
        save_player(p)

        return await update.message.reply_text(f"🏴 Successfully claimed {zone_name}!")
    # === Player Missions ===

    if text.startswith(",missions"):
        today = date.today()
        missions_text = "🎯 *Current Missions:*\n"
        missions = {
            "mine5": {"desc": "Mine 5 ores today", "reward": 50},
            "win1": {"desc": "Win 1 attack today", "reward": 75},
            "forge5": {"desc": "Forge 5 units today", "reward": 60},
        }

        # Initialize player missions if empty
        if not p.get("Missions"):
            p["Missions"] = json.dumps({k: False for k in missions.keys()})
            p["LastMissionReset"] = str(today)
            save_player(p)

        # Auto-reset missions daily
        if p.get("LastMissionReset") != str(today):
            p["Missions"] = json.dumps({k: False for k in missions.keys()})
            p["LastMissionReset"] = str(today)
            save_player(p)

        player_missions = json.loads(p["Missions"])

        for mission_id, status in player_missions.items():
            completed = "✅" if status else "❌"
            missions_text += f"{completed} {missions[mission_id]['desc']} (+{missions[mission_id]['reward']} credits)\n"

        missions_text += "\n_Complete missions and earn credits!_"

        return await update.message.reply_text(missions_text, parse_mode=ParseMode.MARKDOWN)

# === Mission Progress Tracker Functions ===

def check_mission_progress(player, action):
    if not player.get("Missions"):
        return

    missions = json.loads(player["Missions"])

    if action == "mine":
        if "mine5" in missions and not missions["mine5"]:
            player["MissionsProgress"] = player.get("MissionsProgress", {})
            player["MissionsProgress"]["mine5"] = player["MissionsProgress"].get("mine5", 0) + 1
            if player["MissionsProgress"]["mine5"] >= 5:
                missions["mine5"] = True
                player["Credits"] += 50

    if action == "win":
        if "win1" in missions and not missions["win1"]:
            missions["win1"] = True
            player["Credits"] += 75

    if action == "forge":
        if "forge5" in missions and not missions["forge5"]:
            player["MissionsProgress"] = player.get("MissionsProgress", {})
            player["MissionsProgress"]["forge5"] = player["MissionsProgress"].get("forge5", 0) + 1
            if player["MissionsProgress"]["forge5"] >= 5:
                missions["forge5"] = True
                player["Credits"] += 60

    player["Missions"] = json.dumps(missions)
    save_player(player)
# Continuation from previous...

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buy <item>")
        item = parts[1]
        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 Unlock Black Market access first.")
        price = black_market_price(item.replace("1", ""))
        if p["Credits"] < price:
            return await update.message.reply_text("💳 Not enough credits.")
        p["Credits"] -= price
        p["Items"][item] = p["Items"].get(item, 0) + 1
        save_player(p)
        return await update.message.reply_text(f"🛒 Purchased {item}!")

    if text.startswith(",unlockbm"):
        if p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("✅ Black Market already unlocked.")
        if p["Credits"] < 1000:
            return await update.message.reply_text("💳 Need 1000 credits to unlock.")
        p["Credits"] -= 1000
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("🖤 Black Market access unlocked!")

    if text.startswith(",missions"):
        return await update.message.reply_text("🎯 Mission system coming soon...")

    if text.startswith(",map"):
        out = "🗺️ *Zone Control:*\n"
        for z, o in zones.items():
            owner = players.get(o, {}).get("Name", "Unclaimed")
            out += f"{z}: {owner}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in zones:
            return await update.message.reply_text("⚡ Usage: ,claim <zone>")
        if zones[parts[1]]:
            return await update.message.reply_text("⚠️ Zone already claimed.")
        if p["Credits"] < 100:
            return await update.message.reply_text("💳 Need 100 credits to claim zone.")
        zones[parts[1]] = p["ChatID"]
        p["Zone"] = parts[1]
        p["Credits"] -= 100
        save_player(p)
        return await update.message.reply_text(f"🏴 You now control {parts[1]}.")
    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")
        enemy_alias = parts[1]
        target_row = find_player_by_name(enemy_alias)
        if not target_row:
            return await update.message.reply_text("🎯 Target not found!")

        has_infinityscout = p["Items"].get("infinityscout1", 0) > 0
        if not has_infinityscout:
            return await update.message.reply_text("🔍 You need an *Infinity Scout* to perform this action!")

        scout_data = (
            f"🛰️ *Scout Report on {target_row['Name']}*\n"
            f"Ore: {target_row['Ore']} | Credits: {target_row['Credits']}\n"
            f"Army: {target_row['Army']}\n"
            f"ShieldUntil: {target_row['ShieldUntil'] or 'None'}"
        )
        # Use up scout
        p["Items"]["infinityscout1"] -= 1
        if p["Items"]["infinityscout1"] == 0:
            del p["Items"]["infinityscout1"]
        save_player(p)
        return await update.message.reply_text(scout_data, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",store"):
        store = (
            "🏪 *SkyHustle Store:*\n"
            "`upgrade refinery` - 100 credits\n"
            "`upgrade lab` - 150 credits\n"
            "`upgrade defense` - 120 credits\n"
            "`upgrade shield` - 200 credits\n"
            "\nUse `,upgrade <type>` to buy upgrades!"
        )
        return await update.message.reply_text(store, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",upgrade"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛠️ Usage: ,upgrade <type>")
        upg = parts[1]
        if upg not in ["refinery", "lab", "defense", "shield"]:
            return await update.message.reply_text("🛠️ Invalid upgrade type.")

        upgrade_cost = {"refinery": 100, "lab": 150, "defense": 120, "shield": 200}[upg]
        if p["Credits"] < upgrade_cost:
            return await update.message.reply_text("💳 Not enough credits.")

        p["Credits"] -= upgrade_cost
        if upg == "refinery":
            p["RefineryLevel"] += 1
        elif upg == "lab":
            p["LabLevel"] += 1
        elif upg == "defense":
            p["DefenseLevel"] += 1
        elif upg == "shield":
            p["ShieldUntil"] = (datetime.now() + timedelta(hours=6)).isoformat()

        save_player(p)
        return await update.message.reply_text(f"✅ {upg.capitalize()} upgraded!")
    if text.startswith(",missions"):
        today = date.today()
        if p["MissionsDone"].get(str(today), False):
            return await update.message.reply_text("🎯 All daily missions completed already!")

        missions_today = [
            {"task": "Mine 100 ore", "reward": 50},
            {"task": "Win 1 battle", "reward": 100},
            {"task": "Claim daily reward", "reward": 30},
        ]

        mission_text = "*🎯 Daily Missions:*\n"
        for idx, m in enumerate(missions_today, 1):
            mission_text += f"{idx}. {m['task']} ➡️ +{m['reward']} credits\n"

        return await update.message.reply_text(mission_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claimmission"):
        today = date.today()
        if p["MissionsDone"].get(str(today), False):
            return await update.message.reply_text("✅ Already claimed today's mission rewards.")

        p["Credits"] += 150
        p["MissionsDone"][str(today)] = True
        save_player(p)
        return await update.message.reply_text("🎉 Mission rewards claimed! +150 credits.")

    if text.startswith(",banner"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏳️ Usage: ,banner <emoji>")
        emoji = parts[1]
        p["Banner"] = emoji
        save_player(p)
        return await update.message.reply_text(f"🏳️ Banner set to {emoji}!")

    if text.startswith(",rank"):
        all_players = players_sheet.get_all_records()
        sorted_players = sorted(all_players, key=lambda x: int(x.get("Wins", 0)), reverse=True)
        ranking_text = "*🏆 Top Commanders:*\n"
        for i, pl in enumerate(sorted_players[:10], start=1):
            ranking_text += f"{i}. {pl.get('Name', 'Unknown')} - {pl.get('Wins', 0)} wins\n"

        return await update.message.reply_text(ranking_text, parse_mode=ParseMode.MARKDOWN)
    if text.startswith(",pve"):
        # Example simple PvE battle
        enemy_power = 100
        player_power = sum(p["Army"].values()) * 10 + (p["RefineryLevel"] * 5)

        if player_power == 0:
            return await update.message.reply_text("⚠️ You have no army units to battle with!")

        if player_power >= enemy_power:
            reward_ore = 200
            p["Ore"] += reward_ore
            save_player(p)
            return await update.message.reply_text(f"🏴‍☠️ Victory over PvE! Looted {reward_ore} ore!")

        else:
            return await update.message.reply_text("💥 PvE enemy was too strong! Train more units and try again.")

    if text.startswith(",zoneinfo"):
        out = "*🌍 Current Zone Control:*\n"
        zones = players_sheet.get_all_records()
        for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
            holder = next((p['Name'] for p in zones if p.get('Zone') == z), "Unclaimed")
            out += f"🔹 {z}: {holder}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",resetdaily"):
        # Admin/Testing Only
        p["DailyStreak"] = 0
        p["LastDaily"] = ""
        save_player(p)
        return await update.message.reply_text("🔄 Daily streak reset.")
    if text.startswith(",profile"):
        army = json.loads(p["Army"])
        items_owned = json.loads(p["Items"])
        shield_time = "🛡 Active" if p.get("ShieldUntil") and datetime.fromisoformat(p["ShieldUntil"]) > datetime.now() else "❌ None"
        return await update.message.reply_text(
            f"*🧑‍🚀 Commander Profile:*\n"
            f"• Name: {p['Name'] or 'Unknown'}\n"
            f"• Ore: {p['Ore']}  ⚡ Energy: {p['Energy']}  💳 Credits: {p['Credits']}\n"
            f"• Units: {army}\n"
            f"• Zone Controlled: {p['Zone'] or 'None'}\n"
            f"• Shield: {shield_time}\n"
            f"• Wins: {p.get('Wins',0)} / Losses: {p.get('Losses',0)}\n"
            f"• Items: {items_owned}",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",zones"):
        # View full map of zones
        zone_rows = players_sheet.get_all_records()
        out = "*🌌 SkyHustle Zones:*\n"
        zone_list = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        for z in zone_list:
            owner = next((pl["Name"] for pl in zone_rows if pl.get("Zone") == z), "Unclaimed")
            out += f"• {z}: {owner}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",events"):
        # Future feature - scheduled world events
        return await update.message.reply_text(
            "🌟 *Upcoming Events:*\n"
            "• Radiation Storm (3 hours): Prepare Hazmat Units!\n"
            "• PvP Blitz: +20% Attack Strength Next Hour\n"
            "• Pirate Raid: Incoming in Delta Zone\n",
            parse_mode=ParseMode.MARKDOWN
        )
    if text.startswith(",missions"):
        today = datetime.now().date()
        missions = [
            {"desc": "Mine 100 Ore", "check": lambda p: p["Ore"] >= 100, "reward": 100},
            {"desc": "Own 5 Units", "check": lambda p: sum(json.loads(p["Army"]).values()) >= 5, "reward": 150},
            {"desc": "Login 2 Days Streak", "check": lambda p: int(p.get("DailyStreak", 0)) >= 2, "reward": 200},
        ]

        completed = []
        for mission in missions:
            if mission["check"](p):
                completed.append(f"✅ {mission['desc']} (+{mission['reward']} credits)")
                p["Credits"] += mission["reward"]
        if completed:
            save_player(p)
            return await update.message.reply_text(
                "*🎯 Missions Completed:*\n" + "\n".join(completed),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            return await update.message.reply_text(
                "🎯 No missions completed yet. Keep pushing!",
                parse_mode=ParseMode.MARKDOWN
            )

    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2 or parts[1] not in ["speed", "armor"]:
            return await update.message.reply_text(
                "🧪 Usage: ,research speed | armor",
                parse_mode=ParseMode.MARKDOWN
            )
        tech = parts[1]
        cost = 150
        if p["Credits"] < cost:
            return await update.message.reply_text(
                "💳 Not enough credits to research.",
                parse_mode=ParseMode.MARKDOWN
            )
        p["Credits"] -= cost
        p.setdefault("Research", {"speed": 0, "armor": 0})
        p["Research"][tech] += 1
        save_player(p)
        return await update.message.reply_text(
            f"🧪 {tech.capitalize()} technology upgraded to Level {p['Research'][tech]}!",
            parse_mode=ParseMode.MARKDOWN
        )
    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text(
                "🏰 Usage: ,claim <zone>",
                parse_mode=ParseMode.MARKDOWN
            )
        zone = parts[1].capitalize()
        if zone not in enabled_zones:
            return await update.message.reply_text(
                "🏰 Invalid zone. Available: Alpha, Beta, Gamma, Delta, Epsilon.",
                parse_mode=ParseMode.MARKDOWN
            )
        if p["Credits"] < 300:
            return await update.message.reply_text(
                "💳 You need 300 credits to claim a zone!",
                parse_mode=ParseMode.MARKDOWN
            )
        current_owner = find_zone_owner(zone)
        if current_owner:
            return await update.message.reply_text(
                f"⚔️ Zone already claimed by {current_owner['Name']}!",
                parse_mode=ParseMode.MARKDOWN
            )
        p["Zone"] = zone
        p["Credits"] -= 300
        save_player(p)
        return await update.message.reply_text(
            f"🏰 You have claimed Zone {zone}!",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",zones"):
        response = "*🌍 Zone Status:*\n"
        for zone in enabled_zones:
            owner = find_zone_owner(zone)
            owner_name = owner["Name"] if owner else "Unclaimed"
            response += f"`{zone}` - {owner_name}\n"
        return await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
    if text.startswith(",missions"):
        return await update.message.reply_text(
            "*🎯 Mission System:*\n"
            "`,daily` - Claim daily rewards.\n"
            "`,mine ore <count>` - Mine Hyperion ore.\n"
            "`,forge <unit> <count>` - Forge military units.\n"
            "`,attack <enemy>` - Attack another commander.\n"
            "\nMore missions coming soon!",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",store"):
        store = (
            "🛒 *Official Store Packages:*\n"
            "`,buypack basic` - 300 Credits for 50 Ore & 10 Energy (Cost: 150 credits)\n"
            "`,buypack elite` - 800 Credits for 150 Ore & 40 Energy (Cost: 400 credits)\n"
            "`,buypack legend` - 1500 Credits for 400 Ore & 100 Energy (Cost: 700 credits)\n"
            "\nUse `,buypack <basic/elite/legend>` to purchase."
        )
        return await update.message.reply_text(store, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buypack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text(
                "🛒 Usage: ,buypack <basic/elite/legend>",
                parse_mode=ParseMode.MARKDOWN
            )
        pack = parts[1].lower()
        if pack == "basic":
            cost, ore_gain, energy_gain = 150, 50, 10
        elif pack == "elite":
            cost, ore_gain, energy_gain = 400, 150, 40
        elif pack == "legend":
            cost, ore_gain, energy_gain = 700, 400, 100
        else:
            return await update.message.reply_text(
                "🛒 Invalid package. Use basic, elite, or legend.",
                parse_mode=ParseMode.MARKDOWN
            )

        if p["Credits"] < cost:
            return await update.message.reply_text(
                "💳 Not enough credits!",
                parse_mode=ParseMode.MARKDOWN
            )

        p["Credits"] -= cost
        p["Ore"] += ore_gain
        p["Energy"] += energy_gain
        save_player(p)
        return await update.message.reply_text(
            f"🎁 Purchased {pack.capitalize()} pack: +{ore_gain} Ore, +{energy_gain} Energy!",
            parse_mode=ParseMode.MARKDOWN
        )
    if text.startswith(",rank"):
        ranking = sorted(players_sheet.get_all_records(), key=lambda x: x.get("Wins", 0), reverse=True)
        leaderboard = "🏆 *Commander Rankings:*\n"
        for idx, p_data in enumerate(ranking[:10], 1):
            leaderboard += f"{idx}. {p_data.get('Name', 'Unknown')} - {p_data.get('Wins', 0)} Wins\n"
        return await update.message.reply_text(leaderboard, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",stats"):
        player_data = f"*📊 Your Expanded Stats:*\n" \
                      f"Name: {p['Name']}\n" \
                      f"Ore: {p['Ore']} | Energy: {p['Energy']} | Credits: {p['Credits']}\n" \
                      f"Wins: {p.get('Wins',0)} | Losses: {p.get('Losses',0)}\n" \
                      f"Shield Until: {p['ShieldUntil'] or 'None'}\n" \
                      f"Zone: {p['Zone'] or 'Unclaimed'}\n" \
                      f"Black Market Access: {'✅' if p.get('BlackMarketUnlocked') else '❌'}"
        return await update.message.reply_text(player_data, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",zonecontrol"):
        zones_status = ""
        all_zones = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        control = {}
        sheet_records = players_sheet.get_all_records()
        for rec in sheet_records:
            zone = rec.get("Zone")
            if zone:
                control[zone] = rec.get("Name", "Unknown")

        for z in all_zones:
            owner = control.get(z, "Unclaimed")
            zones_status += f"📍 {z}: {owner}\n"

        return await update.message.reply_text(
            f"*🌍 Current Zone Control:*\n{zones_status}",
            parse_mode=ParseMode.MARKDOWN
        )
    if text.startswith(",missions"):
        daily_mission = f"🎯 *Daily Mission:* Mine 500 ore and forge 5 units!\n" \
                        "Rewards: +100 credits, +1 faction point"
        return await update.message.reply_text(daily_mission, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claimmission"):
        sheet_records = players_sheet.get_all_records()
        for rec in sheet_records:
            if str(rec.get("ChatID")) == str(cid):
                if rec.get("Ore", 0) >= 500 and rec.get("Army"):
                    army = json.loads(rec.get("Army", "{}"))
                    total_units = sum(army.values())
                    if total_units >= 5:
                        p["Credits"] += 100
                        update_player(p)
                        return await update.message.reply_text("🎖️ Mission complete! +100 Credits earned.")
                    else:
                        return await update.message.reply_text("⚠️ Not enough units forged yet!")
                else:
                    return await update.message.reply_text("⚠️ You haven't mined enough ore yet!")

        return await update.message.reply_text("⚠️ Error validating mission.")

    if text.startswith(",store"):
        store_text = (
            "🏪 *SkyHustle Store:*\n"
            "`package small` - 500 credits = $1\n"
            "`package medium` - 1500 credits = $3\n"
            "`package large` - 5000 credits = $10\n\n"
            "_(For testing, assume you buy using commands)_"
        )
        return await update.message.reply_text(store_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buycredits"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buycredits <small/medium/large>")

        package = parts[1]
        if package == "small":
            p["Credits"] += 500
        elif package == "medium":
            p["Credits"] += 1500
        elif package == "large":
            p["Credits"] += 5000
        else:
            return await update.message.reply_text("❌ Invalid package name.")

        save_player(p)
        return await update.message.reply_text(f"✅ {package.capitalize()} credit package purchased!")
    if text.startswith(",rank"):
        # Simple ELO-style rank simulation
        total_score = p["Wins"] * 10 - p["Losses"] * 5
        if total_score < 0:
            total_score = 0
        p["Rank"] = total_score
        save_player(p)
        return await update.message.reply_text(f"🏆 Your current SkyHustle Rank Score: {p['Rank']} points.")

    if text.startswith(",faction"):
        factions_text = (
            "🏳️ Choose your faction!\n"
            "`join Solar` ☀️\n"
            "`join Lunar` 🌙\n"
            "`join Stellar` ✨\n\n"
            "Use `,join <faction>` to select!"
        )
        return await update.message.reply_text(factions_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",join"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠️ Usage: ,join <Solar/Lunar/Stellar>")
        faction = parts[1].capitalize()
        if faction not in ["Solar", "Lunar", "Stellar"]:
            return await update.message.reply_text("❌ Invalid faction.")
        p["Faction"] = faction
        save_player(p)
        return await update.message.reply_text(f"🚩 You have joined the *{faction}* faction!", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",zones"):
        zones_control = ""
        sheet_records = players_sheet.get_all_records()
        for rec in sheet_records:
            zone_name = rec.get("Zone", "")
            if zone_name:
                zones_control += f"{zone_name}: {rec.get('Name', 'Unknown')}\n"

        if not zones_control:
            zones_control = "🌌 No zones claimed yet!"
        return await update.message.reply_text(f"🌍 *Current Zone Control:*\n{zones_control}", parse_mode=ParseMode.MARKDOWN)
    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")

        enemy_alias = parts[1]
        target_row = find_player_by_name(enemy_alias)
        if not target_row:
            return await update.message.reply_text("🎯 Target not found for spying!")

        enemy_units = json.loads(target_row.get("Army", "{}"))
        enemy_ore = target_row.get("Ore", 0)
        enemy_credits = target_row.get("Credits", 0)

        # If player owns Infinity Scout, reveal extra information
        reveal_blackmarket = False
        if "infinityscout1" in p["Items"] or "infinityscout2" in p["Items"]:
            reveal_blackmarket = True

        spy_report = (
            f"🕵️ Spy Report for *{target_row['Name']}*:\n"
            f"Units: {enemy_units}\n"
            f"Ore: {enemy_ore}\n"
            f"Credits: {enemy_credits}\n"
        )
        if reveal_blackmarket:
            blackmarket_items = target_row.get("Items", "{}")
            spy_report += f"🖤 Black Market Gear: {blackmarket_items}\n"

        return await update.message.reply_text(spy_report, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",missions"):
        missions_text = (
            "🎯 *Available Missions:*\n"
            "`,mission mine10` - Mine 10 ores\n"
            "`,mission win3` - Win 3 attacks\n"
            "`,mission login7` - Login 7 days in a row\n"
            "Complete missions to earn bonus credits!"
        )
        return await update.message.reply_text(missions_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",mission"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🎯 Usage: ,mission <mission_code>")

        mission = parts[1]
        reward = 0
        if mission == "mine10" and int(p.get("Ore", 0)) >= 200:
            reward = 100
        elif mission == "win3" and int(p.get("Wins", 0)) >= 3:
            reward = 150
        elif mission == "login7" and int(p.get("DailyStreak", 0)) >= 7:
            reward = 200
        else:
            return await update.message.reply_text("⚠️ Mission conditions not met yet.")

        p["Credits"] += reward
        save_player(p)
        return await update.message.reply_text(f"🎖️ Mission complete! +{reward} credits!")
    if text.startswith(",claimzone"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("📍 Usage: ,claimzone <zone_name>")

        zone_name = parts[1].capitalize()
        if zone_name not in enabled_zones:
            return await update.message.reply_text("⚠️ Invalid zone. Available zones: Alpha, Beta, Gamma, Delta, Epsilon")

        # Check ownership
        owner = zones.get(zone_name)
        if owner:
            return await update.message.reply_text(f"🚫 Zone {zone_name} is already owned.")

        # Claim
        zones[zone_name] = p["ChatID"]
        p["Zone"] = zone_name
        save_player(p)
        return await update.message.reply_text(f"✅ You have claimed Zone {zone_name}!")

    if text.startswith(",zoneinfo"):
        output = "🌍 *Zone Ownership:*\n"
        for z in enabled_zones:
            owner_id = zones.get(z)
            owner_name = "Unclaimed"
            if owner_id:
                owner_data = get_player(owner_id)
                owner_name = owner_data["Name"] or "Unknown Commander"
            output += f"- {z}: {owner_name}\n"
        return await update.message.reply_text(output, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",movezone"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🚀 Usage: ,movezone <target_zone>")

        target_zone = parts[1].capitalize()
        if target_zone not in enabled_zones:
            return await update.message.reply_text("⚠️ Invalid zone name.")

        if not p["Zone"]:
            return await update.message.reply_text("🛑 You must own a zone first to move.")

        if target_zone not in adjacency.get(p["Zone"], []):
            return await update.message.reply_text("🛑 You can only move to adjacent zones!")

        # Move
        zones[p["Zone"]] = None  # Release old zone
        zones[target_zone] = p["ChatID"]
        p["Zone"] = target_zone
        save_player(p)
        return await update.message.reply_text(f"🚀 Moved successfully to Zone {target_zone}!")
    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")

        enemy_alias = parts[1]
        enemy_row = find_player_by_name(enemy_alias)
        if not enemy_row:
            return await update.message.reply_text("🎯 Target not found for spying.")

        spy_level = p["RefineryLevel"]
        if spy_level == 0:
            return await update.message.reply_text("🔎 You must upgrade your Lab to enable spying.")

        success_chance = min(90, 30 + spy_level * 10)
        from random import randint
        roll = randint(1, 100)

        if roll <= success_chance:
            army = json.loads(enemy_row["Army"])
            zone = enemy_row["Zone"] or "Unknown"
            info = (
                f"🕵️ *Spy Report: {enemy_alias}*\n"
                f"📍 Zone: {zone}\n"
                f"🤖 Army: {army}\n"
            )
            if enemy_row.get("Items") and "hazmat" in json.loads(enemy_row["Items"]):
                info += "☢️ Has Hazmat Drones\n"
            await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("⚡ Spy attempt failed! They noticed your attempt!")

    if text.startswith(",upgrade"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚙️ Usage: ,upgrade <building>")

        target = parts[1].lower()
        if target not in ["refinery", "lab", "defense"]:
            return await update.message.reply_text("⚙️ Valid upgrades: refinery, lab, defense.")

        cost = 200 + (p[target.capitalize() + "Level"] * 100)
        if p["Credits"] < cost:
            return await update.message.reply_text(f"💳 Not enough credits. Upgrade costs {cost}.")

        p["Credits"] -= cost
        p[target.capitalize() + "Level"] += 1
        save_player(p)
        return await update.message.reply_text(f"🔧 {target.capitalize()} upgraded successfully!")
    if text.startswith(",claimzone"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🚩 Usage: ,claimzone <zone>")

        zone = parts[1].capitalize()
        if zone not in enabled_zones:
            return await update.message.reply_text("🚩 Invalid zone specified.")

        zone_owner = zones.get(zone)
        if zone_owner and zone_owner != cid:
            return await update.message.reply_text("⚠️ Zone already claimed by another Commander.")

        if p["Credits"] < 500:
            return await update.message.reply_text("💳 Need 500 credits to claim a zone!")

        zones[zone] = cid
        p["Zone"] = zone
        p["Credits"] -= 500
        save_player(p)
        return await update.message.reply_text(f"🏴 Zone {zone} claimed successfully!")

    if text.startswith(",missions"):
        today = str(date.today())
        mission = missions.get(cid)
        if not mission or mission["date"] != today:
            missions[cid] = {
                "date": today,
                "task": "Mine 5 ores",
                "progress": 0,
                "goal": 5,
                "reward": 100
            }
            mission = missions[cid]

        msg = (
            f"🎯 *Daily Mission:*\n"
            f"Task: {mission['task']}\n"
            f"Progress: {mission['progress']}/{mission['goal']}\n"
            f"Reward: {mission['reward']} credits"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claimreward"):
        mission = missions.get(cid)
        if not mission or mission["date"] != str(date.today()):
            return await update.message.reply_text("🎯 No active mission today!")

        if mission["progress"] < mission["goal"]:
            return await update.message.reply_text("🎯 Complete the mission first!")

        p["Credits"] += mission["reward"]
        del missions[cid]
        save_player(p)
        return await update.message.reply_text("🏆 Mission reward claimed! Well done, Commander!")
    if text.startswith(",map"):
        msg = "🗺 *Hyperion Zone Control:*\n"
        for zone, owner_cid in zones.items():
            if owner_cid:
                owner_name = players.get(owner_cid, {}).get("Name", "Unknown")
            else:
                owner_name = "Unclaimed"
            msg += f"🏴 {zone}: {owner_name}\n"
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <target alias>")

        target_alias = parts[1]
        target_row = find_player_by_name(target_alias)
        if not target_row:
            return await update.message.reply_text("🎯 Target not found!")

        army = json.loads(target_row["Army"])
        shield_until = target_row.get("ShieldUntil", "")

        if shield_until:
            shield_time = datetime.strptime(shield_until, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < shield_time:
                return await update.message.reply_text("🛡 Target is under Shield Protection!")

        msg = (
            f"🕵️ *Spy Report on {target_alias}:*\n"
            f"🔸 Ore: {target_row['Ore']}\n"
            f"🔸 Energy: {target_row['Energy']}\n"
            f"🔸 Credits: {target_row['Credits']}\n"
            f"🔸 Army: {army}\n"
            f"🔸 Zone: {target_row['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    if text.startswith(",claimzone"):
        if not p["Zone"]:
            return await update.message.reply_text("⚠️ You do not own any zone to claim reward from.")

        zone = p["Zone"]
        zone_owner = zones.get(zone)

        if zone_owner != p["ChatID"]:
            return await update.message.reply_text("⚠️ You lost control of your zone!")

        bonus = 100
        p["Credits"] += bonus
        save_player(p)
        return await update.message.reply_text(f"🏴 Zone reward claimed! +{bonus} credits.")

    if text.startswith(",upgrade"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛠️ Usage: ,upgrade <building>")

        building = parts[1]
        if building == "refinery":
            cost = (p["RefineryLevel"] + 1) * 100
            if p["Credits"] < cost:
                return await update.message.reply_text("💳 Not enough credits to upgrade Refinery.")

            p["Credits"] -= cost
            p["RefineryLevel"] += 1
            save_player(p)
            return await update.message.reply_text(f"🏭 Refinery upgraded to Level {p['RefineryLevel']}!")
        
        if building == "lab":
            cost = (p["LabLevel"] + 1) * 120
            if p["Credits"] < cost:
                return await update.message.reply_text("💳 Not enough credits to upgrade Research Lab.")

            p["Credits"] -= cost
            p["LabLevel"] += 1
            save_player(p)
            return await update.message.reply_text(f"🔬 Research Lab upgraded to Level {p['LabLevel']}!")

        return await update.message.reply_text("⚙️ Unknown building. Upgrade `refinery` or `lab`.")
    if text.startswith(",upgradearmy"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("🛠️ Usage: ,upgradearmy <unit> <count>")

        unit = parts[1]
        try:
            count = int(parts[2])
        except ValueError:
            return await update.message.reply_text("⚙️ Count must be a number.")

        if unit not in p["Army"]:
            return await update.message.reply_text("⚙️ Unknown unit type.")

        upgrade_cost = 30 * count
        if p["Credits"] < upgrade_cost:
            return await update.message.reply_text("💳 Not enough credits.")

        p["Credits"] -= upgrade_cost
        p["Army"][unit] += count
        save_player(p)
        return await update.message.reply_text(f"⚔️ {count} {unit}(s) reinforced successfully!")

    if text.startswith(",events"):
        if world_bank >= 10000:
            await update.message.reply_text("🌎 World Event Active: A rare Hyperion surge boosts mining!")
        else:
            await update.message.reply_text("🌎 No special world events active right now.")

    if text.startswith(",store"):
        store = (
            "🛍️ *SkyHustle Credit Store:*\n"
            "`buy credits100` - Get +100 credits (10 real money)\n"
            "`buy credits250` - Get +250 credits (20 real money)\n"
            "`buy credits1000` - Get +1000 credits (50 real money)\n"
            "\nPurchase credits to boost your empire!"
        )
        return await update.message.reply_text(store, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buycredits"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("💳 Usage: ,buycredits <package>")

        pack = parts[1]
        if pack == "credits100":
            p["Credits"] += 100
            save_player(p)
            return await update.message.reply_text("💳 +100 credits added!")
        if pack == "credits250":
            p["Credits"] += 250
            save_player(p)
            return await update.message.reply_text("💳 +250 credits added!")
        if pack == "credits1000":
            p["Credits"] += 1000
            save_player(p)
            return await update.message.reply_text("💳 +1000 credits added!")

        return await update.message.reply_text("⚠️ Unknown package.")
    if text.startswith(",factioncreate"):
        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            return await update.message.reply_text("🛡️ Usage: ,factioncreate <name>")

        faction_name = parts[1].strip()
        if p["Faction"]:
            return await update.message.reply_text("⚠️ You are already in a faction.")

        if faction_name in factions:
            return await update.message.reply_text("⚠️ Faction already exists.")

        factions[faction_name] = {
            "Founder": p["Name"],
            "Members": [p["Name"]],
            "Points": 0
        }
        p["Faction"] = faction_name
        save_player(p)
        return await update.message.reply_text(f"🛡️ Faction '{faction_name}' created and you joined as Founder!")

    if text.startswith(",factionjoin"):
        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            return await update.message.reply_text("🛡️ Usage: ,factionjoin <faction>")

        faction_name = parts[1].strip()
        if p["Faction"]:
            return await update.message.reply_text("⚠️ You are already in a faction.")

        if faction_name not in factions:
            return await update.message.reply_text("⚠️ Faction does not exist.")

        factions[faction_name]["Members"].append(p["Name"])
        p["Faction"] = faction_name
        save_player(p)
        return await update.message.reply_text(f"🛡️ You joined the faction '{faction_name}'!")

    if text.startswith(",factionleave"):
        if not p["Faction"]:
            return await update.message.reply_text("⚠️ You are not in any faction.")

        faction = p["Faction"]
        factions[faction]["Members"].remove(p["Name"])
        if len(factions[faction]["Members"]) == 0:
            del factions[faction]  # Auto-delete empty faction
        p["Faction"] = None
        save_player(p)
        return await update.message.reply_text(f"🚪 You left the faction '{faction}'.")

    if text.startswith(",factionstatus"):
        if not p["Faction"]:
            return await update.message.reply_text("⚠️ You are not in any faction.")

        faction = factions[p["Faction"]]
        msg = (
            f"🏰 *Faction {p['Faction']}*\n"
            f"Founder: {faction['Founder']}\n"
            f"Members: {', '.join(faction['Members'])}\n"
            f"Points: {faction['Points']}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    if text.startswith(",rankings"):
        faction_leaderboard = sorted(factions.items(), key=lambda x: x[1]["Points"], reverse=True)
        out = "🏆 *Faction Rankings:*\n"
        for i, (name, data) in enumerate(faction_leaderboard, 1):
            out += f"{i}. {name} — {data['Points']} points\n"
        if not faction_leaderboard:
            out += "No factions yet."
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",pvpstats"):
        out = (
            f"🛡️ *{p['Name']} PvP Stats:*\n"
            f"Wins: {p.get('Wins', 0)}\n"
            f"Losses: {p.get('Losses', 0)}\n"
        )
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",donate"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("💳 Usage: ,donate <credits>")

        try:
            amount = int(parts[1])
            if amount <= 0:
                raise ValueError()
        except:
            return await update.message.reply_text("💳 Amount must be a positive number.")

        if p["Credits"] < amount:
            return await update.message.reply_text("💳 Not enough credits.")

        if not p["Faction"]:
            return await update.message.reply_text("⚠️ You are not in a faction.")

        factions[p["Faction"]]["Points"] += amount
        p["Credits"] -= amount
        save_player(p)
        return await update.message.reply_text(f"💳 Donated {amount} credits to your faction!")

    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")

        target_alias = parts[1]
        target_row = find_player_by_name(target_alias)

        if not target_row:
            return await update.message.reply_text("🎯 Target not found!")

        spy_level = p.get("SpyLevel", 0)
        if spy_level < 1:
            return await update.message.reply_text("🛑 You need Spy Technology Level 1 or higher.")

        # Simulate basic spy report
        army = json.loads(target_row["Army"])
        report = (
            f"🕵️ Spy Report on {target_alias}:\n"
            f"Zone: {target_row['Zone'] or 'None'}\n"
            f"Army Units: {army}\n"
            f"Shield Status: {target_row['ShieldUntil'] or 'None'}\n"
        )
        return await update.message.reply_text(report)
    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🔬 Usage: ,research <speed/armor/spy>")

        tech = parts[1].lower()
        if tech not in ["speed", "armor", "spy"]:
            return await update.message.reply_text("🔬 Available research: speed, armor, spy")

        cost = 200 + 50 * p.get(f"{tech.capitalize()}Level", 0)
        if p["Credits"] < cost:
            return await update.message.reply_text(f"💳 Need {cost} credits to research {tech}.")

        p["Credits"] -= cost
        p[f"{tech.capitalize()}Level"] = p.get(f"{tech.capitalize()}Level", 0) + 1
        save_player(p)
        return await update.message.reply_text(f"🔬 {tech.capitalize()} research upgraded to Level {p[f'{tech.capitalize()}Level']}!")

    if text.startswith(",upgrade"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏗 Usage: ,upgrade <refinery/defense/lab>")

        building = parts[1].lower()
        if building not in ["refinery", "defense", "lab"]:
            return await update.message.reply_text("🏗 Available upgrades: refinery, defense, lab")

        level = p.get(f"{building.capitalize()}Level", 0)
        cost = (level + 1) * 150
        if p["Credits"] < cost:
            return await update.message.reply_text(f"💳 Need {cost} credits to upgrade {building}.")

        p["Credits"] -= cost
        p[f"{building.capitalize()}Level"] = level + 1
        save_player(p)
        return await update.message.reply_text(f"🏗 {building.capitalize()} upgraded to Level {level + 1}!")

    if text.startswith(",buildings"):
        out = (
            f"🏗 *{p['Name']} Buildings:*\n"
            f"Refinery: Lv {p.get('RefineryLevel',0)}\n"
            f"Defense: Lv {p.get('DefenseLevel',0)}\n"
            f"Lab: Lv {p.get('LabLevel',0)}"
        )
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)
# --- CONTINUING from previous clean parts ---

# Background Tasks
async def background_tasks():
    while True:
        await check_global_events()
        await asyncio.sleep(30)

# Global Event Logic
async def check_global_events():
    now = datetime.now()
    # Example: Reset shield if expired
    players = players_sheet.get_all_records()
    for p in players:
        if p["ShieldUntil"]:
            shield_time = datetime.strptime(p["ShieldUntil"], "%Y-%m-%d %H:%M:%S")
            if now > shield_time:
                row = p["_row"]
                players_sheet.update_cell(row, 8, "")  # Column H = ShieldUntil
                print(f"🛡️ Shield expired for {p['Name']}")
# --- CONTINUING ---

# Help Command (already integrated previously but beautifying fully now)
async def send_help(update: Update):
    help_text = (
        "🛠 *SkyHustle Commands:*\n\n"
        "🌟 Basic Commands:\n"
        "`,start` - Begin your journey\n"
        "`,name <alias>` - Set your Commander name\n"
        "`,status` - View your current stats\n"
        "`,daily` - Claim daily bonus\n"
        "`,mine ore <count>` - Mine Hyperion ore\n"
        "`,forge <unit> <count>` - Forge units (scout, tank, drone)\n"
        "\n"
        "🛡️ Advanced Actions:\n"
        "`,claim <zone>` - Claim zones\n"
        "`,map` - View Zone Control\n"
        "`,attack <enemy name>` - Attack another Commander\n"
        "`,missions` - View your missions\n"
        "`,use <item>` - Use special items\n"
        "\n"
        "🖤 Black Market:\n"
        "`,unlockbm` - Unlock Black Market access\n"
        "`,blackmarket` - Browse Black Market\n"
        "`,buy <item>` - Purchase Black Market items\n"
        "\n"
        "🎖️ Extras:\n"
        "`,rank` - Check rankings\n"
        "`,profile` - View your detailed Commander profile\n"
        "\n"
        "❓ Type `,help` anytime to see this menu."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
# 📜 Help Command - Reinforced
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 *SkyHustle Core Commands:*\n"
        "`/start` - Begin your legend\n"
        "`/name <alias>` - Set your callsign\n"
        "`/status` - View your empire\n"
        "`/mine ore <count>` - Mine Hyperion ore\n"
        "`/forge <unit> <count>` - Build units\n"
        "`/daily` - Claim your daily rewards\n"
        "`/claim <zone>` - Claim a zone\n"
        "`/map` - View zone map\n"
        "`/missions` - View missions\n"
        "`/blackmarket` - Open premium store\n"
        "`/buy <item>` - Purchase Black Market item\n"
        "`/unlockbm` - Unlock Black Market\n"
        "`/attack <player>` - Attack enemy commander\n"
        "`/rules` - Show game rules\n"
        "`/help` - Show this list\n",
        parse_mode=ParseMode.MARKDOWN
    )

# 📜 Rules Command
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *SkyHustle Universal Laws:*\n"
        "- Respect zones and their owners.\n"
        "- No griefing or abuse.\n"
        "- Play fair, play smart.\n"
        "- Wars are ruthless but honor matters.\n"
        "- Exploits/cheats = permanent ban.\n\n"
        "💬 Questions? Contact the SkyCouncil!",
        parse_mode=ParseMode.MARKDOWN
    )

# App Main Loop
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Connect extra /help and /rules commands
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules_command))

    app.create_task(background_tasks())
    app.run_polling()







        





