from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from modules.sheets_helper import get_player_data, update_player_data


async def research_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # support both /research and inline button
    if update.callback_query:
        await update.callback_query.answer()
        chat_id = update.effective_chat.id
    else:
        chat_id = update.effective_message.chat_id

    data = get_player_data(update.effective_user.id)
    if not data:
        await context.bot.send_message(chat_id, "❌ Send /start first.")
        return

    text = (
        "🧪 *[RESEARCH LAB]*\n"
        "Choose a tech branch:\n\n"
        "📈 Military Tech\n"
        "🏦 Economy Tech\n"
        "⚡ Advanced Tech"
    )
    buttons = [
        [InlineKeyboardButton("📈 Military Tech", callback_data="RESEARCH_MILITARY")],
        [InlineKeyboardButton("🏦 Economy Tech",  callback_data="RESEARCH_ECONOMY")],
        [InlineKeyboardButton("⚡ Advanced Tech", callback_data="RESEARCH_ADVANCED")],
        [InlineKeyboardButton("🏠 Back to Base",   callback_data="RESEARCH_CANCEL")],
    ]
    await context.bot.send_message(
        chat_id, text, parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def research_branch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    branch = query.data.split("_")[1].lower()  # "military","economy","advanced"
    techs = {
        "military": [
            {"key":"infantry_attack","name":"Infantry Attack I","req":"Barracks Lv 2","cost":"100 Food,50 Gold","time":"10m"},
            {"key":"tank_defense",   "name":"Tank Defense I",   "req":"Barracks Lv 3","cost":"120 Food,60 Gold","time":"15m"},
        ],
        "economy": [
            {"key":"wood_boost","name":"Wood Production I", "req":"Lumber Lv 2","cost":"80 Wood,40 Gold","time":"10m"},
            {"key":"stone_boost","name":"Stone Production I","req":"Mine Lv 2",   "cost":"80 Stone,40 Gold","time":"10m"},
        ],
        "advanced": [
            {"key":"recruit_speed","name":"Training Speed I", "req":"Research Lv 2","cost":"200 Food,100 Gold","time":"20m"},
        ],
    }
    items = techs[branch]
    lines = [f"🧪 *[{branch.capitalize()} Tech Tree]*"]
    for t in items:
        lines.append(f"• *{t['name']}* — Req: {t['req']} — Cost: {t['cost']} — Time: {t['time']}")
    text = "\n".join(lines)
    buttons = [[InlineKeyboardButton(t["name"], callback_data=f"RESEARCH_START_{t['key']}")] for t in items]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="RESEARCH_MENU")])
    await query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))

async def research_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    key = query.data.split("_",2)[2]
    chat_id = update.effective_chat.id
    data = get_player_data(update.effective_user.id)
    tech_map = {
        "infantry_attack":{"name":"Infantry Attack I","food":100,"gold":50,"time":10},
        "tank_defense":   {"name":"Tank Defense I",   "food":120,"gold":60,"time":15},
        "wood_boost":     {"name":"Wood Production I","wood":80, "gold":40,"time":10},
        "stone_boost":    {"name":"Stone Production I","stone":80,"gold":40,"time":10},
        "recruit_speed":  {"name":"Training Speed I", "food":200,"gold":100,"time":20},
    }
    tech = tech_map[key]
    # check & deduct each resource if present
    for r in ("food","gold","wood","stone"):
        if tech.get(r) and data[f"resources_{r}"] < tech[r]:
            await query.edit_message_text("❌ Not enough resources.", parse_mode=constants.ParseMode.MARKDOWN)
            return
    for r in ("food","gold","wood","stone"):
        if tech.get(r):
            update_player_data(update.effective_user.id, f"resources_{r}", data[f"resources_{r}"] - tech[r])
    await query.edit_message_text(
        f"🧪 Research *{tech['name']}* started!\n⏱️ It will complete in {tech['time']} minutes.",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def cancel_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await context.bot.send_message(update.effective_chat.id, "❌ Research cancelled.")

def setup_research_system(app: Application) -> None:
    app.add_handler(CommandHandler("research", research_menu))
    app.add_handler(CallbackQueryHandler(research_menu,    pattern="^RESEARCH_MENU$"))
    app.add_handler(CallbackQueryHandler(research_branch,  pattern="^RESEARCH_(MILITARY|ECONOMY|ADVANCED)$"))
    app.add_handler(CallbackQueryHandler(research_start,   pattern="^RESEARCH_START_"))
    app.add_handler(CallbackQueryHandler(cancel_research, pattern="^RESEARCH_CANCEL$")) 