import os
import logging
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
    building_system,
    army_system,
    mission_system,
    battle_system,
    shop_system,
    timer_system,
)

from utils.google_sheets import (
    load_player_army,
    load_building_queue,
    get_building_level,
    load_resources,
)
from utils.ui_helpers import render_status_panel

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Env Check ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")

# ── Main Menu UI ────────────────────────────────────────
MAIN_MENU = [
    [KeyboardButton("🏗️ Buildings"), KeyboardButton("🛡️ Army")],
    [KeyboardButton("⚙️ Status"), KeyboardButton("📜 Missions")],
    [KeyboardButton("🛒 Shop"), KeyboardButton("⚔️ Battle")],
]
MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

# ── Lore ────────────────────────────────────────────────
LORE_TEXT = (
    "🌌 Year 3137.\n"
    "Humanity shattered into warring factions.\n"
    "Earth is divided. Control your empire. Conquer zones. Unlock tech.\n\n"
    "Welcome to SKYHUSTLE — The Last Empire."
)

# ── Command Handlers ────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛰️ Welcome Commander!\nUse the menu below to begin.",
        reply_markup=MENU_MARKUP
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧭 Basic Commands:\n"
        "• /tutorial - Guided Setup\n"
        "• /status - Empire Snapshot\n"
        "• /lore - Game Lore\n\n"
        "Use the menu below for fast access.",
        reply_markup=MENU_MARKUP
    )

async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LORE_TEXT, reply_markup=MENU_MARKUP)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    panel = render_status_panel(pid)
    await update.message.reply_text(panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP)
# ── Buildings UI ────────────────────────────────────────────────
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
            end_time = datetime.datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
            rem = building_system._format_timedelta(end_time - datetime.datetime.now())
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

    cost_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in cost.items())
    eff_str = ", ".join(
        f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
        for k, v in eff.items()
    ) or "(no direct effect)"

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
async def upgrade_building_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    key = query.data.split(":", 1)[1]
    now = datetime.datetime.now()

    queue = load_building_queue(pid)
    if any(t["building_name"] == key for t in queue.values()):
        return await query.edit_message_text(
            f"⚡ Already upgrading {key.replace('_',' ').title()}!",
            parse_mode=ParseMode.HTML,
        )

    cur = get_building_level(pid, key)
    nxt = cur + 1
    cost = building_system.BUILDINGS[key]["resource_cost"](nxt)
    base = building_system.BUILDINGS[key]["base_time_min"]
    mult = building_system.BUILDINGS[key]["time_multiplier"]
    upgrade_time = base * (mult ** cur)
    end_time = now + datetime.timedelta(minutes=upgrade_time)

    resources = load_resources(pid)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            return await query.edit_message_text(
                f"⚡ Not enough {res.title()} to upgrade {key.replace('_',' ').title()}!",
                parse_mode=ParseMode.HTML,
            )
        resources[res] -= amt
    save_resources(pid, resources)

    task = {
        "building_name": key,
        "level": nxt,
        "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_building_task(pid, key, task["end_time"])

    rem = building_system._format_timedelta(end_time - now)
    text = (
        f"🏗️ Upgrading {key.replace('_',' ').title()} to Lv {nxt} ({rem} left)!\n"
        "Tap below to return to building list."
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back to Buildings", callback_data="BUILDINGS")]
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

# ── Main Menu navigation ─────────────────────────────────────────
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Use the menu below to navigate:", reply_markup=MENU_MARKUP
    )
def register_handlers(app: ApplicationBuilder):
    app.add_error_handler(error_handler)

    # Core Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lore", lore))
    app.add_handler(CommandHandler("status", status))

    # Buildings
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🏗️ Buildings"), send_building_list))
    app.add_handler(CallbackQueryHandler(building_detail_callback, pattern="^BUILDING:"))
    app.add_handler(CallbackQueryHandler(upgrade_building_callback, pattern="^UPGRADE:"))
    app.add_handler(CallbackQueryHandler(send_building_list, pattern="^BUILDINGS"))
    app.add_handler(CommandHandler("build", building_system.build))
    app.add_handler(CommandHandler("buildinfo", building_system.buildinfo))
    app.add_handler(CommandHandler("buildstatus", building_system.buildstatus))

    # Army
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛡️ Army"), send_army_list))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^MAIN_MENU"))
    app.add_handler(CommandHandler("train", army_system.train_units))
    app.add_handler(CommandHandler("army", army_system.view_army))
    app.add_handler(CommandHandler("trainstatus", army_system.training_status))
    app.add_handler(CommandHandler("claimtrain", army_system.claim_training))

    # Battle
    app.add_handler(CommandHandler("attack", battle_system.attack))
    app.add_handler(CallbackQueryHandler(battle_system.attack_tactic_callback, pattern="^ATTACK_TACTIC:"))
    app.add_handler(CallbackQueryHandler(battle_system.defend_tactic_callback, pattern="^DEFEND_TACTIC:"))
    app.add_handler(CommandHandler("battle_status", battle_system.battle_status))
    app.add_handler(CommandHandler("spy", battle_system.spy))

    # Shop
    app.add_handler(CommandHandler("shop", shop_system.shop))
    app.add_handler(CommandHandler("buy", shop_system.buy))
    app.add_handler(CommandHandler("unlockblackmarket", shop_system.unlock_blackmarket))
    app.add_handler(CommandHandler("blackmarket", shop_system.blackmarket))
    app.add_handler(CommandHandler("bmbuy", shop_system.bmbuy))

    # Unknown commands fallback
    app.add_handler(
        MessageHandler(
            filters.COMMAND,
            lambda u, c: u.message.reply_text("❓ Unknown—use the menu below.", reply_markup=MENU_MARKUP),
        )
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(app)
    app.run_polling()


