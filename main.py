import os
import logging
from datetime import datetime, timedelta

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from systems import (
    tutorial_system,
    timer_system,
    army_system,
    battle_system,
    mission_system,
    shop_system,
    building_system,
)
from utils.google_sheets import (
    load_player_army,
    load_building_queue,
    get_building_level,
    load_resources,
    save_resources,
    save_building_task,
)
from utils.ui_helpers import render_status_panel

# ────────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception:")
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("❌ Oops, something went wrong.")

MAIN_MENU = [
    [KeyboardButton("🏗️ Buildings"), KeyboardButton("🛡️ Army")],
    [KeyboardButton("⚙️ Status"), KeyboardButton("📜 Missions")],
    [KeyboardButton("🛒 Shop"), KeyboardButton("⚔️ Battle")],
]
MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")

LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions...\n"
    "Welcome to SKYHUSTLE."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\nUse the menu below to navigate.",
        reply_markup=MENU_MARKUP
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔹 /tutorial — Guided setup\n"
        "🔹 /status — Empire snapshot\n"
        "🔹 /lore — Backstory\n\n"
        "Or tap the menu below:",
        reply_markup=MENU_MARKUP
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT, reply_markup=MENU_MARKUP)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    await update.message.reply_text(
        panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP
    )
# ────────────────────────────────────────────────────────────────────────────────
TUTORIAL_HANDLERS = [
    CommandHandler("tutorial", tutorial_system.tutorial),
    CommandHandler("setname", tutorial_system.setname),
    CommandHandler("ready", tutorial_system.ready),
    CommandHandler("build", tutorial_system.build),
    CommandHandler("mine", timer_system.start_mining),
    CommandHandler("minestatus", timer_system.mining_status),
    CommandHandler("claimmine", timer_system.claim_mining),
    CommandHandler("train", army_system.train_units),
    CommandHandler("trainstatus", army_system.training_status),
    CommandHandler("claimtrain", army_system.claim_training),
]

# ────────────────────────────────────────────────────────────────────────────────
# Buildings menu & callbacks

def _make_building_list(pid: str):
    queue = load_building_queue(pid)
    buttons = []
    for key in building_system.BUILDINGS:
        lvl = get_building_level(pid, key)
        busy = any(t["building_name"] == key for t in queue.values())
        label = f"{key.replace('_', ' ').title()} (Lv {lvl})" + (" ⏳" if busy else "")
        buttons.append([InlineKeyboardButton(label, callback_data=f"BUILDING:{key}")])
    text = "🏗️ <b>Your Buildings</b>\nChoose one for details:"
    return text, InlineKeyboardMarkup(buttons)

async def send_building_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    text, markup = _make_building_list(pid)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def building_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":", 1)[1]

    queue = load_building_queue(pid)
    for task in queue.values():
        if task["building_name"] == key:
            end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
            rem = building_system._format_timedelta(end_time - datetime.now())
            text = (
                f"🏗️ <b>{key.replace('_',' ').title()}</b>\n"
                f"• Current Lv: {get_building_level(pid, key)} (Upgrading: {rem} left)\n\n"
                "Tap below to return to building list."
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back to Buildings", callback_data="BUILDINGS")]
            ])
            return await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

    cur = get_building_level(pid, key)
    nxt = cur + 1
    cost = building_system.BUILDINGS[key]["resource_cost"](nxt)
    eff = building_system.BUILDINGS[key]["effect"](nxt)

    cost_str = " | ".join(f"{k.title()}: {v}" for k, v in cost.items())
    eff_str = ", ".join(f"{k.replace('_',' ').title()}: {v}" for k, v in eff.items()) or "(no effect)"

    text = (
        f"🏗️ <b>{key.replace('_',' ').title()}</b>\n"
        f"• Current Lv: {cur}\n• Next Lv: {nxt}\n"
        f"• Cost: {cost_str}\n• Effect: {eff_str}\n\n"
        "Tap below to upgrade or return to building list."
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Upgrade to Lv {nxt}", callback_data=f"UPGRADE:{key}")],
        [InlineKeyboardButton("« Back to Buildings", callback_data="BUILDINGS")],
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def _handle_building_upgrade(query: CallbackQuery, pid: str, key: str):
    queue = load_building_queue(pid)
    if any(t["building_name"] == key for t in queue.values()):
        await query.edit_message_text(
            f"⚡ Already upgrading {key.replace('_',' ').title()}!",
            parse_mode=ParseMode.HTML,
        )
        return True  # Indicate upgrade in progress

    cur = get_building_level(pid, key)
    nxt = cur + 1
    cost = building_system.BUILDINGS[key]["resource_cost"](nxt)
    base = building_system.BUILDINGS[key]["base_time_min"]
    mult = building_system.BUILDINGS[key]["time_multiplier"]
    upgrade_time = base * (mult ** cur)
    end_time = datetime.now() + timedelta(minutes=upgrade_time)

    resources = load_resources(pid)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            await query.edit_message_text(
                f"⚡ Not enough {res.title()} to upgrade!",
                parse_mode=ParseMode.HTML,
            )
            return True  # Indicate not enough resources
        resources[res] -= amt
    save_resources(pid, resources)

    task = {
        "building_name": key,
        "level": nxt,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_building_task(pid, task)

    rem = building_system._format_timedelta(end_time - datetime.now())
    text = (
        f"🏗️ Upgrading {key.replace('_',' ').title()} to Lv {nxt} ({rem} left)!\n"
        "Tap below to return to building list."
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back to Buildings", callback_data="BUILDINGS")]
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    return False # Indicate successful upgrade initiation

async def upgrade_building_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":", 1)[1]
    await _handle_building_upgrade(query, pid, key)

# ────────────────────────────────────────────────────────────────────────────────
# Army menu & callbacks

def _make_army_list(pid: str):
    army = load_player_army(pid)
    lines = ["🛡️ <b>Your Army</b>"]
    if not army:
        lines.append("You have no units. Train some!")
    else:
        for unit, count in army.items():
            lines.append(f"• {unit.title()}: {count} units")
    lines.append("\nTap below to return to the main menu.")
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back to Main Menu", callback_data="MAIN_MENU")]
    ])
    return "\n".join(lines), markup

async def send_army_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    text, markup = _make_army_list(pid)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

# ────────────────────────────────────────────────────────────────────────────────
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("lore", lore))
    application.add_handler(CommandHandler("status", status))

    # Tutorial handlers
    application.add_handlers(TUTORIAL_HANDLERS)

    # Buildings handlers
    application.add_handler(MessageHandler(filters.Regex("^🏗️ Buildings$"), send_building_list))
    application.add_handler(CallbackQueryHandler(building_detail_callback, pattern="^BUILDING:"))
    application.add_handler(CallbackQueryHandler(upgrade_building_callback, pattern="^UPGRADE:"))
    application.add_handler(CallbackQueryHandler(send_building_list, pattern="^BUILDINGS$")) # Handle back button

    # Army handlers
    application.add_handler(MessageHandler(filters.Regex("^🛡️ Army$"), send_army_list))
    application.add_handler(CallbackQueryHandler(lambda update, _: update.effective_message.reply_text("Returning to main menu.", reply_markup=MENU_MARKUP), pattern="^MAIN_MENU$")) # Handle back to main menu

    # Error handler
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
