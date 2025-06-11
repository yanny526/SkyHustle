# modules/zone_system.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, Application
from modules.sheets_helper import get_player_data, list_all_players, update_player_data
from datetime import datetime, timedelta

# callback data prefixes
ZONE_CB = "ZONE_"

# Define zones with their properties
ZONES = [
    {"id":"greenvale","name":"🌲 Greenvale","def":4000,"bonus":"+10% Wood","controlled_by":None},
    {"id":"stonecrack","name":"🪨 Stonecrack","def":4500,"bonus":"+10% Stone","controlled_by":None},
    {"id":"riverbend","name":"🌊 Riverbend","def":3800,"bonus":"+10% Food","controlled_by":None},
    {"id":"goldmine","name":"💰 Goldmine","def":5000,"bonus":"+10% Gold","controlled_by":None},
    {"id":"ironpeak","name":"🔩 Ironpeak","def":4200,"bonus":"+10% Iron","controlled_by":None},
    {"id":"crystalcaverns","name":"💎 Crystal Caverns","def":4800,"bonus":"+10% Diamonds","controlled_by":None},
    {"id":"barrenlands","name":"🏜️ Barren Lands","def":3500,"bonus":"+5% XP","controlled_by":None},
    {"id":"whisperingwoods","name":"🌳 Whispering Woods","def":3700,"bonus":"+5% Energy","controlled_by":None},
    {"id":"shadowfen","name":"🌑 Shadowfen","def":4100,"bonus":"+5% Power","controlled_by":None},
    {"id":"sunstoneplateau","name":"☀️ Sunstone Plateau","def":4300,"bonus":"+5% Prestige","controlled_by":None},
    {"id":"frostbitemountains","name":"🏔️ Frostbite Mountains","def":4600,"bonus":"+10% Building Speed","controlled_by":None},
    {"id":"ancientruins","name":"🏛️ Ancient Ruins","def":4900,"bonus":"+10% Research Speed","controlled_by":None},
    {"id":"strategic_outpost1","name":"📡 Strategic Outpost Alpha","def":6000,"bonus":"Unlock Alpha Zone","controlled_by":None},
    {"id":"strategic_outpost2","name":"📡 Strategic Outpost Beta","def":6200,"bonus":"Unlock Beta Zone","controlled_by":None},
    {"id":"strategic_outpost3","name":"📡 Strategic Outpost Gamma","def":6400,"bonus":"Unlock Gamma Zone","controlled_by":None},
    {"id":"strategic_outpost4","name":"📡 Strategic Outpost Delta","def":6600,"bonus":"Unlock Delta Zone","controlled_by":None},
    {"id":"strategic_outpost5","name":"📡 Strategic Outpost Epsilon","def":6800,"bonus":"Unlock Epsilon Zone","controlled_by":None},
    {"id":"strategic_outpost6","name":"📡 Strategic Outpost Zeta","def":7000,"bonus":"Unlock Zeta Zone","controlled_by":None},
    {"id":"radiation_zone1","name":"☣️ Radiation Zone I","def":7500,"bonus":"Unique Resource A","controlled_by":None,"requirement":"5 Hazmat Masks"},
    {"id":"radiation_zone2","name":"☣️ Radiation Zone II","def":7800,"bonus":"Unique Resource B","controlled_by":None,"requirement":"5 Hazmat Masks"},
    {"id":"radiation_zone3","name":"☣️ Radiation Zone III","def":8000,"bonus":"Unique Resource C","controlled_by":None,"requirement":"5 Hazmat Masks"},
    {"id":"capital_city","name":"👑 Capital City","def":10000,"bonus":"Global Buffs","controlled_by":None},
]

def get_all_zones():
    """Get all zones with their current control status."""
    # In a real implementation, this would read from your database
    # For now, we'll just return our static zones
    return ZONES

async def zones_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the zone control menu."""
    zones = get_all_zones()
    lines = ["🌍 *[ZONE CONTROL]*",
             "Control zones to gain strategic resources and prestige.",
             "Stronger zones offer higher rewards — but tougher defenses.\n"]
    
    # Get player's alliance info
    user = update.effective_user
    player_data = get_player_data(user.id)
    alliance_name = player_data.get("alliance_name", "No Alliance")
    
    for z in zones:
        name = z["name"]
        owner = z["controlled_by"] or "Neutral"
        bonus = z["bonus"]
        dp = z["def"]
        req = z.get("requirement")
        line = f"{name} – Controlled by: [{owner}]\n" \
               f"{bonus}  🛡 Defense Power: {dp}"
        if req:
            line += f"\n*Requires:* {req}"
        lines.append(line)

    footer = "\n───────────────"
    lines.append(footer)
    
    # Add alliance info
    lines.append(f"\n📍 *Your Alliance:* [{alliance_name}]")

    # bottom buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 Zone Status", callback_data=f"{ZONE_CB}STATUS"),
            InlineKeyboardButton("🗡 Attack Zone", callback_data=f"{ZONE_CB}ATTACK")
        ],
        [
            InlineKeyboardButton("📦 Alliance Logistics", callback_data=f"{ZONE_CB}LOGISTICS"),
            InlineKeyboardButton("🏠 Back to Base", callback_data=f"{ZONE_CB}BACK")
        ]
    ]

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def zone_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /zone_attack command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    data = get_player_data(user.id)
    args = context.args
    
    if data.get("alliance_role") != "leader":
        return await context.bot.send_message(chat_id, "❌ Only alliance leaders can schedule zone attacks.")
    if not args:
        return await context.bot.send_message(chat_id, "Usage: /zone_attack <zone_id>")
        
    zid = args[0]
    zone = next((z for z in ZONES if z["id"] == zid), None)
    if not zone:
        return await context.bot.send_message(chat_id, "❌ Invalid zone ID.")
        
    # Check Hazmat for radiation zones
    if zid.startswith("radiation"):
        members = [p for p in list_all_players() if p.get("alliance_name") == data["alliance_name"]]
        have = sum(1 for m in members if m.get("items_hazmat_mask", 0) > 0)
        if have < 5:
            return await context.bot.send_message(chat_id, "❌ Need 5 Hazmat Masks across alliance.")
            
    # Schedule 6h from now
    sched = (datetime.utcnow() + timedelta(hours=6)).isoformat() + "Z"
    update_player_data(user.id, "scheduled_zone", zid)
    update_player_data(user.id, "scheduled_time", sched)
    await context.bot.send_message(chat_id, f"✅ Zone {zone['name']} attack scheduled for 6h from now.")

async def zones_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle zone menu button presses."""
    query = update.callback_query
    await query.answer()
    action = query.data.split("_",1)[1]  # STATUS, ATTACK, LOGISTICS, BACK

    if action == "STATUS":
        # simply re-show /zones
        return await zones_main(query, context)

    if action == "ATTACK":
        return await query.edit_message_text(
            "🗡 *Attack Zone*\n\n"
            "Alliance leaders can schedule a zone assault via /zone_attack\n"
            "e.g. `/zone_attack greenvale`\n\n"
            "Available zones:\n" + 
            "\n".join(f"• {z['id']} - {z['name']}" for z in ZONES) + 
            "\n\n[🏠 Back to Base]",
            parse_mode=constants.ParseMode.MARKDOWN
        )

    if action == "LOGISTICS":
        return await query.edit_message_text(
            "📦 *Alliance Logistics*\n\n"
            "Use /reinforce to send troops to allies under attack, or "
            "/donate to add to your alliance treasury.\n\n"
            "[🏠 Back to Base]",
            parse_mode=constants.ParseMode.MARKDOWN
        )

    if action == "BACK":
        # call your base_handler again
        from modules.base_ui import base_handler
        await base_handler(update, context)
        return

def setup_zone_system(app: Application):
    app.add_handler(CommandHandler("zones", zones_main))
    app.add_handler(CommandHandler("zone_attack", zone_attack))
    app.add_handler(CallbackQueryHandler(zones_callback, pattern=f"^{ZONE_CB}")) 