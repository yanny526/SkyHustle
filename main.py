import os
import json
import asyncio
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from sheet import get_sheet

players_sheet = get_sheet().worksheet("SkyHustle")

def get_player(cid):
    records = players_sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row["ChatID"]) == str(cid):
            row["_row"] = i + 2
            row["Army"] = json.loads(row["Army"]) if row["Army"] else {"scout": 0, "tank": 0, "drone": 0}
            row["Items"] = json.loads(row["Items"]) if row["Items"] else {}
            row["BlackMarketUnlocked"] = True if row.get("BlackMarketUnlocked") == "TRUE" else False
            return row

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
        new_player["ChatID"], new_player["Name"], new_player["Ore"], new_player["Energy"], new_player["Credits"],
        json.dumps(new_player["Army"]), new_player["Zone"], new_player["ShieldUntil"],
        new_player["DailyStreak"], new_player["LastDaily"], new_player["BlackMarketUnlocked"], json.dumps(new_player["Items"])
    ])
    new_player["_row"] = len(records) + 2
    return new_player

def update_player(p):
    players_sheet.update(
        f"A{p['_row']}:L{p['_row']}",
        [[
            p["ChatID"], p["Name"], p["Ore"], p["Energy"], p["Credits"],
            json.dumps(p["Army"]), p["Zone"], p["ShieldUntil"],
            p["DailyStreak"], p["LastDaily"], p["BlackMarketUnlocked"], json.dumps(p["Items"])
        ]]
    )

def save_player(p):
    update_player(p)
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    p = get_player(cid)

    if text.startswith(",start"):
        intro = (
            "🌌 Welcome to *SkyHustle*!\n"
            "The world of Hyperion awaits you, Commander.\n\n"
            "⚡ *Set Callsign:* `,name <alias>`\n"
            "📊 *View Status:* `,status`\n"
            "🛠️ *Begin Mining:* `,mine ore <amount>`\n"
            "🎯 *Daily Rewards:* `,daily`\n"
            "🏰 *Claim a Zone:* `,claim <zone>`\n"
        )
        return await update.message.reply_text(intro, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠️ Usage: ,name <alias>")
        p["Name"] = alias
        save_player(p)
        return await update.message.reply_text(f"🚩 Callsign set to *{alias}*", parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items = json.loads(p["Items"])
        status = (
            f"📜 *Commander {p['Name']}*\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🛡 Zone: {p['Zone'] or 'None'} | 🎯 Daily Streak: {p['DailyStreak']}\n"
            f"🤖 Army: {army}\n"
            f"🎒 Items: {items or 'None'}"
        )
        return await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)
        if text.startswith(",name"):
        alias = text[6:].strip()
        if not alias:
            return await update.message.reply_text("⚠️ Usage: ,name <alias>")
        p["Name"] = alias
        save_player(p)
        return await update.message.reply_text(f"🎖️ Callsign set to {alias}!")

    if text.startswith(",status"):
        army = json.loads(p["Army"])
        items_owned = ", ".join([f"{k}x{v}" for k, v in json.loads(p["Items"]).items()]) or "None"
        msg = (
            f"📊 *Commander {p['Name'] or 'Unknown'}*\n"
            f"🪨 Ore: {p['Ore']} | ⚡ Energy: {p['Energy']} | 💳 Credits: {p['Credits']}\n"
            f"🤖 Army: {army}\n"
            f"🎒 Items: {items_owned}\n"
            f"📍 Zone: {p['Zone'] or 'None'}"
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        if text.startswith(",daily"):
        today = str(date.today())
        if p["LastDaily"] == today:
            return await update.message.reply_text("🎁 You've already claimed your daily reward today!")
        last = p["LastDaily"]
        if last and last == str(date.today() - timedelta(days=1)):
            p["DailyStreak"] += 1
        else:
            p["DailyStreak"] = 1
        p["Credits"] += 50
        p["Energy"] += 25
        p["LastDaily"] = today
        save_player(p)
        return await update.message.reply_text(f"🎉 +50 Credits, +25 Energy! Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠️ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠️ Count must be a number.")
        if p["Energy"] < count * 5:
            return await update.message.reply_text("⚡ Not enough Energy.")
        ore_gain = 20 * count
        p["Ore"] += ore_gain
        p["Energy"] -= count * 5
        p["Credits"] += 10 * count
        save_player(p)
        return await update.message.reply_text(f"⛏️ You mined {ore_gain} ore and earned {10*count} credits!")
        if text.startswith(",forge"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("⚒️ Usage: ,forge <unit> <count>")

        unit = parts[1].lower()
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠️ Count must be a number.")

        if unit not in ["scout", "tank", "drone"]:
            return await update.message.reply_text("⚠️ Invalid unit. Available: scout, tank, drone.")

        unit_costs = {
            "scout": {"Ore": 20, "Credits": 10},
            "tank": {"Ore": 50, "Credits": 30},
            "drone": {"Ore": 80, "Credits": 50}
        }

        cost = unit_costs[unit]
        if p["Ore"] < cost["Ore"] * count or p["Credits"] < cost["Credits"] * count:
            return await update.message.reply_text("💳 Not enough resources!")

        p["Ore"] -= cost["Ore"] * count
        p["Credits"] -= cost["Credits"] * count
        army = json.loads(p["Army"])
        army[unit] += count
        p["Army"] = json.dumps(army)
        save_player(p)
        return await update.message.reply_text(f"⚔️ Forged {count} {unit}(s) successfully!")
    if text.startswith(",spy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🕵️ Usage: ,spy <enemy alias>")

        enemy_alias = parts[1]
        enemy = find_player_by_name(enemy_alias)
        if not enemy:
            return await update.message.reply_text("🎯 Target not found!")

        scout_count = json.loads(p["Army"]).get("scout", 0)
        if scout_count <= 0:
            return await update.message.reply_text("🚫 You need at least 1 scout to spy.")

        success = random.choice([True, False])
        if success:
            army = json.loads(enemy["Army"])
            return await update.message.reply_text(
                f"🛰️ Spy Report on {enemy['Name']}:\n"
                f"Ore: {enemy['Ore']} | Credits: {enemy['Credits']}\n"
                f"Army: {army}"
            )
        else:
            return await update.message.reply_text("❌ Your scouts failed to gather intel.")
                if text.startswith(",missions"):
        mission_list = [
            "🛡 Complete a daily login streak (5 days)",
            "⛏ Mine 500 Ore",
            "⚔️ Win 5 Battles",
            "🏗 Upgrade your Refinery",
            "🛰 Unlock the Black Market"
        ]
        msg = "🎯 *Available Missions:*\n\n" + "\n".join(f"- {m}" for m in mission_list)
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claimmission"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏅 Usage: ,claimmission <mission>")
        mission_id = parts[1]
        if mission_id == "1" and p["DailyStreak"] >= 5:
            p["Credits"] += 200
            await update.message.reply_text("🎯 Mission 1 completed! +200 credits.")
        elif mission_id == "2" and p["Ore"] >= 500:
            p["Credits"] += 150
            await update.message.reply_text("🎯 Mission 2 completed! +150 credits.")
        elif mission_id == "3" and p["Wins"] >= 5:
            p["Credits"] += 300
            await update.message.reply_text("🎯 Mission 3 completed! +300 credits.")
        elif mission_id == "4" and p["RefineryLevel"] >= 2:
            p["Credits"] += 250
            await update.message.reply_text("🎯 Mission 4 completed! +250 credits.")
        elif mission_id == "5" and p.get("BlackMarketUnlocked"):
            p["Credits"] += 500
            await update.message.reply_text("🎯 Mission 5 completed! +500 credits.")
        else:
            return await update.message.reply_text("🚫 Mission requirements not met.")
        save_player(p)
        return

    if text.startswith(",upgrade"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏗 Usage: ,upgrade <refinery/lab>")
        building = parts[1]
        if building == "refinery":
            cost = (p["RefineryLevel"] + 1) * 100
            if p["Credits"] < cost:
                return await update.message.reply_text(f"💳 Need {cost} credits to upgrade.")
            p["Credits"] -= cost
            p["RefineryLevel"] += 1
            save_player(p)
            return await update.message.reply_text(f"🏗 Refinery upgraded to level {p['RefineryLevel']}!")
        elif building == "lab":
            cost = (p["LabLevel"] + 1) * 120
            if p["Credits"] < cost:
                return await update.message.reply_text(f"💳 Need {cost} credits to upgrade.")
            p["Credits"] -= cost
            p["LabLevel"] += 1
            save_player(p)
            return await update.message.reply_text(f"🔬 Lab upgraded to level {p['LabLevel']}!")
        else:
            return await update.message.reply_text("🏗 Invalid building. Use ,upgrade refinery or ,upgrade lab.")

    if text.startswith(",store"):
        msg = (
            "🏪 *SkyHustle Store:*\n"
            "`pack1` - 500 credits for 5$\n"
            "`pack2` - 1200 credits for 10$\n"
            "`pack3` - 3000 credits for 20$\n\n"
            "Use ,buycredit <pack> to purchase."
        )
        return await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",buycredit"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏪 Usage: ,buycredit <pack>")
        pack = parts[1]
        if pack == "pack1":
            p["Credits"] += 500
        elif pack == "pack2":
            p["Credits"] += 1200
        elif pack == "pack3":
            p["Credits"] += 3000
        else:
            return await update.message.reply_text("🏪 Invalid pack. Use pack1, pack2, or pack3.")
        save_player(p)
        return await update.message.reply_text(f"🏪 Purchased {pack}! Credits added.")
            if text.startswith(",donate"):
        parts = text.split()
        if len(parts) != 3:
            return await update.message.reply_text("💳 Usage: ,donate <player alias> <amount>")
        alias = parts[1]
        amount = parts[2]
        try:
            amount = int(amount)
        except:
            return await update.message.reply_text("⚠ Amount must be a number.")

        target_row = find_player_by_name(alias)
        if not target_row:
            return await update.message.reply_text("👤 Target player not found.")

        if amount <= 0:
            return await update.message.reply_text("⚠ Invalid donation amount.")

        if p["Credits"] < amount:
            return await update.message.reply_text("💳 You don't have enough credits.")

        p["Credits"] -= amount
        target_row["Credits"] += amount
        save_player(p)
        save_player(target_row)

        return await update.message.reply_text(f"🎁 Donated {amount} credits to {target_row['Name']}!")

    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🔬 Usage: ,research <field>")
        field = parts[1]
        if field not in ["speed", "armor"]:
            return await update.message.reply_text("🔬 Invalid research field. Use speed or armor.")

        cost = 100 + (p["ResearchLevels"][field] * 50)
        if p["Credits"] < cost:
            return await update.message.reply_text(f"💳 Need {cost} credits for this research.")

        p["Credits"] -= cost
        p["ResearchLevels"][field] += 1
        save_player(p)

        return await update.message.reply_text(f"🔬 Upgraded {field} research to Level {p['ResearchLevels'][field]}!")

    if text.startswith(",build"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏗️ Usage: ,build <structure>")
        structure = parts[1]
        valid_structures = ["refinery", "lab", "defense"]
        if structure not in valid_structures:
            return await update.message.reply_text("🏗️ Structures: refinery, lab, defense")

        cost = 200
        if p["Credits"] < cost:
            return await update.message.reply_text("💳 Not enough credits.")

        if structure == "refinery":
            p["RefineryLevel"] += 1
        elif structure == "lab":
            p["LabLevel"] += 1
        elif structure == "defense":
            p["DefenseLevel"] += 1

        p["Credits"] -= cost
        save_player(p)

        return await update.message.reply_text(f"🏗️ Upgraded {structure} to level {p[structure.capitalize()+'Level']}!")
    if text.startswith(",missions"):
        today = date.today()
        mission_report = (
            f"🎯 *Your Missions for {today}:*\n"
            "• Mine ore x5 ✅\n"
            "• Forge units x3 ✅\n"
            "• Donate credits ✅\n"
            "• Attack a player ✅\n"
            "\n(Missions system will track officially soon!)"
        )
        return await update.message.reply_text(mission_report, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🧪 Usage: ,use <item>")
        item_name = parts[1]

        if item_name not in p["Items"] or p["Items"][item_name] == 0:
            return await update.message.reply_text("❌ You don't own that item.")

        # Perishable item use
        if item_name.startswith("infinityscout"):
            return await update.message.reply_text("🛰️ Sending Infinity Scout... (scouting not yet live)")

        if item_name == "reviveall":
            for unit in p["Army"]:
                p["Army"][unit] += 5
            p["Ore"] += 200
            p["Energy"] += 100
            del p["Items"][item_name]
            save_player(p)
            return await update.message.reply_text("⚕️ All troops revived + bonus resources!")

        if item_name == "hazmat":
            p["HasHazmat"] = True
            save_player(p)
            return await update.message.reply_text("☢️ Hazmat Equipment activated. You can now enter Radiation Zones!")

        return await update.message.reply_text("❓ Unknown item effect.")

    if text.startswith(",zones"):
        out = "🗺️ *Zone Control Map:*\n"
        for z, o in zones.items():
            owner = "Unclaimed" if not o else players.get(o, {}).get("Name", "???")
            out += f"{z} ➔ {owner}\n"
        return await update.message.reply_text(out, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🗺️ Usage: ,claim <zone>")
        zone_name = parts[1]
        if zone_name not in zones:
            return await update.message.reply_text("⚠️ Invalid zone.")

        if zones[zone_name] and zones[zone_name] != p["ChatID"]:
            return await update.message.reply_text("🚫 Zone already claimed by another Commander!")

        if p["Credits"] < 300:
            return await update.message.reply_text("💳 Need 300 credits to claim a zone.")

        p["Credits"] -= 300
        p["Zone"] = zone_name
        zones[zone_name] = p["ChatID"]
        save_player(p)

        return await update.message.reply_text(f"🏴 Claimed zone {zone_name}! Expand your Empire!")
    if text.startswith(",research"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🧬 Usage: ,research <tech>")
        tech = parts[1]
        if tech not in ["speed", "armor"]:
            return await update.message.reply_text("🧬 Invalid technology. Choose 'speed' or 'armor'.")

        if p["Credits"] < 500:
            return await update.message.reply_text("💳 Need 500 credits to research!")

        p["Credits"] -= 500
        p["Research"][tech] += 1
        save_player(p)

        return await update.message.reply_text(f"🧪 {tech.capitalize()} research upgraded to level {p['Research'][tech]}!")

    if text.startswith(",build"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🏗️ Usage: ,build <structure>")

        building = parts[1].lower()
        structures = {
            "refinery": "RefineryLevel",
            "lab": "LabLevel",
            "defense": "DefenseLevel"
        }

        if building not in structures:
            return await update.message.reply_text("🏗️ Available: refinery, lab, defense.")

        level_key = structures[building]
        current_level = p.get(level_key, 0)

        cost = 200 + (current_level * 150)
        if p["Credits"] < cost:
            return await update.message.reply_text(f"💳 Not enough credits! {cost} needed.")

        p["Credits"] -= cost
        p[level_key] = current_level + 1
        save_player(p)

        return await update.message.reply_text(f"🏗️ {building.capitalize()} upgraded to level {p[level_key]}!")

    if text.startswith(",store"):
        return await update.message.reply_text(
            "🛒 *Store Packages:*\n"
            "• `pack1` ➔ 500 Credits ➔ 5 Units each\n"
            "• `pack2` ➔ 1500 Credits ➔ 20 Units each\n"
            "• `pack3` ➔ 3000 Credits ➔ 50 Units each\n"
            "\nUse ,buy <pack> to purchase.",
            parse_mode=ParseMode.MARKDOWN
        )

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buy <pack>")
        pack = parts[1].lower()

        if pack == "pack1":
            cost = 500
            bonus = 5
        elif pack == "pack2":
            cost = 1500
            bonus = 20
        elif pack == "pack3":
            cost = 3000
            bonus = 50
        else:
            return await update.message.reply_text("🛒 Invalid pack. Choose pack1, pack2, or pack3.")

        if p["Credits"] < cost:
            return await update.message.reply_text("💳 Not enough credits.")

        p["Credits"] -= cost
        for unit in p["Army"]:
            p["Army"][unit] += bonus
        save_player(p)

        return await update.message.reply_text(f"🛒 Purchased {pack}. Units boosted!")

    if text.startswith(",pvp"):
        board = "🏆 *Top PvP Players:*\n"
        leaderboard = sorted(players.values(), key=lambda x: x.get("Wins", 0), reverse=True)[:5]
        for idx, commander in enumerate(leaderboard, 1):
            board += f"{idx}. {commander['Name']} - {commander.get('Wins', 0)} Wins\n"

        return await update.message.reply_text(board, parse_mode=ParseMode.MARKDOWN)
    if text.startswith(",missions"):
        mission_text = (
            "🎯 *Available Missions:*\n"
            "• Mine 100 Ore ➔ +200 Credits\n"
            "• Win 3 Battles ➔ +500 Credits\n"
            "• Recruit 20 Units ➔ +300 Credits\n"
            "\nUse ,claim <mission> to claim rewards."
        )
        return await update.message.reply_text(mission_text, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🎯 Usage: ,claim <mission>")

        mission = parts[1].lower()

        if mission == "mine":
            if p["Ore"] >= 100:
                p["Credits"] += 200
                p["Ore"] -= 100
                save_player(p)
                return await update.message.reply_text("✅ Mission Complete: +200 Credits!")
            else:
                return await update.message.reply_text("⚒️ You haven't mined enough Ore yet!")

        elif mission == "battles":
            if p.get("Wins", 0) >= 3:
                p["Credits"] += 500
                p["Wins"] -= 3
                save_player(p)
                return await update.message.reply_text("✅ Mission Complete: +500 Credits!")
            else:
                return await update.message.reply_text("⚔️ You haven't won enough battles yet!")

        elif mission == "recruit":
            total_units = sum(p["Army"].values())
            if total_units >= 20:
                p["Credits"] += 300
                for unit in p["Army"]:
                    p["Army"][unit] = max(0, p["Army"][unit] - 5)
                save_player(p)
                return await update.message.reply_text("✅ Mission Complete: +300 Credits!")
            else:
                return await update.message.reply_text("🛡️ You haven't recruited enough units yet!")

        else:
            return await update.message.reply_text("❓ Unknown mission. Try: mine, battles, recruit")

    if text.startswith(",blackmarket"):
        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 Black Market locked. Use ,unlockbm first.")
        shop = (
            "🖤 *Black Market Deals:*\n"
            "• `buy infinityscout1` - 100 Credits\n"
            "• `buy reviveall` - 500 Credits\n"
            "• `buy hazmat` - 250 Credits\n"
            "\nUse ,buy <item> to purchase."
        )
        return await update.message.reply_text(shop, parse_mode=ParseMode.MARKDOWN)

    if text.startswith(",unlockbm"):
        if p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("✅ Black Market already unlocked.")
        if p["Credits"] < 1000:
            return await update.message.reply_text("💳 You need 1000 Credits to unlock the Black Market.")

        p["Credits"] -= 1000
        p["BlackMarketUnlocked"] = True
        save_player(p)
        return await update.message.reply_text("🖤 Black Market access granted!")

    if text.startswith(",buy"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("🛒 Usage: ,buy <item>")
        item = parts[1].lower()

        if not p.get("BlackMarketUnlocked"):
            return await update.message.reply_text("🔒 You must unlock Black Market first.")

        price_table = {
            "infinityscout1": 100,
            "reviveall": 500,
            "hazmat": 250
        }

        if item not in price_table:
            return await update.message.reply_text("🛒 Invalid item. Check ,blackmarket.")

        price = price_table[item]

        if p["Credits"] < price:
            return await update.message.reply_text("💳 Not enough credits to buy.")

        p["Credits"] -= price
        p["Items"].setdefault(item, 0)
        p["Items"][item] += 1
        save_player(p)

        return await update.message.reply_text(f"🛒 Purchased {item} successfully!")






