# SkyHustle Main Core - PART 1

import os
import json
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from sheet import get_sheet

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
        if p["LastDaily"] == str(today):
            return await update.message.reply_text("🎁 Already claimed today.")
        last = datetime.strptime(p["LastDaily"], "%Y-%m-%d") if p["LastDaily"] else None
        streak = int(p["DailyStreak"])
        p["Credits"] = int(p["Credits"]) + 50
        p["Energy"] = int(p["Energy"]) + 30
        p["DailyStreak"] = streak + 1 if last and last.date() == today - timedelta(days=1) else 1
        p["LastDaily"] = str(today)
        update_player(p)
        return await update.message.reply_text(f"🎁 Claimed +50 Credits, +30 Energy! Streak: {p['DailyStreak']} days.")

    if text.startswith(",mine"):
        parts = text.split()
        if len(parts) != 3 or parts[1] != "ore":
            return await update.message.reply_text("⚠ Usage: ,mine ore <count>")
        try:
            count = int(parts[2])
        except:
            return await update.message.reply_text("⚠ Count must be a number.")
        if p["Energy"] < count * 5:
            return await update.message.reply_text("⚠ Not enough energy.")
        ore_gain = 20 * count
        p["Ore"] += ore_gain
        p["Energy"] -= count * 5
        update_player(p)
        return await update.message.reply_text(f"⛏ Your miners recovered *{ore_gain} Ore* from Hyperion’s core!", parse_mode=ParseMode.MARKDOWN)

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

    if text.startswith(",use"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,use <item>")
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

    if text.startswith(",claim"):
        parts = text.split()
        if len(parts) != 2:
            return await update.message.reply_text("Usage: ,claim <zone>")
        zone = parts[1]
        if zone not in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
            return await update.message.reply_text("❌ Zone does not exist.")
        if p["Credits"] < 200:
            return await update.message.reply_text("❌ Need 200 credits to claim a zone.")
        p["Credits"] -= 200
        p["Zone"] = zone
        save_player(p)
        return await update.message.reply_text(f"🚩 You now control {zone}!")

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

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


  
