# admin_tools_system.py (Part 1)

import os
import time
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from telegram.helpers import escape_markdown
from telegram.error import BadRequest

from utils.google_sheets import (
    save_resources,
    load_resources,
    save_player_army,
    load_player_army,
    save_building_level,
    get_building_level,
    load_building_queue,
    buildings_ws,
    army_ws,
    resources_ws,
    training_ws,
    building_queue_ws,
    purchases_ws,
    get_worksheet,
)

# ── Admin Setup ─────────────────────────────────────────────────────
ADMIN_IDS = {
    "yanny": 7737016510  # Replace with your actual Telegram user ID
}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS.values()

# ── Give Resources ───────────────────────────────────────────────────
async def give_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 3:
        return await update.message.reply_text("Usage: ,give_resource [player_id] [resource] [amount]")

    pid, resource, amount = context.args
    try:
        amount = int(amount)
        res = load_resources(pid)
        res[resource] = res.get(resource, 0) + amount
        save_resources(pid, res)
        await update.message.reply_text(f"✅ Gave {amount} {resource} to {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ── Take Resources ───────────────────────────────────────────────────
async def take_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 3:
        return await update.message.reply_text("Usage: ,take_resource [player_id] [resource] [amount]")

    pid, resource, amount = context.args
    try:
        amount = int(amount)
        res = load_resources(pid)
        res[resource] = max(0, res.get(resource, 0) - amount)
        save_resources(pid, res)
        await update.message.reply_text(f"✅ Took {amount} {resource} from {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# admin_tools_system.py (Part 2)

# ── Give Units ──────────────────────────────────────────────────────
async def give_units(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 3:
        return await update.message.reply_text("Usage: ,give_unit [player_id] [unit] [amount]")

    pid, unit, amount = context.args
    try:
        amount = int(amount)
        army = load_player_army(pid)
        army[unit] = army.get(unit, 0) + amount
        save_player_army(pid, army)
        await update.message.reply_text(f"✅ Gave {amount} {unit} to {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ── Set Building Level ──────────────────────────────────────────────
async def set_building_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 3:
        return await update.message.reply_text("Usage: ,set_building [player_id] [building] [level]")

    pid, building, level = context.args
    try:
        level = int(level)
        save_building_level(pid, building, level)
        await update.message.reply_text(f"✅ Set {building} to Level {level} for {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ── Wipe Player Data (Single Sheets) ────────────────────────────────
def _wipe_from_ws(ws, pid: str, col_name: str = "player_id"):
    records = ws.get_all_records()
    col_idx = 1
    headers = ws.row_values(1)
    for i, h in enumerate(headers):
        if h == col_name:
            col_idx = i + 1
            break
    cells = ws.findall(pid, in_column=col_idx)
    for cell in reversed(cells):
        ws.delete_row(cell.row)

async def wipe_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: ,wipe_player [player_id]")

    pid = context.args[0]
    try:
        for ws in [resources_ws, buildings_ws, army_ws, training_ws, building_queue_ws]:
            _wipe_from_ws(ws, pid)
        await update.message.reply_text(f"✅ Wiped all data for {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error wiping data: {str(e)}")

# admin_tools_system.py (Part 3)

# ── Give Premium Item ───────────────────────────────────────────────
async def give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 2:
        return await update.message.reply_text("Usage: ,give_premium [player_id] [item_id]")

    pid, item_id = context.args
    try:
        purchases_ws.append_row([pid, item_id, 1, str(int(time.time()))])
        await update.message.reply_text(f"✅ Gave {item_id} to {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to assign item: {str(e)}")

# ── Reset Player Resources ──────────────────────────────────────────
async def reset_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if len(context.args) != 1:
        return await update.message.reply_text("Usage: ,reset_resources [player_id]")

    pid = context.args[0]
    try:
        save_resources(pid, {"metal": 0, "fuel": 0, "crystal": 0, "credits": 0})
        await update.message.reply_text(f"✅ Reset all resources for {pid}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error resetting resources: {str(e)}")

# ── List Players ────────────────────────────────────────────────────
async def list_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    try:
        rows = resources_ws.get_all_records()
        if not rows:
            return await update.message.reply_text("No players found.")

        lines = []
        for row in rows:
            pid = row.get("player_id")
            metal = row.get("metal", 0)
            credits = row.get("credits", 0)
            lines.append(f"• ID: {pid} | 💠 Metal: {metal} | 💳 Credits: {credits}")

        message = "\n".join(lines[:50])
        await update.message.reply_text(f"<b>📋 Player Summary:</b>\n{message}", parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error listing players: {str(e)}")

# admin_tools_system.py (Part 4)

# ── Broadcast Message ───────────────────────────────────────────────
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")

    if not context.args:
        return await update.message.reply_text("Usage: ,broadcast [message]")

    msg = " ".join(context.args)
    rows = resources_ws.get_all_records()
    success, fail = 0, 0

    for row in rows:
        pid = row.get("player_id")
        try:
            await context.bot.send_message(chat_id=pid, text=f"📢 {msg}")
            success += 1
        except BadRequest:
            fail += 1

    await update.message.reply_text(f"✅ Broadcast sent to {success} users. ❌ Failed: {fail}")

# ── Wipe All Player Data (All Sheets) ───────────────────────────────
async def wipe_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: ,wipe [player_id]")

    target_id = context.args[0]
    deleted = 0
    try:
        for ws in [resources_ws, buildings_ws, training_ws, army_ws, building_queue_ws, purchases_ws]:
            for cell in ws.findall(str(target_id)):
                ws.delete_row(cell.row)
                deleted += 1
        await update.message.reply_text(f"✅ Wiped player {target_id} ({deleted} entries removed)")
    except Exception as e:
        await update.message.reply_text(f"❌ Error wiping data: {str(e)}")

# ── Inspect Player ──────────────────────────────────────────────────
async def inspect_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Unauthorized.")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: ,inspect [player_id]")

    pid = context.args[0]
    try:
        res = load_resources(pid)
        army = load_player_army(pid)
        bq = load_building_queue(pid)

        lines = [f"<b>🧾 Player {pid} Summary</b>"]
        lines.append(f"<b>Resources:</b> {res}")
        lines.append(f"<b>Army:</b> {army}")
        lines.append(f"<b>Build Queue:</b> {list(bq.keys())}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error inspecting player: {str(e)}")
# admin_tools_system.py (Part 5)

# ── Register Admin Tools ────────────────────────────────────────────
def register_admin_tools(app: ApplicationBuilder):
    app.add_handler(CommandHandler("give_resource", give_resources))
    app.add_handler(CommandHandler("take_resource", take_resources))
    app.add_handler(CommandHandler("give_unit", give_units))
    app.add_handler(CommandHandler("set_building", set_building_level))
    app.add_handler(CommandHandler("give_premium", give_premium))
    app.add_handler(CommandHandler("reset_resources", reset_resources))
    app.add_handler(CommandHandler("wipe_player", wipe_player))
    app.add_handler(CommandHandler("list_players", list_players))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("wipe", wipe_data))
    app.add_handler(CommandHandler("inspect", inspect_player))

# ── Admin Audit Logger ──────────────────────────────────────────────
def log_admin_action(admin_id, action: str, target_id: str, details: str = ""):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audit_ws = get_worksheet("admin_audit")
        audit_ws.append_row([admin_id, action, target_id, details, timestamp])
    except Exception as e:
        print(f"⚠️ Audit log failed: {e}")
