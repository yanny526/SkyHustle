# SkyHustle Main Core - PART 1

import os
import json
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from sheet import get_sheet
# Available Skins and Titles

available_skins = ["Default", "Crimson Armor", "Emerald Camo", "Golden Paladin"]
available_titles = ["Rookie", "Veteran", "Warlord", "Conqueror"]
# Fame points system
fame_points = {}  # {ChatID: fame score}
# Fame adjustment
fame_points[p["ChatID"]] = fame_points.get(p["ChatID"], 0) + 10  # Attacker gains 10 fame on win
fame_points[target_row["ChatID"]] = fame_points.get(target_row["ChatID"], 0) + 2  # Defender gains 2 fame for defense attempt



# Connect to Google Sheet
players_sheet = get_sheet().worksheet("SkyHustle")

# Player Helpers
def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            return row
    # Create new player
    new_player = {
        "ChatID": cid,
        "Name": "",
        "Ore": 0,
        "Energy": 100,
        "Credits": 100,
        "Army": json.dumps({"scout": 0, "tank": 0, "drone": 0}),
        "Zone": "",
        "ShieldUntil": "",
        "DailyStreak": 0,
        "LastDaily": "",
        "BlackMarketUnlocked": "FALSE",
        "Items": json.dumps({})
    }
    players_sheet.append_row(list(new_player.values()))
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    players_sheet.update(f"A{p['_row']}:L{p['_row']}", [[
        p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"],
        p["Army"], p["Zone"], p["ShieldUntil"], p["DailyStreak"],
        p["LastDaily"], p["BlackMarketUnlocked"], p["Items"]
    ]])
async def attack_player(attacker, defender, update):
    attacker_power = sum(attacker["Army"].values()) + (attacker.get("RefineryLevel", 0) * 5)
    defender_power = sum(defender["Army"].values()) + (defender.get("RefineryLevel", 0) * 5)

    if attacker_power == 0:
        return await update.message.reply_text("⚠️ You have no units to attack with!")

    if defender_power == 0:
        return await update.message.reply_text("🎯 Enemy has no defenses! Easy win!")

    battle_summary = f"⚔️ *Battle Summary:*\n"
    battle_summary += f"👨‍🚀 {attacker['Name']} Power: {attacker_power}\n"
    battle_summary += f"🛡 {defender['Name']} Power: {defender_power}\n"

    if attacker_power > defender_power:
        reward_credits = 50
        attacker["Credits"] += reward_credits
        attacker["Wins"] += 1
        defender["Losses"] += 1
        outcome = f"🏆 *Victory!* You plundered +{reward_credits} credits!"
    else:
        loss_credits = 20
        attacker["Credits"] = max(0, attacker["Credits"] - loss_credits)
        attacker["Losses"] += 1
        defender["Wins"] += 1
        outcome = f"❌ *Defeat!* You lost {loss_credits} credits."

    battle_summary += f"\n\n{outcome}"

    # Minor troop losses for both
    for unit in attacker["Army"]:
        attacker["Army"][unit] = max(0, attacker["Army"][unit] - 1)
    for unit in defender["Army"]:
        defender["Army"][unit] = max(0, defender["Army"][unit] - 1)

    save_player(attacker)
    save_player(defender)

    return await update.message.reply_text(battle_summary, parse_mode=ParseMode.MARKDOWN)


# Add command inside handle_message
if text.startswith(",attack"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("⚔️ Usage: ,attack <enemy alias>")
    enemy_alias = parts[1]
    target_row = find_player_by_name(enemy_alias)
    if not target_row:
        return await update.message.reply_text("🎯 Target not found!")
    if target_row["ChatID"] == p["ChatID"]:
        return await update.message.reply_text("🤔 You can't attack yourself!")

    await attack_player(p, target_row, update)
    return
    # -- Shield Activation System --

from datetime import datetime, timedelta

# Inside handle_message after other commands
if text.startswith(",shield"):
    if p["Energy"] < 50:
        return await update.message.reply_text("⚡ Not enough energy! Need 50 Energy to activate Shield.")
    
    if p["ShieldUntil"]:
        shield_time = datetime.strptime(p["ShieldUntil"], "%Y-%m-%d %H:%M:%S")
        if shield_time > datetime.now():
            return await update.message.reply_text(f"🛡️ Shield active until {shield_time.strftime('%Y-%m-%d %H:%M:%S')}.")

    # Consume energy and set shield
    p["Energy"] -= 50
    p["ShieldUntil"] = (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
    save_player(p)
    return await update.message.reply_text("🛡️ Shield activated! You are protected for 12 hours.")

def get_faction_bonus(p):
    if p["Faction"] == "Solaris":
        return {"attack": 5, "defense": 0}
    if p["Faction"] == "Eclipse":
        return {"attack": 0, "defense": 5}
    if p["Faction"] == "Voidborn":
        return {"attack": 2, "defense": 2}
    return {"attack": 0, "defense": 0}
 def black_market_price(item_id, level=1):
    # Dynamic pricing model
    base_prices = {
        "infinityscout": 100,
        "reviveall": 500,
        "hazmat": 250
    }
    return base_prices.get(item_id, 100) * level

def upgrade_black_market_item(p, item_id):
    # Upgrade perishable items (example for scouts)
    current = p["Items"].get(item_id+"1", 0)
    if current == 0:
        return False, "❌ You don't own the base version yet."

    upgrade_cost = black_market_price(item_id, 2)
    if p["Credits"] < upgrade_cost:
        return False, "💳 Not enough credits to upgrade."

    p["Credits"] -= upgrade_cost
    p["Items"].pop(item_id+"1")
    p["Items"][item_id+"2"] = 1
    return True, "🛠️ Successfully upgraded to level 2!"
   
def start_new_season():
    # Reset all player win/loss for fresh rankings
    records = players_sheet.get_all_records()
    for row_idx, record in enumerate(records, start=2):
        players_sheet.update(f"N{row_idx}:O{row_idx}", [[0, 0]])  # N: Wins, O: Losses
async def use_item(p, item, update):
    if item == "reviveall":
        # Revive all non-BlackMarket units
        revived = 0
        for unit in p["Army"]:
            p["Army"][unit] += 5  # Revive 5 units each
            revived += 5
        save_player(p)
        return await update.message.reply_text(f"🧬 Revived {revived} units!")
    elif item == "infinityscout1":
        return await update.message.reply_text("🛰 InfinityScout launched! Enemy scan complete (RP only).")
    else:
        return await update.message.reply_text("❓ Unknown or unusable item.")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)
    now = datetime.now()
    today = date.today()

    if text.startswith(",start"):
        intro = (
            "🌌 *Welcome Commander!*\n\n"
            "In the ruins of Hyperion’s shattered worlds, factions rise and fall. "
            "You are the last hope.\n\n"
            "🔹 Set your identity: `,name <yourname>`\n"
            "🔹 View stats: `,status`\n"
            "🔹 Begin mining: `,mine ore 1`\n"
            "🔹 Claim daily rewards: `,daily`\n\n"
            "_Forge your destiny among the stars._ 🚀"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias: return await update.message.reply_text("⚠ Usage: ,name <alias>")
        p["Name"] = alias
        update_player(p)
        return await update.message.reply_text(f"🚩 Callsign registered as *{alias}*", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p["Items"])
        shield = p["ShieldUntil"] if p["ShieldUntil"] else "None"
        msg = (
            f"👤 *{p['Name'] or 'Unregistered Commander'}*\n"
            f"🪨 Ore: `{p['Ore']}` | ⚡ Energy: `{p['Energy']}` | 💳 Credits: `{p['Credits']}`\n"
            f"🛡 Shield: `{shield}` | 📍 Zone: `{p['Zone'] or 'None'}`\n"
            f"🤖 Army: `{army}`\n"
            f"🎒 Items: `{items}`"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",daily"):
    if p["LastDaily"] == str(date.today()):
        return await update.message.reply_text("🎁 Already claimed today.")
    reward = 50 + (p["DailyStreak"] * 5)  # Increase reward over streak
    p["Credits"] += reward
    p["Energy"] = min(100, p["Energy"] + 20)
    p["DailyStreak"] += 1
    p["LastDaily"] = str(date.today())
    save_player(p)
    return await update.message.reply_text(f"🎁 Daily reward: +{reward} credits, +20 energy! (Streak: {p['DailyStreak']} days)")


  if text.startswith(",mine"):
    parts = text.split()
    if len(parts) != 3 or parts[1] != "ore":
        return await update.message.reply_text("⚒️ Usage: ,mine ore <count>")

    try:
        count = int(parts[2])
    except ValueError:
        return await update.message.reply_text("⚠️ Count must be a number.")

    # Enforce cooldown
    now = datetime.now()
    if "LastMine" in p and p["LastMine"]:
        last_mine_time = datetime.strptime(p["LastMine"], "%Y-%m-%d %H:%M:%S")
        if (now - last_mine_time).seconds < 60:
            seconds_left = 60 - (now - last_mine_time).seconds
            return await update.message.reply_text(f"⏳ Mining cooldown: {seconds_left} seconds left.")

    if p["Energy"] < count * 5:
        return await update.message.reply_text("⚡ Not enough energy to mine that much!")

    ore_boost = 1.0
    if "hazmat" in json.loads(p["Items"]):
        ore_boost = 1.2  # Hazmat players mine faster (example: extra ore in radiation zones)

    ore_earned = int(20 * count * ore_boost)
    credit_earned = int(10 * count)

    p["Ore"] += ore_earned
    p["Credits"] += credit_earned
    p["Energy"] -= count * 5
    p["LastMine"] = now.strftime("%Y-%m-%d %H:%M:%S")
    save_player(p)

    await update.message.reply_text(
        f"⛏️ You mined {ore_earned} ore and earned {credit_earned} credits!\n"
        f"Energy left: {p['Energy']}"
    )
    return


    if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚙️ Usage: ,forge <unit> <count>")
        unit = parts[1]
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        army = json.loads(p["Army"])
        cost_ore = {"scout": 10, "tank": 20, "drone": 30}
        cost_credits = {"scout": 5, "tank": 10, "drone": 15}
        if unit not in army:
            return await update.message.reply_text("⚠ Invalid unit type.")
        total_ore = cost_ore[unit] * count
        total_credits = cost_credits[unit] * count
        if p["Ore"] < total_ore or p["Credits"] < total_credits:
            return await update.message.reply_text("⚠ Insufficient resources.")
        p["Ore"] -= total_ore
        p["Credits"] -= total_credits
        army[unit] += count
        p["Army"] = json.dumps(army)
        update_player(p)
        return await update.message.reply_text(f"⚙️ Forged *{count} {unit}(s)* into your mighty army.", parse_mode=ParseMode.MARKDOWN)

        ### BEGIN PART 2: Black Market, PvP, Use Items

    if text.startswith(",blackmarket"):
        if not p.get("BlackMarketUnlocked", False):
            return await update.message.reply_text("🔒 You must unlock access! Use ,unlockbm first.")
        bm_items = "\n".join([f"- {k}: {v['desc']}" for k, v in blackmarket.items()])
        return await update.message.reply_text(f"🛒 *Black Market Items:*\n{bm_items}", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",unlockbm"):
        if p.get("BlackMarketUnlocked", False):
            return await update.message.reply_text("✅ Already unlocked.")
        if p["Credits"] < 500:
            return await update.message.reply_text("❌ Need 500 credits to unlock Black Market.")
        p["Credits"] -= 500
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("🎉 Black Market access unlocked!")

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buy <item>")
        item = parts[1]
        if item not in blackmarket:
            return await update.message.reply_text("❌ Item does not exist.")
        cost = blackmarket[item]["cost"]
        if p["Credits"] < cost:
            return await update.message.reply_text("❌ Not enough credits.")
        items_owned = json.loads(p["Items"])
        items_owned[item] = items_owned.get(item, 0) + 1
        p["Credits"] -= cost
        p["Items"] = json.dumps(items_owned)
        save_player(p)
        return await update.message.reply_text(f"✅ Bought {item}!")
        # -- Faction / Clan System --

async def create_faction(name, leader_chatid):
    sheet = players_sheet
    factions = sheet.worksheet("Factions").get_all_records()
    for faction in factions:
        if faction["Name"].lower() == name.lower():
            return False, "⚠️ Faction name already exists."
    
    sheet.worksheet("Factions").append_row([name, leader_chatid, 1])
    return True, f"✅ Faction '{name}' created successfully!"

async def join_faction(p, faction_name):
    sheet = players_sheet
    factions = sheet.worksheet("Factions").get_all_records()
    for faction in factions:
        if faction["Name"].lower() == faction_name.lower():
            if p["Faction"]:
                return False, "⚠️ You're already in a faction."
            p["Faction"] = faction["Name"]
            save_player(p)
            return True, f"🤝 Joined faction {faction_name}!"
    return False, "❌ Faction not found."

if text.startswith(",createfaction"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("Usage: ,createfaction <name>")
    success, msg = await create_faction(parts[1], cid)
    return await update.message.reply_text(msg)

if text.startswith(",joinfaction"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("Usage: ,joinfaction <name>")
    success, msg = await join_faction(p, parts[1])
    return await update.message.reply_text(msg)
    # -- Faction Communication System --

async def faction_chat(p, message, update):
    if not p["Faction"]:
        return await update.message.reply_text("⚠️ You're not in any faction.")
    
    faction_members = factions.get(p["Faction"], [])
    if not faction_members:
        return await update.message.reply_text("⚠️ Your faction is empty.")
    
    for member_cid in faction_members:
        if member_cid != p["ChatID"]:  # Don't send to self
            try:
                await ctx.bot.send_message(chat_id=member_cid, text=f"[Faction] {p['Name']}: {message}")
            except:
                pass  # Fail silently if user blocked bot or unavailable

async def list_factions(update):
    if not factions:
        return await update.message.reply_text("❌ No factions exist yet.")
    
    output = "🏴‍☠️ *Current Factions:*\n"
    for fname, members in factions.items():
        output += f"- {fname}: {len(members)} members\n"
    await update.message.reply_text(output, parse_mode=ParseMode.MARKDOWN)

# -- Commands --

if text.startswith(",fchat"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("💬 Usage: ,fchat <message>")
    await faction_chat(p, parts[1], update)
    return

if text.startswith(",factions"):
    await list_factions(update)
    return

# -- PvE: Pirate Raids --

import random

async def pirate_raid(p, update):
    enemy_power = random.randint(5, 20)
    player_power = sum(p["Army"].values()) + p["RefineryLevel"] * 5

    if player_power == 0:
        return await update.message.reply_text("⚠️ You have no army to defend against pirates!")

    if player_power >= enemy_power:
        reward = random.randint(100, 250)
        p["Credits"] += reward
        save_player(p)
        return await update.message.reply_text(f"🏴‍☠️ You defeated the pirate raid! +{reward} credits!")
    else:
        loss = random.randint(10, 50)
        p["Credits"] = max(0, p["Credits"] - loss)
        save_player(p)
        return await update.message.reply_text(f"💀 Pirates overwhelmed your forces... Lost {loss} credits.")

if text.startswith(",pve") or text.startswith(",raid"):
    return await pirate_raid(p, update)

if text.startswith(",rankings"):
    records = players_sheet.get_all_records()
    ranked = sorted(records, key=lambda x: (x.get("Wins", 0) - x.get("Losses", 0)), reverse=True)
    
    ranking_msg = "🏆 *SkyHustle Global Rankings:*\n\n"
    for idx, player in enumerate(ranked[:10], start=1):
        name = player.get("Name", "Unknown")
        wins = player.get("Wins", 0)
        losses = player.get("Losses", 0)
        ranking_msg += f"{idx}. {name} — {wins}W/{losses}L\n"

    return await update.message.reply_text(ranking_msg, parse_mode=ParseMode.MARKDOWN)
if text.startswith(",achievements"):
    # Achievements based on total Wins
    wins = p.get("Wins", 0)
    if wins >= 100:
        badge = "🌟 *Galactic Hero* (100+ Wins)"
    elif wins >= 50:
        badge = "🔥 *Battle Commander* (50+ Wins)"
    elif wins >= 20:
        badge = "⚔️ *Skirmisher* (20+ Wins)"
    elif wins >= 10:
        badge = "🛡 *Survivor* (10+ Wins)"
    else:
        badge = "🧱 *Recruit* (<10 Wins)"

    return await update.message.reply_text(
        f"🏅 Your Achievement Badge:\n{badge}",
        parse_mode=ParseMode.MARKDOWN
    )
if text.startswith(",fame"):
    fame = fame_points.get(cid, 0)
    return await update.message.reply_text(f"🌟 Fame Points: {fame}")

if text.startswith(",fameboard"):
    if not fame_points:
        return await update.message.reply_text("🌌 No fame points recorded yet!")
    sorted_fame = sorted(fame_points.items(), key=lambda x: x[1], reverse=True)
    top = "\n".join(
        f"{i+1}. {players.get(uid, {}).get('Name', 'Unknown')} - {score} Fame"
        for i, (uid, score) in enumerate(sorted_fame[:10])
    )
    return await update.message.reply_text(f"🌟 *Top Fame Leaders:*\n{top}", parse_mode=ParseMode.MARKDOWN)

if text.startswith(",prestige"):
    if p.get("Wins", 0) < 100:
        return await update.message.reply_text("🔒 You need 100+ Wins to Prestige!")

    # Reset major stats but give Prestige Title
    p["Ore"] = 0
    p["Energy"] = 100
    p["Credits"] = 500
    p["Army"] = {"scout": 0, "drone": 0, "tank": 0}
    p["Zone"] = ""
    p["ShieldUntil"] = ""
    p["Wins"] = 0
    p["Losses"] = 0
    p["Prestige"] = p.get("Prestige", 0) + 1
    save_player(p)

    return await update.message.reply_text(
        f"🌌 Prestige complete! You are now Prestige Level {p['Prestige']}!",
        parse_mode=ParseMode.MARKDOWN
    )
if text.startswith(",skins"):
    skins_list = "\n".join(f"- {skin}" for skin in available_skins)
    return await update.message.reply_text(
        f"🎨 *Available Skins:*\n{skins_list}\n\nUse `,equipskin <skin>` to equip!",
        parse_mode=ParseMode.MARKDOWN
    )

if text.startswith(",equipskin"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("🎨 Usage: ,equipskin <skin>")
    chosen = parts[1]
    if chosen not in available_skins:
        return await update.message.reply_text("❌ Invalid skin name!")
    p["Skin"] = chosen
    save_player(p)
    return await update.message.reply_text(f"✅ Skin equipped: {chosen}!")

if text.startswith(",titles"):
    titles_list = "\n".join(f"- {title}" for title in available_titles)
    return await update.message.reply_text(
        f"🎖 *Available Titles:*\n{titles_list}\n\nUse `,equiptitle <title>` to equip!",
        parse_mode=ParseMode.MARKDOWN
    )

if text.startswith(",equiptitle"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("🎖 Usage: ,equiptitle <title>")
    chosen = parts[1]
    if chosen not in available_titles:
        return await update.message.reply_text("❌ Invalid title name!")
    p["Title"] = chosen
    save_player(p)
    return await update.message.reply_text(f"✅ Title equipped: {chosen}!")

   if text.startswith(",use"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🧪 Usage: ,use <item>")
    item_id = parts[1]
    await use_item(p, item_id, update)
    return

        item = parts[1]
        items_owned = json.loads(p["Items"])
        if items_owned.get(item, 0) <= 0:
            return await update.message.reply_text("❌ You don't own this item.")
        if item in perishables:
            items_owned[item] -= 1
            if items_owned[item] == 0:
                del items_owned[item]
            p["Items"] = json.dumps(items_owned)
            save_player(p)
        return await update.message.reply_text(f"✅ Used {item}!")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,attack <playername>")
        target_name = parts[1]
        target_id, target = find_by_name(target_name)
        if not target:
            return await update.message.reply_text("❌ Target not found.")
        if p["Energy"] < 20:
            return await update.message.reply_text("⚡ Not enough energy.")
        p["Energy"] -= 20
        if p["Army"]["scout"] > target["Army"]["scout"]:
            return await update.message.reply_text(f"⚔️ Victory over {target_name}!")
        else:
            return await update.message.reply_text(f"💥 Defeated by {target_name}...")

    if text.startswith(",help"):
        return await update.message.reply_text(
            "🛠 *SkyHustle Commands:*\n"
            "`,start` - Begin your journey\n"
            "`,name <alias>` - Set your callsign\n"
            "`,status` - View your stats\n"
            "`,daily` - Claim daily reward\n"
            "`,mine ore <count>` - Mine Hyperion ore\n"
            "`,forge <unit> <count>` - Build army units\n"
            "`,blackmarket` - View Black Market\n"
            "`,unlockbm` - Unlock Black Market access\n"
            "`,buy <item>` - Purchase Black Market item\n"
            "`,use <item>` - Use an owned item\n"
            "`,attack <playername>` - Attack another player\n"
            "`,help` - Show this help list",
            parse_mode=ParseMode.MARKDOWN
        )
        # ---- PART 50: Spy System (Scouting other players) ----

async def spy_on_player(spy, target, update):
    if spy["Energy"] < 20:
        return await update.message.reply_text("🔍 Not enough energy to launch a scout mission (Need 20 Energy).")
    
    spy["Energy"] -= 20
    save_player(spy)

    # Normal spy only sees basic info unless Infinity Scout is used
    basic_report = (
        f"🛰️ Scout Report on {target['Name']}:\n"
        f"- Ore: {target['Ore']}\n"
        f"- Credits: {target['Credits']}\n"
        f"- Army: {target['Army']}\n"
    )

    if "infinityscout1" in spy["Items"] and spy["Items"]["infinityscout1"] > 0:
        # Reveal hidden info if using Infinity Scout
        spy["Items"]["infinityscout1"] -= 1
        if spy["Items"]["infinityscout1"] == 0:
            del spy["Items"]["infinityscout1"]
        save_player(spy)

        detailed = (
            f"- Zone: {target['Zone']}\n"
            f"- Shield: {target['ShieldUntil'] or 'None'}\n"
            f"- Black Market Items: {json.loads(target['Items'])}"
        )
        return await update.message.reply_text(basic_report + "\n" + detailed)
    
    return await update.message.reply_text(basic_report)

# Inside handle_message

if text.startswith(",spy"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🛰️ Usage: ,spy <enemy alias>")
    target_alias = parts[1]
    target_row = find_player_by_name(target_alias)
    if not target_row:
        return await update.message.reply_text("🎯 Target not found.")
    if target_row["ChatID"] == p["ChatID"]:
        return await update.message.reply_text("🤔 You can't scout yourself.")

    await spy_on_player(p, target_row, update)
    return

        # ---- PART 47: Spy Mechanics ----

async def spy_on_player(spy, target, update):
    if "infinityscout1" in json.loads(spy["Items"]):
        spy_data = (
            f"🕵️ Spy Report on {target['Name']}:\n"
            f"- Ore: {target['Ore']}\n"
            f"- Energy: {target['Energy']}\n"
            f"- Credits: {target['Credits']}\n"
            f"- Army: {target['Army']}\n"
            f"- Zone: {target['Zone'] or 'None'}"
        )
        spy_items = json.loads(spy["Items"])
        spy_items["infinityscout1"] -= 1
        if spy_items["infinityscout1"] == 0:
            del spy_items["infinityscout1"]
        spy["Items"] = json.dumps(spy_items)
        save_player(spy)
        return await update.message.reply_text(spy_data)
    else:
        return await update.message.reply_text("🔍 You need an Infinity Scout to perform espionage.")

# Inside handle_message

if text.startswith(",spy"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")
    enemy_alias = parts[1]
    target_row = find_player_by_name(enemy_alias)
    if not target_row:
        return await update.message.reply_text("🎯 Target not found!")
    if target_row["ChatID"] == p["ChatID"]:
        return await update.message.reply_text("🤔 You cannot spy on yourself!")

    await spy_on_player(p, target_row, update)
    return
# ---- PART 48: Radiation Zone Access ----

async def enter_radiation_zone(player, update):
    if "hazmat" not in json.loads(player["Items"]):
        return await update.message.reply_text("☢️ You need a Hazmat Unit to access Radiation Zones!")
    
    zones_with_radiation = ["Gamma", "Delta"]  # Define which zones are radiation zones
    available_zones = [z for z in zones_with_radiation if players_sheet.find(z) is None]

    if not available_zones:
        return await update.message.reply_text("⚠️ No Radiation Zones are currently unclaimed!")

    # Claim first available radiation zone
    player["Zone"] = available_zones[0]
    save_player(player)
    return await update.message.reply_text(f"☢️ You have bravely entered Radiation Zone: {available_zones[0]}!")


# Inside handle_message

if text.startswith(",hazzone"):
    await enter_radiation_zone(p, update)
    return
# ---- PART 49: Shield System ----

async def activate_shield(player, update):
    if player["ShieldUntil"]:
        current_shield = datetime.strptime(player["ShieldUntil"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < current_shield:
            return await update.message.reply_text(f"🛡️ Shield active until {current_shield.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Apply 12-hour shield
    new_shield_time = datetime.now() + timedelta(hours=12)
    player["ShieldUntil"] = new_shield_time.strftime("%Y-%m-%d %H:%M:%S")
    save_player(player)
    return await update.message.reply_text(f"🛡️ Shield activated! Protects until {new_shield_time.strftime('%Y-%m-%d %H:%M:%S')}.")

# Inside handle_message

if text.startswith(",shield"):
    await activate_shield(p, update)
    return

if text.startswith(",blackmarket"):
    if not p.get("BlackMarketUnlocked"):
        return await update.message.reply_text("🔒 Black Market locked. Unlock it first.")
    shop = (
        "🖤 *Black Market Deals:*\n"
        "`buy infinityscout1` - 100 credits\n"
        "`buy reviveall` - 500 credits\n"
        "`buy hazmat` - 250 credits\n"
        "\nUse `,buy <item>` to purchase."
    )
    return await update.message.reply_text(shop, parse_mode=ParseMode.MARKDOWN)

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
    p["Items"].setdefault(item, 0)
    p["Items"][item] += 1
    save_player(p)
    return await update.message.reply_text(f"🛒 Purchased {item}!")

if text.startswith(",unlockbm"):
    # Unlock Black Market access (costs real money in full version!)
    if p.get("BlackMarketUnlocked"):
        return await update.message.reply_text("✅ Black Market already unlocked.")
    # For now, simulate unlocking with credits (cost: 1000)
    if p["Credits"] < 1000:
        return await update.message.reply_text("💳 Need 1000 credits to unlock.")
    p["Credits"] -= 1000
    p["BlackMarketUnlocked"] = True
    save_player(p)
    return await update.message.reply_text("🖤 Black Market access unlocked!")
if text.startswith(",missions"):
    daily_missions = (
        "🎯 *Daily Missions:*\n"
        "• Mine 100 ore → Reward: 50 credits\n"
        "• Forge 5 scouts → Reward: 50 credits\n"
        "• Attack any enemy → Reward: 100 credits\n\n"
        "Complete all to get a bonus!"
    )
    weekly_missions = (
        "🌟 *Weekly Missions:*\n"
        "• Win 5 battles → Reward: 300 credits\n"
        "• Upgrade refinery → Reward: 200 credits\n"
        "• Capture a zone → Reward: 400 credits"
    )
    await update.message.reply_text(daily_missions + "\n\n" + weekly_missions, parse_mode=ParseMode.MARKDOWN)
    return
if text.startswith(",rank"):
    players = players_sheet.get_all_records()
    player_list = sorted(players, key=lambda x: int(x.get("Wins", 0)) - int(x.get("Losses", 0)), reverse=True)

    rank_position = 1
    for pl in player_list:
        if str(pl["ChatID"]) == str(cid):
            break
        rank_position += 1

    await update.message.reply_text(f"🏅 Your rank: {rank_position} / {len(player_list)} players.")
    return

if text.startswith(",leaderboard"):
    players = players_sheet.get_all_records()
    player_list = sorted(players, key=lambda x: int(x.get("Wins", 0)) - int(x.get("Losses", 0)), reverse=True)

    board = "🏆 *Top 5 Commanders:*\n"
    for i, pl in enumerate(player_list[:5], start=1):
        board += f"{i}. {pl['Name'] or 'Unknown'} (Wins: {pl.get('Wins',0)}, Losses: {pl.get('Losses',0)})\n"

    await update.message.reply_text(board, parse_mode=ParseMode.MARKDOWN)
    return

    await update.message.reply_text("❓ Unknown command. Type ,help for available actions.")
    ### BEGIN PART 3: Buildings, Research, Zones

    if text.startswith(",build"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,build <refinery/lab>")
        building = parts[1]
        if building not in ["refinery", "lab"]:
            return await update.message.reply_text("❌ Invalid building. Choose refinery or lab.")
        cost = 100 if building == "refinery" else 200
        if p["Credits"] < cost:
            return await update.message.reply_text(f"❌ Need {cost} credits to build.")
        p["Credits"] -= cost
        if building == "refinery":
            p["RefineryLevel"] = p.get("RefineryLevel", 0) + 1
        else:
            p["LabLevel"] = p.get("LabLevel", 0) + 1
        save_player(p)
        return await update.message.reply_text(f"🏗 Built {building}! It's now level {p.get(building.capitalize()+'Level',1)}.")

    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,research <speed/armor>")
        tech = parts[1]
        if tech not in ["speed", "armor"]:
            return await update.message.reply_text("❌ Invalid tech. Choose speed or armor.")
        cost = 150
        if p["Credits"] < cost:
            return await update.message.reply_text("❌ Need 150 credits to research.")
        p["Credits"] -= cost
        researches = json.loads(p["Research"])
        researches[tech] = researches.get(tech, 0) + 1
        p["Research"] = json.dumps(researches)
        save_player(p)
        return await update.message.reply_text(f"🧪 Researched {tech}! Level {researches[tech]}.")

    if text.startswith(",map"):
        control_map = "🗺 Zone Map:\n"
        zones = {
            "Alpha": None,
            "Beta": None,
            "Gamma": None,
            "Delta": None,
            "Epsilon": None
        }
        for z, owner in zones.items():
            control_map += f"{z}: {'Unclaimed' if not owner else owner}\n"
        return await update.message.reply_text(control_map)

    # -- Enhanced Zone Claiming System --

if text.startswith(",claim"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🗺️ Usage: ,claim <zone>")

    zone = parts[1]
    if zone not in zones:
        return await update.message.reply_text("⚠️ Invalid zone!")

    if zones[zone]:
        return await update.message.reply_text("⚠️ Zone already controlled!")

    # Cannot claim while shielded
    if p["ShieldUntil"]:
        shield_time = datetime.strptime(p["ShieldUntil"], "%Y-%m-%d %H:%M:%S")
        if shield_time > datetime.now():
            return await update.message.reply_text("🛡️ You can't claim zones while shielded!")

    if p["Credits"] < 500:
        return await update.message.reply_text("💳 Need 500 credits to claim a zone!")

    p["Credits"] -= 500
    p["Zone"] = zone
    zones[zone] = p["ChatID"]
    save_player(p)
    return await update.message.reply_text(f"🏰 You have claimed control over zone: {zone}!")

# -- Zone Control --

zones = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}

async def claim_zone(p, zone_name, update):
    if p["Credits"] < 200:
        return await update.message.reply_text("💳 Need 200 credits to claim a zone.")
    if zones.get(zone_name) and zones[zone_name] != p["ChatID"]:
        return await update.message.reply_text("❌ Zone already occupied.")
    zones[zone_name] = p["ChatID"]
    p["Zone"] = zone_name
    p["Credits"] -= 200
    save_player(p)
    await update.message.reply_text(f"🌍 You now control {zone_name}!")

async def show_map(update):
    out = "🗺️ *Zone Map:*\n"
    for z, cid in zones.items():
        owner = "None"
        if cid:
            owner_row = find_player_by_chatid(cid)
            if owner_row:
                owner = owner_row["Name"]
        out += f"🔹 {z}: {owner}\n"
    await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

# -- Commands --

if text.startswith(",map"):
    return await show_map(update)

if text.startswith(",claim"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("⚠️ Usage: ,claim <zone>")
    zone = parts[1]
    if zone not in zones:
        return await update.message.reply_text("❌ Zone doesn't exist.")
    await claim_zone(p, zone, update)
    return

    ### END PART 3
    ### BEGIN PART 4: Missions and PvE Battles

    if text.startswith(",missions"):
        mission_list = (
            "🎯 *Available Missions:*\n"
            "▫️ ,mission mine5 — Mine 5 ores (Reward: 30 Credits)\n"
            "▫️ ,mission forge3 — Forge 3 units (Reward: 40 Credits)\n"
            "▫️ ,mission claimzone — Claim a zone (Reward: 100 Credits)\n"
        )
        return await update.message.reply_text(mission_list, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",mission"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,mission <task>")
        task = parts[1]
        completed = False

        if task == "mine5":
            if p.get("Ore", 0) >= 100:  # Assume 20 ore per mine
                p["Credits"] += 30
                completed = True
        elif task == "forge3":
            army = json.loads(p["Army"])
            total_units = sum(army.values())
            if total_units >= 3:
                p["Credits"] += 40
                completed = True
        elif task == "claimzone":
            if p.get("Zone"):
                p["Credits"] += 100
                completed = True

        if completed:
            save_player(p)
            return await update.message.reply_text(f"✅ Mission {task} complete! Reward granted.")
        else:
            return await update.message.reply_text("❌ Mission not yet complete. Keep pushing, Commander!")

    if text.startswith(",pve"):
        import random
        enemy_strength = random.randint(30, 70)
        my_power = sum(json.loads(p["Army"]).values()) * 10
        if my_power >= enemy_strength:
            reward = 50
            p["Credits"] += reward
            save_player(p)
            return await update.message.reply_text(f"⚔️ You defeated the enemy! +{reward} credits earned!")
        else:
            penalty = 20
            p["Credits"] = max(0, p["Credits"] - penalty)
            save_player(p)
            return await update.message.reply_text(f"☠️ You were overwhelmed! Lost {penalty} credits.")

    ### END PART 4
    ### BEGIN PART 5: Black Market Unlock + Item Usage

    if text.startswith(",unlockblackmarket"):
        if p.get("BlackMarketUnlocked") == "TRUE":
            return await update.message.reply_text("🛒 Black Market already unlocked!")
        if p["Credits"] < 500:
            return await update.message.reply_text("❌ You need 500 credits to unlock the Black Market.")
        p["Credits"] -= 500
        p["BlackMarketUnlocked"] = "TRUE"
        save_player(p)
        return await update.message.reply_text("✅ Black Market unlocked! Use ,blackmarket to browse.")

    if text.startswith(",blackmarket"):
        if p.get("BlackMarketUnlocked") != "TRUE":
            return await update.message.reply_text("❌ Unlock the Black Market first with ,unlockblackmarket.")
        catalog = (
            "🛒 *Black Market Stock:*\n"
            "▫️ ,buy infinityscout1 — 1-use super scout (Cost: 200 credits)\n"
            "▫️ ,buy reviveall — Revive all regular units and buildings (Cost: 500 credits)\n"
            "▫️ ,buy hazmat — Access Radiation Zones (Cost: 300 credits)\n"
        )
        return await update.message.reply_text(catalog, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buy"):
        if p.get("BlackMarketUnlocked") != "TRUE":
            return await update.message.reply_text("❌ Unlock Black Market first.")
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,buy <itemname>")
        item = parts[1]
        cost_table = {
            "infinityscout1": 200,
            "reviveall": 500,
            "hazmat": 300
        }
        if item not in cost_table:
            return await update.message.reply_text("❌ Item not found.")
        if p["Credits"] < cost_table[item]:
            return await update.message.reply_text("❌ Not enough credits.")
        
        p["Credits"] -= cost_table[item]
        inventory = json.loads(p.get("Items", "{}"))
        inventory[item] = inventory.get(item, 0) + 1
        p["Items"] = json.dumps(inventory)
        save_player(p)
        return await update.message.reply_text(f"✅ Purchased {item}.")

    if text.startswith(",useitem"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,useitem <itemname>")
        item = parts[1]
        inventory = json.loads(p.get("Items", "{}"))
        if inventory.get(item, 0) <= 0:
            return await update.message.reply_text("❌ You don't have that item.")
        if item == "reviveall":
            p["Army"] = json.dumps({"scout": 10, "tank": 5, "drone": 7})
            await update.message.reply_text("🛡 All regular units and buildings revived!")
        if item == "infinityscout1":
            await update.message.reply_text("👁 Scout activated. (Nothing visual yet — future expansion!)")
        if item == "hazmat":
            await update.message.reply_text("☢ You can now explore Radiation Zones!")
        # Remove item if perishable
        inventory[item] -= 1
        if inventory[item] <= 0:
            del inventory[item]
        p["Items"] = json.dumps(inventory)
        save_player(p)

    ### END PART 5
    ### BEGIN PART 6: Zone Control + Radiation Zone Access

    zones_controlled = {z: None for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "RadiationZone1", "RadiationZone2"]}

    if text.startswith(",map"):
        output = "🗺 *Zone Control Map:*\n"
        for zone, owner_id in zones_controlled.items():
            if owner_id:
                owner_name = get_player(owner_id)["Name"]
            else:
                owner_name = "Unclaimed"
            output += f"▫️ {zone}: {owner_name}\n"
        return await update.message.reply_text(output, parse_mode=ParseMode.MARKDOWN)
if text.startswith(",claimzone"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🗺 Usage: ,claimzone <zone>")
    zone = parts[1].capitalize()

    if zone not in zones:
        return await update.message.reply_text("🚫 Zone not found.")
# -- Factions System --

factions = {}

async def create_faction(p, faction_name, update):
    if p["Faction"]:
        return await update.message.reply_text("⚠️ You're already in a faction!")
    if faction_name in factions:
        return await update.message.reply_text("⚠️ Faction name already exists.")
    if p["Credits"] < 500:
        return await update.message.reply_text("💳 Need 500 credits to create a faction.")

    p["Faction"] = faction_name
    factions[faction_name] = [p["ChatID"]]
    p["Credits"] -= 500
    save_player(p)
    await update.message.reply_text(f"🏴‍☠️ Faction '{faction_name}' created successfully!")

async def join_faction(p, faction_name, update):
    if p["Faction"]:
        return await update.message.reply_text("⚠️ You're already in a faction!")
    if faction_name not in factions:
        return await update.message.reply_text("❌ Faction does not exist.")
    
    factions[faction_name].append(p["ChatID"])
    p["Faction"] = faction_name
    save_player(p)
    await update.message.reply_text(f"🤝 Joined faction '{faction_name}'!")

# -- Commands --

if text.startswith(",createfaction"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("⚠️ Usage: ,createfaction <name>")
    await create_faction(p, parts[1], update)
    return

if text.startswith(",joinfaction"):
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return await update.message.reply_text("⚠️ Usage: ,joinfaction <name>")
    await join_faction(p, parts[1], update)
    return

    # Check ownership
    current_owner = zones.get(zone)
    if current_owner and current_owner != p["ChatID"]:
        return await update.message.reply_text("🛡 Zone already occupied!")

    if p["Credits"] < 500:
        return await update.message.reply_text("💳 Need 500 credits to claim.")

    p["Credits"] -= 500
    p["Zone"] = zone
    zones[zone] = p["ChatID"]

    save_player(p)
    return await update.message.reply_text(f"✅ You now control {zone} zone!")

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,claim <zone>")
        zone = parts[1]
        if zone not in zones_controlled:
            return await update.message.reply_text("❌ Invalid zone.")
        if zones_controlled[zone]:
            return await update.message.reply_text("❌ Zone already controlled.")
        if p["Credits"] < 300:
            return await update.message.reply_text("❌ You need 300 credits to claim a zone.")
        if zone.startswith("Radiation") and json.loads(p.get("Items", "{}")).get("hazmat", 0) <= 0:
            return await update.message.reply_text("☢️ You need Hazmat access to enter Radiation Zones.")
        
        p["Credits"] -= 300
        p["Zone"] = zone
        zones_controlled[zone] = cid
        save_player(p)
        return await update.message.reply_text(f"✅ You now control {zone}!")

    if text.startswith(",zoneinfo"):
        if not p.get("Zone"):
            return await update.message.reply_text("❌ You are not controlling any zone.")
        return await update.message.reply_text(f"📍 You currently control {p['Zone']}.")

    ### END PART 6
    ### BEGIN PART 7: Factions & PvP Combat

    player_factions = {}

    if text.startswith(",faction join"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("Usage: ,faction join <factionname>")
        faction = parts[2]
        player_factions[cid] = faction
        await update.message.reply_text(f"🛡 You have joined *{faction}*!", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",faction"):
        faction = player_factions.get(cid)
        if faction:
            await update.message.reply_text(f"🛡 You belong to *{faction}*!", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("⚠️ You are not part of any faction. Use ,faction join <name>")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,attack <enemy name>")
        enemy_name = parts[1]
        found = None
        for pid, pdata in players.items():
            if pdata["Name"].lower() == enemy_name.lower():
                found = pid
                break
        if not found:
            return await update.message.reply_text("❌ Enemy not found.")
        
        attacker = p
        defender = get_player(found)

        attacker_army = sum(json.loads(attacker["Army"]).values())
        defender_army = sum(json.loads(defender["Army"]).values())

        if attacker_army == 0:
            return await update.message.reply_text("⚠️ You have no army units to attack.")
        if defender_army == 0:
            return await update.message.reply_text("⚠️ Enemy has no army units.")

        if attacker_army > defender_army:
            attacker["Credits"] += 100
            defender["Credits"] -= 50
            result = f"🔥 Victory! You gained +100 credits. Enemy lost 50 credits."
        elif attacker_army < defender_army:
            attacker["Credits"] -= 50
            defender["Credits"] += 100
            result = f"💀 Defeat! You lost 50 credits. Enemy gained +100 credits."
        else:
            result = "🤝 It's a draw! No rewards."

        save_player(attacker)
        save_player(defender)
        await update.message.reply_text(result)

    ### END PART 7

# -- PvE Mission System --

async def start_pve_mission(p, mission_name, update):
    if p["Energy"] < 50:
        return await update.message.reply_text("⚡ Need at least 50 energy to start a mission.")
    
    if mission_name == "pirateraid":
        p["Energy"] -= 50
        loot = 100
        p["Credits"] += loot
        save_player(p)
        return await update.message.reply_text(f"🏴‍☠️ Raid successful! You stole {loot} credits!")
    
    if mission_name == "radiationrun":
        if not p["Items"].get("hazmat", 0):
            return await update.message.reply_text("☢️ You need a Hazmat Drone to attempt this mission.")
        p["Energy"] -= 50
        ore_gain = 200
        p["Ore"] += ore_gain
        save_player(p)
        return await update.message.reply_text(f"☢️ Radiation run complete! Gained {ore_gain} ore.")

    return await update.message.reply_text("❓ Unknown mission.")

# -- Commands --

if text.startswith(",pve"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🛰️ Usage: ,pve <pirateraid/radiationrun>")
    await start_pve_mission(p, parts[1], update)
    return

    ### BEGIN PART 8: PvE Pirate Raids

    from random import randint

    if text.startswith(",pirateraids"):
        enemy_force = randint(5, 25)
        p_army_total = sum(json.loads(p["Army"]).values())

        if p_army_total == 0:
            return await update.message.reply_text("⚓ You have no army units to defend against pirates!")

        if p_army_total >= enemy_force:
            reward = randint(50, 150)
            p["Credits"] += reward
            result = f"🏴‍☠️ You defeated the pirate raid! +{reward} credits!"
        else:
            loss = randint(10, 30)
            p["Credits"] = max(p["Credits"] - loss, 0)
            result = f"💥 Pirates overwhelmed you! Lost {loss} credits."

        save_player(p)
        await update.message.reply_text(result)

    ### END PART 8
# -- Mission System --

def generate_missions():
    return {
        "mine_ore": {"target": 5, "progress": 0, "reward": 50},
        "forge_units": {"target": 3, "progress": 0, "reward": 30},
        "win_battles": {"target": 1, "progress": 0, "reward": 100}
    }

def get_player_missions(p):
    if not p.get("Missions"):
        p["Missions"] = generate_missions()
    return p["Missions"]

def update_mission(p, mission_key, amount=1):
    missions = get_player_missions(p)
    if mission_key in missions:
        missions[mission_key]["progress"] += amount
        if missions[mission_key]["progress"] > missions[mission_key]["target"]:
            missions[mission_key]["progress"] = missions[mission_key]["target"]
    p["Missions"] = missions
    save_player(p)

async def claim_mission(p, key, update):
    missions = get_player_missions(p)
    if missions[key]["progress"] >= missions[key]["target"]:
        reward = missions[key]["reward"]
        p["Credits"] += reward
        missions[key]["progress"] = 0  # Reset progress
        p["Missions"] = missions
        save_player(p)
        await update.message.reply_text(f"🎉 Claimed {reward} credits for {key} mission!")
    else:
        await update.message.reply_text("🔒 Mission not completed yet!")

# -- Commands --

if text.startswith(",missions"):
    missions = get_player_missions(p)
    msg = "🎯 *Daily Missions:*\n"
    for k, v in missions.items():
        msg += f"- {k.replace('_', ' ').title()}: {v['progress']}/{v['target']} (Reward: {v['reward']} credits)\n"
    msg += "\nUse `,claim <mission>` to collect rewards."
    return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

if text.startswith(",claim"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("⚠️ Usage: ,claim <mission>")
    key = parts[1]
    missions = get_player_missions(p)
    if key not in missions:
        return await update.message.reply_text("❌ Mission not found.")
    await claim_mission(p, key, update)
    return

    ### BEGIN PART 9: PvP Ranking and Missions

    if text.startswith(",rank"):
        all_records = players_sheet.get_all_records()
        sorted_records = sorted(all_records, key=lambda x: int(x.get("Credits", 0)), reverse=True)
        leaderboard = "🏆 *Top Commanders:*\n"
        for idx, rec in enumerate(sorted_records[:10], 1):
            leaderboard += f"{idx}. {rec.get('Name', 'Unknown')} - {rec.get('Credits', 0)} credits\n"
        await update.message.reply_text(leaderboard, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",missions"):
        mission_text = (
            "🎯 *Available Missions:*\n"
            "1. Mine 500 ore ➡️ +100 Credits\n"
            "2. Forge 10 Units ➡️ +50 Energy\n"
            "3. Win a Pirate Raid ➡️ +1 Random Item\n\n"
            "_(Complete by doing actions normally!)_"
        )
        await update.message.reply_text(mission_text, parse_mode=ParseMode.MARKDOWN)
# -- Fortify Zone Command --

if text.startswith(",fortify"):
    if not p.get("Zone"):
        return await update.message.reply_text("⚠️ You don't control any zone yet!")

    fortify_cost = 750
    if p["Credits"] < fortify_cost:
        return await update.message.reply_text(f"💳 Need {fortify_cost} credits to fortify your zone!")

    # Simulate fortification: Increase player's passive defense or resource bonuses
    p["RefineryLevel"] += 1
    p["Credits"] -= fortify_cost
    save_player(p)
    return await update.message.reply_text(f"🏗️ Fortification complete! Refinery upgraded to level {p['RefineryLevel']}.\nDefense improved and mining efficiency boosted!")
# -- Create Faction Command --

if text.startswith(",createfaction"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🏳️ Usage: ,createfaction <name>")
    faction_name = parts[1]

    if p.get("Faction"):
        return await update.message.reply_text("⚠️ You already belong to a faction!")

    existing = players_sheet.get_all_records()
    for row in existing:
        if row.get("Faction") == faction_name:
            return await update.message.reply_text("❌ Faction name already taken!")

    p["Faction"] = faction_name
    save_player(p)
    return await update.message.reply_text(f"🏳️ Faction {faction_name} created successfully!")

# -- Join Faction Command --

if text.startswith(",joinfaction"):
    parts = text.split()
    if len(parts) != 2:
        return await update.message.reply_text("🏳️ Usage: ,joinfaction <name>")
    faction_name = parts[1]

    existing = players_sheet.get_all_records()
    found = False
    for row in existing:
        if row.get("Faction") == faction_name:
            found = True
            break

    if not found:
        return await update.message.reply_text("❌ No such faction found!")

    if p.get("Faction"):
        return await update.message.reply_text("⚠️ You already belong to a faction!")

    p["Faction"] = faction_name
    save_player(p)
    return await update.message.reply_text(f"🤝 You joined faction {faction_name}!")

    ### END PART 9
    ### BEGIN PART 10: Black Market and Premium Shop

    if text.startswith(",unlock blackmarket"):
        if p["Credits"] < 500:
            return await update.message.reply_text("❌ You need 500 credits to unlock the Black Market!")
        if p["BlackMarketUnlocked"] == "TRUE":
            return await update.message.reply_text("✅ Black Market already unlocked.")
        p["Credits"] -= 500
        p["BlackMarketUnlocked"] = "TRUE"
        save_player(p)
        return await update.message.reply_text("🛒 Black Market access granted! Use ,blackmarket to view items.")

    if text.startswith(",blackmarket"):
        if p["BlackMarketUnlocked"] != "TRUE":
            return await update.message.reply_text("🔒 Unlock the Black Market first! Use ,unlock blackmarket")
        bm_items = (
            "🛒 *Black Market Deals:*\n"
            "`buy infinityscout1` - R100 (1-use ultimate scout)\n"
            "`buy reviveall` - R500 (revive all units & buildings)\n"
            "`buy hazmat` - R200 (enter Radiation Zones)\n"
        )
        await update.message.reply_text(bm_items, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buy"):
        if p["BlackMarketUnlocked"] != "TRUE":
            return await update.message.reply_text("🔒 You must unlock Black Market first!")
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠️ Usage: ,buy <item>")
        item = parts[1].lower()

        prices = {
            "infinityscout1": 100,
            "reviveall": 500,
            "hazmat": 200
        }

        if item not in prices:
            return await update.message.reply_text("❓ Invalid item.")
        if p["Credits"] < prices[item]:
            return await update.message.reply_text("❌ Not enough credits!")

        p["Credits"] -= prices[item]
        items_owned = json.loads(p["Items"]) if p["Items"] else {}
        items_owned[item] = items_owned.get(item, 0) + 1
        p["Items"] = json.dumps(items_owned)
        save_player(p)
        return await update.message.reply_text(f"✅ Successfully bought {item}!")

    ### END PART 10
    ### BEGIN PART 11: Radiation Zones and Hazmat Handling

    radiation_zones = ["Zeta", "Sigma"]

    if text.startswith(",zones"):
        available = [z for z in radiation_zones if zones.get(z) is None]
        normal = [z for z in zones.keys() if z not in radiation_zones and zones.get(z) is None]
        return await update.message.reply_text(
            f"🌍 Available Zones:\nNormal: {', '.join(normal)}\nRadiation: {', '.join(available)}\n"
            "⚠ Radiation Zones require Hazmat Gear!"
        )

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,claim <zone>")
        target = parts[1]

        if target not in zones and target not in radiation_zones:
            return await update.message.reply_text("❓ Unknown zone.")

        if target in radiation_zones:
            items_owned = json.loads(p["Items"]) if p["Items"] else {}
            if "hazmat" not in items_owned:
                return await update.message.reply_text("☢ Radiation detected! You need Hazmat Gear to claim this zone.")

        if p["Credits"] < 200:
            return await update.message.reply_text("💳 You need 200 credits to claim a zone.")

        zones[target] = cid
        p["Zone"] = target
        p["Credits"] -= 200
        save_player(p)
        return await update.message.reply_text(f"✅ You have successfully claimed {target}!")

    ### END PART 11
    ### BEGIN PART 12: PvP Combat System (Attack Other Players)

    async def attack_enemy(attacker, defender, update):
        atk_power = 0
        def_power = 0

        atk_army = json.loads(attacker["Army"]) if attacker["Army"] else {}
        def_army = json.loads(defender["Army"]) if defender["Army"] else {}

        for unit, count in atk_army.items():
            atk_power += count * (5 if unit == "scout" else 10 if unit == "drone" else 20)

        for unit, count in def_army.items():
            def_power += count * (5 if unit == "scout" else 10 if unit == "drone" else 20)

        if atk_power > def_power:
            steal = int(defender["Ore"]) // 2
            attacker["Ore"] = int(attacker["Ore"]) + steal
            defender["Ore"] = int(defender["Ore"]) - steal
            save_player(attacker)
            save_player(defender)
            await update.message.reply_text(f"🏴‍☠️ Victory! You stole {steal} ore!")
        else:
            await update.message.reply_text(f"❌ Defeat! Enemy defenses too strong!")

    if text.startswith(",attack"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,attack <target_name>")

        target_name = parts[1]
        records = players_sheet.get_all_records()
        target_row = None
        for i, row in enumerate(records):
            if row["Name"].lower() == target_name.lower():
                target_row = row
                break

        if not target_row:
            return await update.message.reply_text("❓ Target not found!")

        if target_row["ShieldUntil"]:
            shield_until = datetime.strptime(target_row["ShieldUntil"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < shield_until:
                return await update.message.reply_text("🛡 Target is under shield protection!")

        await attack_enemy(p, target_row, update)

    ### END PART 12
    ### BEGIN PART 13: Shields and Defense Mechanics

    async def activate_shield(p, hours):
        shield_time = datetime.now() + timedelta(hours=hours)
        p["ShieldUntil"] = shield_time.strftime("%Y-%m-%d %H:%M:%S")
        save_player(p)

    if text.startswith(",shield"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,shield <hours> (e.g., ,shield 12)")

        try:
            hours = int(parts[1])
            if hours <= 0 or hours > 72:
                return await update.message.reply_text("⚠ Choose between 1 and 72 hours.")
        except ValueError:
            return await update.message.reply_text("⚠ Hours must be a number.")

        if int(p["Credits"]) < hours * 20:
            return await update.message.reply_text("❌ Not enough credits for shield. 20 credits per hour!")

        p["Credits"] = int(p["Credits"]) - (hours * 20)
        await activate_shield(p, hours)
        await update.message.reply_text(f"🛡 Shield activated for {hours} hours!")

    if text.startswith(",refinery"):
        if int(p["Credits"]) < 100:
            return await update.message.reply_text("❌ Need 100 credits to upgrade Refinery!")

        p["Credits"] = int(p["Credits"]) - 100
        p["RefineryLevel"] = int(p.get("RefineryLevel", 0)) + 1
        save_player(p)
        await update.message.reply_text(f"🏭 Refinery upgraded to level {p['RefineryLevel']}!")

    ### END PART 13
    ### BEGIN PART 14: Trading Mechanics (Player-to-Player Economy)

    offers = {}
    offer_counter = 1

    if text.startswith(",offer"):
        parts = text.split()
        if len(parts) != 5:
            return await update.message.reply_text(
                "⚠ Usage: ,offer <type> <amount> <price> <item> (example: ,offer sell 50 100 ore)"
            )

        _, offer_type, amount, price, item = parts
        try:
            amount = int(amount)
            price = int(price)
        except ValueError:
            return await update.message.reply_text("⚠ Amount and price must be numbers.")

        if offer_type not in ["sell", "buy"]:
            return await update.message.reply_text("⚠ Type must be 'sell' or 'buy'.")

        if item not in ["ore", "energy", "credits"]:
            return await update.message.reply_text("⚠ Item must be ore, energy, or credits.")

        # Validate player's balance for sell offers
        if offer_type == "sell":
            if item == "ore" and int(p["Ore"]) < amount:
                return await update.message.reply_text("❌ Not enough ore to sell!")
            if item == "energy" and int(p["Energy"]) < amount:
                return await update.message.reply_text("❌ Not enough energy to sell!")
            if item == "credits" and int(p["Credits"]) < amount:
                return await update.message.reply_text("❌ Not enough credits to sell!")

            # Lock the amount temporarily
            p[item.capitalize()] = int(p[item.capitalize()]) - amount
            save_player(p)

        global offer_counter
        offers[offer_counter] = {
            "cid": cid,
            "type": offer_type,
            "amount": amount,
            "price": price,
            "item": item
        }
        await update.message.reply_text(f"📢 Offer #{offer_counter} posted successfully!")
        offer_counter += 1

    if text.startswith(",market"):
        if not offers:
            return await update.message.reply_text("🏪 No active offers in the marketplace.")
        
        out = "🏪 *Active Market Offers:*\n\n"
        for oid, offer in offers.items():
            seller = players.get(offer["cid"], {}).get("Name", "Unknown")
            out += f"#{oid} | {offer['type'].upper()} {offer['amount']} {offer['item'].capitalize()} for {offer['price']} credits | By: {seller}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buyoffer"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,buyoffer <offer_id>")
        try:
            oid = int(parts[1])
        except ValueError:
            return await update.message.reply_text("⚠ Offer ID must be a number.")
        if oid not in offers:
            return await update.message.reply_text("❌ Offer not found.")

        offer = offers[oid]
        seller_p = get_player(offer["cid"])

        if int(p["Credits"]) < offer["price"]:
            return await update.message.reply_text("❌ Not enough credits to accept this offer!")

        p["Credits"] = int(p["Credits"]) - offer["price"]

        if offer["type"] == "sell":
            p[offer["item"].capitalize()] = int(p.get(offer["item"].capitalize(), 0)) + offer["amount"]
            seller_p["Credits"] = int(seller_p["Credits"]) + offer["price"]
            save_player(seller_p)
        else:
            seller_p[offer["item"].capitalize()] = int(seller_p.get(offer["item"].capitalize(), 0)) + offer["amount"]
            seller_p["Credits"] = int(seller_p["Credits"]) - offer["price"]
            save_player(seller_p)
            p[offer["item"].capitalize()] = int(p.get(offer["item"].capitalize(), 0)) + offer["amount"]

        save_player(p)
        del offers[oid]
        await update.message.reply_text("✅ Offer successfully completed!")

    ### END PART 14
    ### BEGIN PART 15: World Events and Boss Fights

    world_boss = None
    boss_timer = None

    if text.startswith(",summonboss"):
        if world_boss:
            return await update.message.reply_text("⚠ A boss is already active!")
        
        world_boss = {
            "name": "Titanus Omega",
            "hp": 10000,
            "attack_power": 250,
            "reward_credits": 300,
            "reward_ore": 500
        }
        boss_timer = datetime.now() + timedelta(minutes=60)
        await update.message.reply_text(
            "🚨 *Alert! Titanus Omega has appeared in the wastelands!*\n"
            "⏳ You have 60 minutes to defeat it!\n"
            "🗡 Attack it with `,attackboss <your army>`!",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",bossstatus"):
        if not world_boss:
            return await update.message.reply_text("☀ No active bosses currently.")
        time_left = (boss_timer - datetime.now()).seconds // 60
        await update.message.reply_text(
            f"👹 *Boss Status:*\n"
            f"Name: {world_boss['name']}\n"
            f"HP: {world_boss['hp']}\n"
            f"Time left: {time_left} min",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",attackboss"):
        if not world_boss:
            return await update.message.reply_text("☀ No boss to attack!")
        
        army = json.loads(p["Army"])
        damage = army["scout"] * 5 + army["drone"] * 8 + army["tank"] * 15

        if damage == 0:
            return await update.message.reply_text("⚠ You have no army units to attack!")

        world_boss["hp"] -= damage

        if world_boss["hp"] <= 0:
            reward_credits = world_boss["reward_credits"]
            reward_ore = world_boss["reward_ore"]
            p["Credits"] += reward_credits
            p["Ore"] += reward_ore
            save_player(p)
            world_boss = None
            await update.message.reply_text(
                f"🏆 You landed the final blow on the boss!\n"
                f"🎁 Rewards: +{reward_credits} Credits, +{reward_ore} Ore."
            )
        else:
            save_player(p)
            await update.message.reply_text(
                f"⚔ You dealt {damage} damage to {world_boss['name']}!\n"
                f"🧟 Remaining HP: {world_boss['hp']}"
            )

    ### END PART 15
    ### BEGIN PART 16: Radiation Zones + Hazmat Enforcement

    radiation_zones = ["Zeta", "Omega", "Kronos"]

    # Expand map if needed
    for rz in radiation_zones:
        if rz not in zones:
            zones[rz] = None

    if text.startswith(",map"):
        out = "🌍 *Zone Control Map:*\n\n"
        for z, owner in zones.items():
            name = players.get(owner, {}).get("Name", "Unclaimed") if owner else "Unclaimed"
            if z in radiation_zones:
                out += f"☢ {z} (Radiated): {name}\n"
            else:
                out += f"🛡 {z}: {name}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,claim <zone>")
        
        zone = parts[1]
        if zone not in zones:
            return await update.message.reply_text("⚠ Unknown zone.")
        
        if zones[zone]:
            return await update.message.reply_text("⚠ Zone already claimed.")

        # Check radiation requirement
        if zone in radiation_zones:
            items = json.loads(p["Items"])
            if "hazmat" not in items or items["hazmat"] <= 0:
                return await update.message.reply_text(
                    "☢ You need a Hazmat Drone (Black Market) to access radiation zones!"
                )
        
        if p["Credits"] < 150:
            return await update.message.reply_text("💳 You need at least 150 Credits to claim a zone.")

        zones[zone] = cid
        p["Zone"] = zone
        p["Credits"] -= 150
        save_player(p)

        await update.message.reply_text(f"🏴 Successfully claimed {zone}!")

    ### END PART 16
    ### BEGIN PART 17: EMP Field Device (Item Usage)

    if text.startswith(",emp"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚡ Usage: ,emp <target_alias>")
        
        target_alias = parts[1]
        target_cid, target_p = find_by_name(target_alias)

        if not target_p:
            return await update.message.reply_text("⚡ Target not found.")
        
        if not target_p["ShieldUntil"]:
            return await update.message.reply_text("⚡ Target has no active shield to disable.")

        # Check if player owns EMP device
        items = json.loads(p["Items"])
        if "empdevice" not in items or items["empdevice"] <= 0:
            return await update.message.reply_text("⚡ You don't have an EMP Field Device.")
        
        # Consume EMP device
        items["empdevice"] -= 1
        if items["empdevice"] == 0:
            del items["empdevice"]
        p["Items"] = json.dumps(items)
        save_player(p)

        # Remove target shield
        target_p["ShieldUntil"] = ""
        save_player(target_p)

        await update.message.reply_text(f"💥 EMP Deployed! {target_p['Name']}'s shield disabled!")

    ### END PART 17
    ### BEGIN PART 18: Advanced Shields (Auto-Daily)

    if text.startswith(",shieldinfo"):
        has_adv_shield = False
        items = json.loads(p["Items"])
        if "advancedshield" in items and items["advancedshield"] > 0:
            has_adv_shield = True

        status = (
            "🛡 *Shield Status:*\n"
            f"- {'✅' if p['ShieldUntil'] else '❌'} Normal Daily Shield\n"
            f"- {'✅' if has_adv_shield else '❌'} Advanced Shield (auto-absorb first attack)"
        )
        return await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

    async def apply_daily_shields():
        """At daily reset, auto-reapply normal shields for all players."""
        records = players_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            # Normal shield reset daily
            record["ShieldUntil"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            players_sheet.update(f"H{idx}", [[record["ShieldUntil"]]])

    def consume_advanced_shield(p):
        """Consume player's advanced shield if attacked."""
        items = json.loads(p["Items"])
        if "advancedshield" in items and items["advancedshield"] > 0:
            items["advancedshield"] -= 1
            if items["advancedshield"] == 0:
                del items["advancedshield"]
            p["Items"] = json.dumps(items)
            save_player(p)
            return True
        return False

    ### END PART 18
    ### BEGIN PART 19: Zone Control - Occupation and Scoring

    zone_scores = {z: 0 for z in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]}

    if text.startswith(",zoneclaim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,zoneclaim <zone>")
        zone = parts[1].capitalize()
        if zone not in zone_scores:
            return await update.message.reply_text("⚠ Invalid zone.")
        if p["Zone"]:
            return await update.message.reply_text("⚠ You already control a zone. Abandon first.")
        if int(p["Credits"]) < 100:
            return await update.message.reply_text("⚠ Need 100 credits to claim zone.")

        p["Zone"] = zone
        p["Credits"] = int(p["Credits"]) - 100
        update_player(p)

        zone_scores[zone] = cid
        return await update.message.reply_text(f"🏴 You now control zone {zone}!")

    if text.startswith(",zonemap"):
        msg = "🗺 *Zone Control Map:*\n\n"
        for zone, owner_id in zone_scores.items():
            owner_name = "Unclaimed"
            if owner_id and str(owner_id) != "0":
                owner = get_player(owner_id)
                owner_name = owner["Name"] or "Unknown"
            msg += f"🏳️ {zone}: {owner_name}\n"
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",abandonzone"):
        if not p["Zone"]:
            return await update.message.reply_text("⚠ You don't control any zone.")
        zone = p["Zone"]
        p["Zone"] = ""
        update_player(p)
        zone_scores[zone] = 0
        return await update.message.reply_text(f"⚠ You abandoned zone {zone}.")

    async def zone_score_tick():
        """Award points to players controlling zones every hour."""
        records = players_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record["Zone"]:
                record["Credits"] = int(record["Credits"]) + 10  # 10 credits per hour for control
                players_sheet.update(f"E{idx}", [[record["Credits"]]])

    ### END PART 19
    ### BEGIN PART 20: Trading & World Bank

    trade_offers = {}
    trade_id_counter = 1
    world_bank = {"Ore": 100000, "Credits": 50000}

    if text.startswith(",offer"):
        parts = text.split()
        if len(parts) != 5:
            return await update.message.reply_text("⚠ Usage: ,offer <type> <amount> <cost> <resource>")
        _, trade_type, amount, cost, resource = parts
        amount = int(amount)
        cost = int(cost)

        if trade_type not in ["sell", "buy"]:
            return await update.message.reply_text("⚠ Trade type must be sell or buy.")
        if resource not in ["Ore", "Credits"]:
            return await update.message.reply_text("⚠ Resource must be Ore or Credits.")
        
        global trade_id_counter
        tid = trade_id_counter
        trade_id_counter += 1

        trade_offers[tid] = {
            "type": trade_type,
            "amount": amount,
            "cost": cost,
            "resource": resource,
            "seller": cid
        }
        return await update.message.reply_text(f"📜 Trade offer created with ID {tid}.")

    if text.startswith(",market"):
        if not trade_offers:
            return await update.message.reply_text("🏦 No active market offers.")
        msg = "🏦 *Market Offers:*\n\n"
        for tid, offer in trade_offers.items():
            seller = get_player(offer["seller"])["Name"] or "Unknown"
            msg += f"ID {tid}: {offer['type']} {offer['amount']} {offer['resource']} for {offer['cost']} Credits [{seller}]\n"
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",accept"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("⚠ Usage: ,accept <id>")
        tid = int(parts[1])
        if tid not in trade_offers:
            return await update.message.reply_text("⚠ Offer not found.")
        offer = trade_offers[tid]

        if offer["type"] == "sell":
            # Buyer must have enough credits
            if int(p["Credits"]) < offer["cost"]:
                return await update.message.reply_text("⚠ Not enough credits.")
            seller = get_player(offer["seller"])
            p[offer["resource"]] = int(p.get(offer["resource"], 0)) + offer["amount"]
            p["Credits"] = int(p["Credits"]) - offer["cost"]
            seller["Credits"] = int(seller["Credits"]) + offer["cost"]
            update_player(p)
            update_player(seller)
        elif offer["type"] == "buy":
            # Seller must have enough resource
            if int(p.get(offer["resource"], 0)) < offer["amount"]:
                return await update.message.reply_text("⚠ Not enough resource.")
            buyer = get_player(offer["seller"])
            p[offer["resource"]] = int(p.get(offer["resource"], 0)) - offer["amount"]
            p["Credits"] = int(p["Credits"]) + offer["cost"]
            buyer[offer["resource"]] = int(buyer.get(offer["resource"], 0)) + offer["amount"]
            buyer["Credits"] = int(buyer["Credits"]) - offer["cost"]
            update_player(p)
            update_player(buyer)

        del trade_offers[tid]
        return await update.message.reply_text(f"✅ Trade ID {tid} completed.")

    if text.startswith(",bankinfo"):
        return await update.message.reply_text(
            f"🏦 *World Bank:*\nOre: {world_bank['Ore']}\nCredits: {world_bank['Credits']}",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",bankbuy"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚠ Usage: ,bankbuy <resource> <amount>")
        res = parts[1].capitalize()
        amt = int(parts[2])
        if res not in ["Ore", "Credits"]:
            return await update.message.reply_text("⚠ Resource must be Ore or Credits.")

        price_per_unit = 5 if res == "Ore" else 10
        total_cost = amt * price_per_unit

        if int(p["Credits"]) < total_cost:
            return await update.message.reply_text("⚠ Not enough credits.")
        if world_bank[res] < amt:
            return await update.message.reply_text("⚠ Bank doesn't have that much.")

        p[res] = int(p.get(res, 0)) + amt
        p["Credits"] = int(p["Credits"]) - total_cost
        world_bank[res] -= amt
        update_player(p)

        return await update.message.reply_text(f"🏦 Purchased {amt} {res} for {total_cost} credits.")

    ### END PART 20
    ### BEGIN PART 21: Global Events

    from random import randint, choice

    invasion_targets = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    last_event_time = datetime.now()

    async def check_global_events():
        global last_event_time
        now = datetime.now()

        if (now - last_event_time).seconds > 300:  # Every 5 minutes
            event_type = randint(1, 3)
            last_event_time = now

            if event_type == 1:
                lucky_zone = choice(invasion_targets)
                lucky_bonus = randint(100, 500)
                world_bank["Ore"] += lucky_bonus
                await broadcast_message(f"🌟 Cosmic Surge detected at {lucky_zone}! Bank Ore increased by {lucky_bonus}!")

            elif event_type == 2:
                unlucky_zone = choice(invasion_targets)
                unlucky_penalty = randint(50, 200)
                world_bank["Credits"] = max(0, world_bank["Credits"] - unlucky_penalty)
                await broadcast_message(f"⚠ Solar Flare hit {unlucky_zone}! Bank lost {unlucky_penalty} Credits.")

            elif event_type == 3:
                target_zone = choice(invasion_targets)
                await broadcast_message(f"👾 ALERT: Alien Invaders are attacking Zone {target_zone}!")
                # Invasion weakens whoever owns it
                for cid, p in players.items():
                    if p["Zone"] == target_zone:
                        p["Energy"] = max(0, int(p["Energy"]) - 20)
                        update_player(p)

    async def broadcast_message(text):
        for cid in players.keys():
            try:
                await app.bot.send_message(chat_id=cid, text=text)
            except:
                pass  # In case someone blocked the bot

    ### END PART 21
# -- Daily and Weekly Missions System --

# (At the top after imports)
import random

# -- Mission Templates --
daily_missions = [
    "Mine 100 ore",
    "Forge 5 scouts",
    "Win 1 attack",
    "Claim a zone",
]
weekly_missions = [
    "Win 5 battles",
    "Forge 20 tanks",
    "Earn 1000 credits",
]

def assign_daily_mission(p):
    if not p.get("DailyMission"):
        p["DailyMission"] = random.choice(daily_missions)

def assign_weekly_mission(p):
    if not p.get("WeeklyMission"):
        p["WeeklyMission"] = random.choice(weekly_missions)

# -- Mission Checking --
async def check_mission_completion(p, update):
    completed = []
    
    if p.get("DailyMission") == "Mine 100 ore" and p["Ore"] >= 100:
        completed.append("Daily")
    if p.get("DailyMission") == "Forge 5 scouts" and p["Army"].get("scout", 0) >= 5:
        completed.append("Daily")
    if p.get("DailyMission") == "Win 1 attack" and p["Wins"] >= 1:
        completed.append("Daily")
    if p.get("DailyMission") == "Claim a zone" and p["Zone"]:
        completed.append("Daily")
    
    if p.get("WeeklyMission") == "Win 5 battles" and p["Wins"] >= 5:
        completed.append("Weekly")
    if p.get("WeeklyMission") == "Forge 20 tanks" and p["Army"].get("tank", 0) >= 20:
        completed.append("Weekly")
    if p.get("WeeklyMission") == "Earn 1000 credits" and p["Credits"] >= 1000:
        completed.append("Weekly")
    
    reward_message = ""
    for mission in completed:
        if mission == "Daily":
            reward_message += "🎯 Completed Daily Mission! +200 credits!\n"
            p["Credits"] += 200
            p["DailyMission"] = None
        if mission == "Weekly":
            reward_message += "🎯 Completed Weekly Mission! +1000 credits!\n"
            p["Credits"] += 1000
            p["WeeklyMission"] = None
    
    if reward_message:
        save_player(p)
        await update.message.reply_text(reward_message)

# -- New Command to Show Missions --
if text.startswith(",missions"):
    assign_daily_mission(p)
    assign_weekly_mission(p)
    msg = (
        f"🗓️ *Your Missions:*\n"
        f"Daily: `{p.get('DailyMission', 'None')}`\n"
        f"Weekly: `{p.get('WeeklyMission', 'None')}`"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    return

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.create_task(background_tasks())  # <-- NEW line to add
    app.run_polling()



  
