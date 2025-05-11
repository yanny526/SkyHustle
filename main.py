import os
import logging
import json
import random
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from modules.sheets_service import SheetsService

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO
)

sheets_service = SheetsService()

AVAILABLE_UNITS = [
    {"id": "drone", "name": "Drone⚔️"},
    {"id": "mech", "name": "Mech 🤖"},
    {"id": "jet", "name": "Jet ✈️"},
]
AVAILABLE_TECHS = [
    {"id": "plasma", "name": "Plasma Weapons"},
    {"id": "shields", "name": "Energy Shields"},
]
AVAILABLE_STRUCTURES = [
    {"id": "turret", "name": "Turret 🛡️"},
    {"id": "generator", "name": "Generator ⚡"},
    {"id": "lab", "name": "Lab 🧪"},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to SkyHustle! Use /status to view your base."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player = await sheets_service.get_player(user_id)
    if not player:
        await update.message.reply_text(
            "❌ No player data found. Use /start to begin your journey."
        )
        return
    msg = (
        f"✅ *{player.get('display_name', 'Unknown Commander')}*\n"
        f"Level: {int(player.get('experience', 0)) // 100}\n"
        f"Credits: 💎 {player.get('credits', 0)}\n"
        f"Minerals: ⚙️ {player.get('minerals', 0)}\n"
        f"Energy: ⚡ {player.get('energy', 0)}\n"
        f"Skybucks: 🛡️ {player.get('skybucks', 0)}\n"
    )
    await update.message.reply_markdown_v2(msg)

async def build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    player = await sheets_service.get_player(user_id)
    if not player:
        await update.message.reply_text("❌ No player data found. Use /start to begin your journey.")
        return
    buildings = await sheets_service.get_buildings(user_id)
    build_queue = [b for b in buildings if b.get("status") == "queued"]
    if not args:
        keyboard = [
            [InlineKeyboardButton(s["name"], callback_data=json.dumps({"cmd": "build", "id": s["id"]}))]
            for s in AVAILABLE_STRUCTURES
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "ℹ️ Select a structure to build:",
            reply_markup=reply_markup
        )
        return
    structure_id = args[0]
    quantity = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    if len(build_queue) + quantity > 5:
        await update.message.reply_text("❌ Build queue limit reached (max 5).")
        return
    structure = next((s for s in AVAILABLE_STRUCTURES if s["id"] == structure_id), None)
    if not structure:
        await update.message.reply_text("❌ Invalid structure. Example: /build turret 1")
        return
    # (Stub) Resource validation for build
    for _ in range(quantity):
        await sheets_service.save_building({
            "player_id": user_id,
            "structure_id": structure_id,
            "status": "queued"
        })
    await update.message.reply_text(
        f"✅ Queued {quantity}x {structure['name']} for construction!"
    )

async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    player = await sheets_service.get_player(user_id)
    if not player:
        await update.message.reply_text("❌ No player data found. Use /start to begin your journey.")
        return
    if not args:
        keyboard = [
            [InlineKeyboardButton(u["name"], callback_data=json.dumps({"cmd": "train", "id": u["id"]}))]
            for u in AVAILABLE_UNITS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("ℹ️ Select a unit to train:", reply_markup=reply_markup)
        return
    unit_id = args[0]
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    unit = next((u for u in AVAILABLE_UNITS if u["id"] == unit_id), None)
    if not unit:
        await update.message.reply_text("❌ Invalid unit. Example: /train drone 5")
        return
    total_cost = {k: v * count for k, v in sheets_service.UNIT_COSTS[unit_id].items()}
    enough, msg = await sheets_service.deduct_resources(user_id, total_cost)
    if not enough:
        await update.message.reply_text(f"❌ {msg}")
        return
    await sheets_service.save_unit(user_id, unit_id, count)
    await update.message.reply_text(f"✅ Trained {count}x {unit['name']}!")

async def alliance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ Alliance commands: create, join, info\nExample: /alliance create SkyForce"
        )
        return
    subcmd = args[0].lower()
    if subcmd == "create":
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /alliance create <name>")
            return
        name = " ".join(args[1:])
        alliance_id, join_code = await sheets_service.create_alliance(name, user_id)
        await update.message.reply_text(f"✅ Alliance '{name}' created! Join code: `{join_code}`", parse_mode="Markdown")
    elif subcmd == "join":
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /alliance join <code>")
            return
        code = args[1]
        success, info = await sheets_service.join_alliance(user_id, code)
        if success:
            await update.message.reply_text(f"✅ Joined alliance: {info}")
        else:
            await update.message.reply_text(f"❌ {info}")
    elif subcmd == "info":
        info = await sheets_service.get_alliance_info(user_id)
        if not info:
            await update.message.reply_text("❌ You are not in an alliance.")
            return
        await update.message.reply_text(
            f"ℹ️ Alliance: *{info['name']}*\nMembers: {info['member_count']}\nJoin code: `{info['join_code']}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Unknown subcommand. Use /alliance create|join|info")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player = await sheets_service.get_player(user_id)
    if not player:
        await update.message.reply_text("❌ No player data found. Use /start to begin your journey.")
        return
    power = int(player.get("experience", 0))
    targets = await sheets_service.get_pvp_targets(user_id, power)
    if not targets:
        await update.message.reply_text("ℹ️ No suitable PvP targets found.")
        return
    msg = "ℹ️ PvP Targets:\n"
    for t in targets:
        msg += f"- {t.get('display_name', 'Unknown')} (Power: {t.get('experience', 0)}) — /attack {t['player_id']}\n"
    await update.message.reply_text(msg)

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: /attack <player_id>")
        return
    target_id = args[0]
    player = await sheets_service.get_player(user_id)
    target = await sheets_service.get_player(target_id)
    if not player or not target:
        await update.message.reply_text("❌ Invalid target.")
        return
    p_exp = int(player.get("experience", 0))
    t_exp = int(target.get("experience", 0))
    total = p_exp + t_exp
    win = random.random() < (p_exp / total) if total > 0 else True
    result = {"winner": user_id if win else target_id, "attacker": user_id, "defender": target_id}
    await sheets_service.log_attack(user_id, target_id, result)
    if win:
        await update.message.reply_text("✅ You won the battle!")
    else:
        await update.message.reply_text("❌ You lost the battle!")

async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args:
        keyboard = [
            [InlineKeyboardButton(t["name"], callback_data=json.dumps({"cmd": "research", "id": t["id"]}))]
            for t in AVAILABLE_TECHS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("ℹ️ Available techs:", reply_markup=reply_markup)
        return
    tech_id = args[0]
    tech = sheets_service.TECH_TREE.get(tech_id)
    if not tech:
        await update.message.reply_text("❌ Invalid tech. Example: /research plasma")
        return
    unlocked = await sheets_service.get_research(user_id)
    unlocked_ids = [r["tech_id"] for r in unlocked]
    for prereq in tech["prereq"]:
        if prereq not in unlocked_ids:
            await update.message.reply_text(f"❌ Prerequisite not met: {prereq}")
            return
    await sheets_service.unlock_tech(user_id, tech_id)
    await update.message.reply_text(f"✅ Researched {tech['name']}!")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player = await sheets_service.get_player(user_id)
    if not player:
        await update.message.reply_text("❌ No player data found. Use /start to begin your journey.")
        return
    daily = await sheets_service.get_daily(user_id)
    now = int(time.time())
    if daily:
        last_claimed = int(daily.get("last_claimed", 0))
        streak = int(daily.get("streak", 0))
        if now - last_claimed < 86400:
            await update.message.reply_text("ℹ️ You have already claimed your daily reward today.")
            return
        if now - last_claimed < 2 * 86400:
            streak += 1
        else:
            streak = 1
    else:
        streak = 1
    player["credits"] = int(player.get("credits", 0)) + 100 * streak
    await sheets_service.save_player(player)
    await sheets_service.update_daily(user_id, streak)
    await update.message.reply_text(f"✅ Daily reward claimed! Streak: {streak} days. +{100*streak} credits.")

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    player_achievements = await sheets_service.get_achievements(user_id)
    msg = "🏆 *Your Achievements:*\n"
    for ach in sheets_service.ACHIEVEMENT_LIST:
        pa = next((a for a in player_achievements if a["achievement_id"] == ach["id"]), None)
        status = "✅" if pa and pa.get("claimed") == "1" else "🔒"
        progress = pa["progress"] if pa else "0"
        msg += f"\n*{ach['name']}* — {ach['desc']}\nProgress: {progress} | Reward: 💎{ach['reward']} {status}"
        if pa and pa.get("claimed") != "1" and int(progress) >= 1:
            msg += f" — /claim_{ach['id']}"
        msg += "\n"
    await update.message.reply_markdown_v2(msg)

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = await sheets_service.get_active_events()
    if not events:
        await update.message.reply_text("ℹ️ No active events right now.")
        return
    keyboard = [
        [InlineKeyboardButton(e["name"], callback_data=json.dumps({"cmd": "join_event", "id": e["event_id"]}))]
        for e in events
    ]
    msg = "🎉 *Active Events:*\n"
    for e in events:
        msg += f"\n*{e['name']}* — {e['desc']}"
    await update.message.reply_markdown_v2(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = json.loads(query.data)
    if data.get("cmd") == "join_event":
        user_id = str(query.from_user.id)
        event_id = data.get("id")
        success, info = await sheets_service.join_event(user_id, event_id)
        await query.answer()
        if success:
            await query.edit_message_text(f"✅ {info}")
        else:
            await query.edit_message_text(f"❌ {info}")
    elif data.get("cmd") == "pve":
        user_id = str(query.from_user.id)
        mission_id = data.get("id")
        success, info = await sheets_service.attempt_mission(user_id, mission_id)
        await query.answer()
        if success:
            await query.edit_message_text(f"✅ {info}")
        else:
            await query.edit_message_text(f"❌ {info}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    scope = "global"
    page = 1
    if args:
        if args[0] in ["global", "alliance"]:
            scope = args[0]
        if len(args) > 1 and args[1].isdigit():
            page = int(args[1])
    user_id = str(update.effective_user.id)
    alliance_id = None
    if scope == "alliance":
        info = await sheets_service.get_alliance_info(user_id)
        if not info:
            await update.message.reply_text("❌ You are not in an alliance.")
            return
        alliance_id = info["join_code"]  # or alliance_id if you store it
    players, total = await sheets_service.get_leaderboard(scope, alliance_id, page)
    if not players:
        await update.message.reply_text("ℹ️ No players found for this leaderboard.")
        return
    msg = f"🏆 *Leaderboard* ({scope.title()}) — Page {page}\n"
    for idx, p in enumerate(players, start=1 + (page-1)*10):
        msg += f"{idx}. {p.get('display_name', 'Unknown')} — XP: {p.get('experience', 0)}\n"
    if total > page * 10:
        msg += f"\nType `/leaderboard {scope} {page+1}` for next page."
    await update.message.reply_markdown_v2(msg)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    stats = await sheets_service.get_stats()
    msg = (
        f"ℹ️ *Admin Stats:*\n"
        f"Players: {stats['players']}\n"
        f"Units: {stats['units']}\n"
        f"Alliances: {stats['alliances']}\n"
    )
    await update.message.reply_markdown_v2(msg)

async def war(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ War commands: create, join, deploy, status, results")
        return
    subcmd = args[0].lower()
    info = await sheets_service.get_alliance_info(user_id)
    if not info:
        await update.message.reply_text("❌ You must be in an alliance to use war commands.")
        return
    alliance_id = info["join_code"]  # or alliance_id if you store it
    if subcmd == "create":
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /war create <opponent_alliance_code>")
            return
        opponent_code = args[1]
        war_id = await sheets_service.create_war(alliance_id, opponent_code)
        await update.message.reply_text(f"✅ War created! War ID: {war_id}")
    elif subcmd == "status":
        wars = await sheets_service.get_active_wars(alliance_id)
        if not wars:
            await update.message.reply_text("ℹ️ No active wars for your alliance.")
            return
        msg = "⚔️ *Active Wars:*\n"
        for w in wars:
            msg += f"War ID: {w['war_id']} | Status: {w['status']}\n"
        await update.message.reply_markdown_v2(msg)
    elif subcmd == "deploy":
        if len(args) < 3:
            await update.message.reply_text("❌ Usage: /war deploy <war_id> <units>")
            return
        war_id = args[1]
        units = int(args[2])
        await sheets_service.deploy_to_war(war_id, user_id, units)
        await update.message.reply_text(f"✅ Deployed {units} units to war {war_id}!")
    elif subcmd == "results":
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /war results <war_id>")
            return
        war_id = args[1]
        status = await sheets_service.get_war_status(war_id)
        if not status:
            await update.message.reply_text("❌ War not found.")
            return
        msg = f"⚔️ *War {war_id} Status:*\n"
        msg += f"Status: {status['war']['status']}\n"
        msg += "Deployments:\n"
        for d in status["deployments"]:
            msg += f"- Player {d['player_id']}: {d['units_committed']} units\n"
        await update.message.reply_markdown_v2(msg)
    else:
        await update.message.reply_text("❌ Unknown subcommand. Use /war create|status|deploy|results")

async def pve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    missions = await sheets_service.get_active_missions()
    if not missions:
        await update.message.reply_text("ℹ️ No active missions right now.")
        return
    keyboard = [
        [InlineKeyboardButton(m["name"], callback_data=json.dumps({"cmd": "pve", "id": m["mission_id"]}))]
        for m in missions
    ]
    msg = "🛰️ *PvE Missions:*\n"
    for m in missions:
        msg += f"\n*{m['name']}* — {m['desc']} (Reward: 💎{m['reward']})"
    await update.message.reply_markdown_v2(msg, reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in environment variables.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("build", build))
    app.add_handler(CommandHandler("train", train))
    app.add_handler(CommandHandler("alliance", alliance))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("research", research))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("war", war))
    app.add_handler(CommandHandler("pve", pve))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.run_polling()
