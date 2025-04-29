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
)
from utils.ui_helpers import render_status_panel

# ────────────────────────────────────────────────────────────────────────────────
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception:")
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("❌ Oops, something went wrong.")

# ────────────────────────────────────────────────────────────────────────────────
# Persistent Reply Keyboard
MAIN_MENU = [
    [KeyboardButton("🏗 Buildings"), KeyboardButton("🛡️ Army")],
    [KeyboardButton("⚙️ Status"),    KeyboardButton("📜 Missions")],
    [KeyboardButton("🛒 Shop"),       KeyboardButton("⚔️ Battle")],
]
MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

# ────────────────────────────────────────────────────────────────────────────────
# Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")

# ────────────────────────────────────────────────────────────────────────────────
# /start, /help, /lore, /status
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
        "🔹 /status   — Empire snapshot\n"
        "🔹 /lore     — Backstory\n\n"
        "Or tap the menu below:",
        reply_markup=MENU_MARKUP
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT, reply_markup=MENU_MARKUP)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panel = render_status_panel(str(update.effective_user.id))
    await update.message.reply_text(
        panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP
    )

# ────────────────────────────────────────────────────────────────────────────────
# Tutorial flows (highest priority)
TUTORIAL_HANDLERS = [
    CommandHandler("tutorial",    tutorial_system.tutorial),
    CommandHandler("setname",     tutorial_system.setname),
    CommandHandler("ready",       tutorial_system.ready),
    CommandHandler("build",       tutorial_system.build),
    CommandHandler("mine",        tutorial_system.tutorial_mine),
    CommandHandler("minestatus",  tutorial_system.tutorial_mine_status),
    CommandHandler("claimmine",   tutorial_system.tutorial_claim_mine),
    CommandHandler("train",       tutorial_system.tutorial_train),
    CommandHandler("trainstatus", tutorial_system.tutorial_trainstatus),
    CommandHandler("claimtrain",  tutorial_system.tutorial_claim_train),
]

# ────────────────────────────────────────────────────────────────────────────────
# BUILDING LIST & DETAILS

def _make_building_list(pid: str):
    """Return (text, markup) for the building list menu."""
    queue = load_building_queue(pid)
    buttons = []
    for key in building_system.BUILDINGS:
        lvl  = get_building_level(pid, key)
        busy = any(t['building_name']==key for t in queue.values())
        label = f"{key.replace('_',' ').title()} (Lv {lvl})" + (" ⏳" if busy else "")
        buttons.append([InlineKeyboardButton(label, callback_data=f"BUILDING:{key}")])
    text = "🏗 <b>Your Buildings</b>\nChoose one for details:"
    return text, InlineKeyboardMarkup(buttons)

async def send_building_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    text, markup = _make_building_list(pid)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def building_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":",1)[1]

    # — If already upgrading, show remaining time and only a Back button —
    queue = load_building_queue(pid)
    for task in queue.values():
        if task['building_name'] == key:
            end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
            rem = building_system._format_timedelta(end_time - datetime.now())
            text = (
                f"🏗️ <b>{key.replace('_',' ').title()}</b>\n"
                f"• Current Lv: {get_building_level(pid, key)} (Upgrading: {rem} left)\n\n"
                "« Back to list"
            )
            markup = InlineKeyboardMarkup([
                [ InlineKeyboardButton("« Back", callback_data="BUILDING:__back__") ]
            ])
            return await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

    # — Otherwise, show normal detail & Upgrade button —
    cur = get_building_level(pid, key)
    nxt = cur + 1
    cost = building_system.BUILDINGS[key]["resource_cost"](nxt)
    eff  = building_system.BUILDINGS[key]["effect"](nxt) or {}
    cost_str = " | ".join(f"{k.title()}: {v}" for k,v in cost.items())
    eff_str  = ", ".join(
        f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
        for k,v in eff.items()
    ) or "(no direct effect)"

    text = (
        f"🏗️ <b>{key.replace('_',' ').title()}</b>\n"
        f"• Current Lv: {cur}\n"
        f"• Next Lv:    {nxt}\n"
        f"• Cost:       {cost_str}\n"
        f"• Effect:     {eff_str}\n\n"
        "Tap ⬆️ to upgrade or « Back to return."
    )
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬆️ Upgrade", callback_data=f"BUILDING_UPGRADE:{key}"),
            InlineKeyboardButton("« Back",    callback_data="BUILDING:__back__"),
        ]
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def building_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    text, markup = _make_building_list(pid)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def building_upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":",1)[1]

    # —— Inline build logic ——
    cur_lv = get_building_level(pid, key)
    nxt_lv = cur_lv + 1
    cost   = building_system.BUILDINGS[key]["resource_cost"](nxt_lv)
    res    = load_resources(pid)

    # Check resources
    for r, amt in cost.items():
        if res.get(r, 0) < amt:
            return await query.answer(
                f"❌ Not enough {r.title()}: need {amt}, have {res.get(r,0)}",
                show_alert=True
            )

    # Deduct & save
    for r, amt in cost.items():
        res[r] -= amt
    save_resources(pid, res)

    # Schedule upgrade
    base    = building_system.BUILDINGS[key]["base_time"]
    mult    = building_system.BUILDINGS[key]["time_mult"]
    minutes = int(base * (mult ** cur_lv))
    ready_at = datetime.now() + timedelta(minutes=minutes)
    building_system.save_building_task(pid, key, datetime.now(), ready_at)

    # Acknowledge & refresh detail to show “Upgrading”
    await query.answer(f"🔨 Upgrading to Lv {nxt_lv}!")
    await building_detail_callback(update, context)

# ────────────────────────────────────────────────────────────────────────────────
# Main menu router for reply‐keyboard
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    pid  = str(update.effective_user.id)

    if text == "🏗 Buildings":
        return await send_building_list(update, context)

    if text == "🛡️ Army":
        army = load_player_army(pid)
        if not army:
            msg = "🛡️ Your army is empty.\nUse /train [unit] [amount]."
        else:
            lines = [f"• {u.title()}: {q}" for u,q in army.items()]
            msg = "<b>🛡️ Your Army</b>\n" + "\n".join(lines)
        return await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)

    if text == "⚙️ Status":
        return await status(update, context)

    if text == "📜 Missions":
        return await update.message.reply_text("Use /missions to view missions.", reply_markup=MENU_MARKUP)

    if text == "🛒 Shop":
        return await update.message.reply_text("Use /shop to browse.", reply_markup=MENU_MARKUP)

    if text == "⚔️ Battle":
        return await update.message.reply_text("Use /attack or /battle_status.", reply_markup=MENU_MARKUP)

# ────────────────────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tutorial
    for h in TUTORIAL_HANDLERS:
        app.add_handler(h)

    # Core
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("lore",   lore))
    app.add_handler(CommandHandler("status", status))

    # Reply‐keyboard menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))

    # Inline building callbacks
    app.add_handler(CallbackQueryHandler(building_detail_callback, pattern="^BUILDING:[^_].+"))
    app.add_handler(CallbackQueryHandler(building_back_callback,   pattern="^BUILDING:__back__$"))
    app.add_handler(CallbackQueryHandler(building_upgrade_callback,pattern="^BUILDING_UPGRADE:.+"))

    # Fallback commands
    app.add_handler(CommandHandler("build",       building_system.build))
    app.add_handler(CommandHandler("buildinfo",   building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus", building_system.buildstatus))
    app.add_handler(CommandHandler("mine",        timer_system.start_mining))
    app.add_handler(CommandHandler("minestatus",  timer_system.mining_status))
    app.add_handler(CommandHandler("claimmine",   timer_system.claim_mining))
    app.add_handler(CommandHandler("train",       army_system.train_units))
    app.add_handler(CommandHandler("army",        army_system.view_army))
    app.add_handler(CommandHandler("trainstatus", army_system.training_status))
    app.add_handler(CommandHandler("claimtrain",  army_system.claim_training))
    app.add_handler(CommandHandler("missions",      mission_system.missions))
    app.add_handler(CommandHandler("storymissions", mission_system.storymissions))
    app.add_handler(CommandHandler("epicmissions",  mission_system.epicmissions))
    app.add_handler(CommandHandler("claimmission",  mission_system.claimmission))
    app.add_handler(CommandHandler("attack",         battle_system.attack))
    app.add_handler(CommandHandler("battle_status",  battle_system.battle_status))
    app.add_handler(CommandHandler("spy",            battle_system.spy))
    app.add_handler(CommandHandler("shop",            shop_system.shop))
    app.add_handler(CommandHandler("buy",             shop_system.buy))
    app.add_handler(CommandHandler("unlockblackmarket", shop_system.unlock_blackmarket))
    app.add_handler(CommandHandler("blackmarket",       shop_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy",             shop_system.bmbuy))

    # Unknown /fallback
    app.add_handler(MessageHandler(filters.COMMAND,
        lambda u,c: u.message.reply_text("❓ Unknown—use the menu below.", reply_markup=MENU_MARKUP)
    ))

    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
