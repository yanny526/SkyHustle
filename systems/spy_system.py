# Spy system
# spy_system.py (Part 1 of X)

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.google_sheets import (
    load_resources,
    get_building_level,
    load_player_army,
    save_player_mission,
    save_spy_report,
    load_spy_reports,
)
from utils.ui_helpers import render_status_panel

# ── Spy Action ────────────────────────────────────────────────────────────────

async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "Usage: /spy [target_player_id]\n\n" + render_status_panel(player_id),
            parse_mode=ParseMode.HTML
        )

    target_id = context.args[0]
    if player_id == target_id:
        return await update.message.reply_text(
            "❌ You cannot spy on yourself.",
            parse_mode=ParseMode.HTML
        )

    # Load target data
    resources = load_resources(target_id)
    army = load_player_army(target_id)
    radar_level = get_building_level(target_id, "radar_station")
    detection_chance = min(20 + radar_level * 15, 95)

    # Prepare report
    now = datetime.datetime.now()
    report_id = f"{player_id}-{int(now.timestamp())}"
    summary = {
        "metal": resources.get("metal", 0),
        "fuel": resources.get("fuel", 0),
        "crystal": resources.get("crystal", 0),
        "units": army,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "detected": False,
    }

    # Spy detection check
    import random
    if random.randint(1, 100) <= detection_chance:
        summary["detected"] = True

    # Save report to Google Sheets
    save_spy_report(report_id, player_id, target_id, summary)

    # Inform player
    unit_count = sum(v for k, v in army.items() if not "_" in k)
    msg = (
        f"🕵️ You scouted <b>{target_id}</b>\n"
        f"• Metal: {summary['metal']}\n"
        f"• Fuel: {summary['fuel']}\n"
        f"• Crystal: {summary['crystal']}\n"
        f"• Units Found: {unit_count}\n\n"
    )

    if summary["detected"]:
        msg += "⚠️ You were <b>detected</b> by enemy radar!"

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
# spy_system.py (Part 2 of X)

# ── View Spy Reports ──────────────────────────────────────────────────────────

async def my_spy_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    reports = load_spy_reports(player_id)

    if not reports:
        return await update.message.reply_text("📭 You have no spy reports yet.")

    latest = sorted(reports, key=lambda r: r["timestamp"], reverse=True)[:5]
    lines = ["<b>🗂️ Latest Spy Reports</b>"]

    for rpt in latest:
        ts = rpt.get("timestamp")
        tgt = rpt.get("target_id")
        det = "❌" if rpt.get("detected") else "✅"
        metal = rpt.get("metal", 0)
        fuel = rpt.get("fuel", 0)
        crystal = rpt.get("crystal", 0)
        lines.append(
            f"🕵️ Target: {tgt} | {ts}\n"
            f"• Metal: {metal} | Fuel: {fuel} | Crystal: {crystal}\n"
            f"• Detected: {det}"
        )

    await update.message.reply_text("\n\n".join(lines), parse_mode=ParseMode.HTML)

# ── Admin Utility: Save Spy Report to Sheet ───────────────────────────────────

def save_spy_report(report_id, scout_id, target_id, summary: dict):
    from utils.google_sheets import spy_reports_ws

    spy_reports_ws.append_row([
        report_id,
        scout_id,
        target_id,
        summary["metal"],
        summary["fuel"],
        summary["crystal"],
        summary["timestamp"],
        "yes" if summary["detected"] else "no",
        json.dumps(summary["units"])
    ])

# ── Load Reports ──────────────────────────────────────────────────────────────

def load_spy_reports(player_id: str):
    try:
        from utils.google_sheets import spy_reports_ws
        recs = spy_reports_ws.get_all_records()
        return [
            {
                "report_id": r["report_id"],
                "target_id": r["target_id"],
                "timestamp": r["timestamp"],
                "metal": int(r["metal"]),
                "fuel": int(r["fuel"]),
                "crystal": int(r["crystal"]),
                "detected": r["detected"].lower() == "yes",
                "units": json.loads(r.get("units", "{}")),
            }
            for r in recs if r.get("scout_id") == player_id
        ]
    except Exception:
        return []
# spy_system.py (Part 3 of X)

# ── Premium Spy Units & Mechanics ─────────────────────────────────────────────

PREMIUM_UNITS = {
    "infinity_scout": {
        "name": "Infinity Scout",
        "detected_chance": 0.05,
        "reveal_hidden": True,
        "is_consumable": True,
        "credits_cost": 250
    },
    "hazmat_drone": {
        "name": "Hazmat Drone",
        "detected_chance": 0.10,
        "reveal_hidden": False,
        "resists_radiation": True,
        "credits_cost": 200,
        "is_consumable": True
    }
}

def get_spy_unit_details(unit_key):
    return PREMIUM_UNITS.get(unit_key)

# ── Command to Use Premium Unit ───────────────────────────────────────────────

async def use_premium_spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 2:
        return await update.message.reply_text(
            "Usage: /spyuse [unit_name] [target_id]\n"
            "Example: /spyuse infinity_scout 123456789"
        )

    unit_name, target_id = args[0], args[1]
    if unit_name not in PREMIUM_UNITS:
        return await update.message.reply_text("❌ Unknown premium spy unit.")

    unit = PREMIUM_UNITS[unit_name]
    credits = load_resources(player_id).get("credits", 0)

    if credits < unit["credits_cost"]:
        return await update.message.reply_text("💳 Not enough credits to deploy this unit.")

    # Deduct credits
    player_resources = load_resources(player_id)
    player_resources["credits"] -= unit["credits_cost"]
    save_resources(player_id, player_resources)

    # Simulate result
    detected = random.random() < unit["detected_chance"]
    fake_summary = {
        "metal": random.randint(200, 600),
        "fuel": random.randint(100, 400),
        "crystal": random.randint(50, 200),
        "units": {"infantry": 30, "tank": 5},
        "detected": detected,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    report_id = f"{player_id}-{int(datetime.datetime.now().timestamp()*1000)}"
    save_spy_report(report_id, player_id, target_id, fake_summary)

    await update.message.reply_text(
        f"✅ {unit['name']} deployed!\n"
        f"Target: {target_id}\n"
        f"Detected: {'Yes' if detected else 'No'}\n"
        f"Resources: Metal {fake_summary['metal']}, Fuel {fake_summary['fuel']}, Crystal {fake_summary['crystal']}\n"
        f"{'🕵️ Hidden units revealed!' if unit.get('reveal_hidden') else ''}",
        parse_mode=ParseMode.HTML
    )

# spy_system.py (Part 4 of X)

from telegram.ext import CommandHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

SPY_COOLDOWN_SECONDS = 180  # 3 minutes per spy

# ── Cooldown System ──────────────────────────────────────────────────────────

def spy_cooldown_ok(player_id):
    reports = load_all_spy_reports(player_id)
    if not reports:
        return True
    last_report = max(reports, key=lambda r: r["timestamp"])
    last_time = datetime.datetime.strptime(last_report["timestamp"], "%Y-%m-%d %H:%M:%S")
    return (datetime.datetime.now() - last_time).total_seconds() > SPY_COOLDOWN_SECONDS

# ── View Recent Spy Reports ──────────────────────────────────────────────────

async def view_spy_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    reports = load_all_spy_reports(player_id)

    if not reports:
        return await update.message.reply_text("🕵️ No spy reports available.")

    lines = ["<b>🛰️ Recent Spy Missions:</b>"]
    for r in sorted(reports, key=lambda x: x["timestamp"], reverse=True)[:5]:
        lines.append(
            f"• Target: {r['target_id']}, Detected: {'Yes' if r['detected'] else 'No'}, "
            f"Metal: {r['metal']}, Fuel: {r['fuel']}, Crystal: {r['crystal']} ({r['timestamp']})"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# ── Admin Utilities ───────────────────────────────────────────────────────────

ADMIN_IDS = {"123456789"}  # Replace with real admin Telegram user IDs

async def clear_all_spy_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Access denied.")
    try:
        clear_spy_logs()
        await update.message.reply_text("✅ All spy reports cleared.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error clearing reports: {e}")
# spy_system.py (Part 5 of 5)

from telegram.ext import ApplicationBuilder

# ── Helper: Risk of Detection ────────────────────────────────────────────────

def calculate_detection_chance(level: int) -> float:
    """Returns a % chance of being detected based on level of target radar station."""
    base_chance = 20  # 20% base detection risk
    per_level_increase = 15  # +15% per radar level
    return min(90, base_chance + level * per_level_increase)

# ── Register Command Handlers ────────────────────────────────────────────────

def register_spy_handlers(app: ApplicationBuilder):
    app.add_handler(CommandHandler("spy", spy_command))
    app.add_handler(CommandHandler("spyrisk", calculate_risk))
    app.add_handler(CommandHandler("spyreports", view_spy_reports))
    app.add_handler(CommandHandler("clearspies", clear_all_spy_reports))

