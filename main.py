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
 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)
 

 async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
  logger.exception("Unhandled exception:")
  if hasattr(update, "message") and update.message:
  await update.message.reply_text("❌ Oops, something went wrong.")
 

 # ────────────────────────────────────────────────────────────────────────────────
 MAIN_MENU = [
  [KeyboardButton("🏗 Buildings"), KeyboardButton("🛡️ Army")],
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
  panel = render_status_panel(str(update.effective_user.id))
  await update.message.reply_text(
  panel, parse_mode=ParseMode.HTML, reply_markup=MENU_MARKUP
  )
 

 # ────────────────────────────────────────────────────────────────────────────────
 # Tutorial handlers (highest priority)
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
  for key in building_system.BUILDING_DATA:
  lvl = get_building_level(pid, key)
  busy = any(t["building_name"] == key for t in queue.values())
  label = (
  f"{building_system.BUILDING_DATA[key]['display_name']} (Lv {lvl})"
  + (" ⏳" if busy else "")
  )
  buttons.append([InlineKeyboardButton(label, callback_data=f"BUILDING:{key}")])
  text = "🏗 <b>Your Buildings</b>\nChoose one for details:"
  return text, InlineKeyboardMarkup(buttons)
 

 async def send_building_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
  pid = str(update.effective_user.id)
  text, markup = _make_building_list(pid)
  await update.message.reply_text(
  text, parse_mode=ParseMode.HTML, reply_markup=markup
  )
 

 async def building_detail_callback(
  update: Update, context: ContextTypes.DEFAULT_TYPE
 ):
  query = update.callback_query
  await query.answer()
  pid = str(query.from_user.id)
  key = query.data.split(":", 1)[1]
 

  # If already upgrading, show remaining time + back
  queue = load_building_queue(pid)
  for task in queue.values():
  if task["building_name"] == key:
  end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
  rem = end_time - datetime.now()
  text = (
  f"🏗️ <b>{building_system.BUILDING_DATA[key]['display_name']}</b>\n"
  f"• Current Lv: {get_building_level(pid, key)} (Upgrading: {rem} left)\n\n"
  "« Back to list"
  )
  markup = InlineKeyboardMarkup([
  [InlineKeyboardButton("« Back", callback_data="BUILDING:__back__")]
  ])
  return await query.edit_message_text(
  text, parse_mode=ParseMode.HTML, reply_markup=markup
  )
 

  # Otherwise show detail + upgrade button
  cur = get_building_level(pid, key)
  nxt = cur + 1
  cost = building_system.calculate_building_cost(key, nxt)
  eff = building_system.get_building_effect(key, nxt) or {}
  cost_str = " | ".join(f"{k.title()}: {v}" for k, v in cost.items())
  eff_str = ", ".join(
  f"{k.replace('_',' ').title()}: {v}{'%' if 'pct' in k else ''}"
  for k, v in eff.items()
  ) or "(no direct effect)"
  text = (
  f"🏗️ <b>{building_system.BUILDING_DATA[key]['display_name']}</b>\n"
  f"• Current Lv: {cur}\n"
  f"• Next Lv: {nxt}\n"
  f"• Cost: {cost_str}\n"
  f"• Effect: {eff_str}\n\n"
  "Tap ⬆️ to upgrade or « Back to return."
  )
  markup = InlineKeyboardMarkup(
  [
  [
  InlineKeyboardButton(
  "⬆️ Upgrade", callback_data=f"BUILDING_UPGRADE:{key}"
  ),
  InlineKeyboardButton("« Back", callback_data="BUILDING:__back__"),
  ]
  ]
  )
  await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
 

 async def building_back_callback(
  update: Update, context: ContextTypes.DEFAULT_TYPE
 ):
  query = update.callback_query
  await query.answer()
  pid = str(query.from_user.id)
  text, markup = _make_building_list(pid)
  await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
 

 async def building_upgrade_callback(
  update: Update, context: ContextTypes.DEFAULT_TYPE
 ):
  query = update.callback_query
  await query.answer()
  pid = str(query.from_user.id)
  key = query.data.split(":", 1)[1]
  await building_system.build(update, context, building_name=key)
  text, markup = _make_building_list(pid)
  await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
 

 # ────────────────────────────────────────────────────────────────────────────────
 # Main app
 

 if __name__ == '__main__':
  app = ApplicationBuilder().token(BOT_TOKEN).build()
 

  # Error handler
  app.add_error_handler(error_handler)
 

  # Main commands
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("help", help_cmd))
  app.add_handler(CommandHandler("lore", lore))
  app.add_handler(CommandHandler("status", status))
 

  # Tutorial commands
  for h in TUTORIAL_HANDLERS:
  app.add_handler(h)
 

  # Building commands
  app.add_handler(MessageHandler(filters.Regex("^\U0001F3D7 Buildings$"), send_building_list))
  app.add_handler(CallbackQueryHandler(building_detail_callback, pattern="^BUILDING:(?!__back__).*"))
  app.add_handler(CallbackQueryHandler(building_back_callback, pattern="^BUILDING:__back__$"))
  app.add_handler(CallbackQueryHandler(building_upgrade_callback, pattern="^BUILDING_UPGRADE:.*"))
  app.add_handler(CommandHandler("build", building_system.build))
  app.add_handler(CommandHandler("buildstatus", building_system.buildstatus))
  app.add_handler(CommandHandler("buildinfo", building_system.buildinfo))
 

  # Timer commands
  app.add_handler(CommandHandler("mine", timer_system.start_mining))
  app.add_handler(CommandHandler("minestatus", timer_system.mining_status))
  app.add_handler(CommandHandler("claimmine", timer_system.claim_mining))
 

  # Army commands
  app.add_handler(CommandHandler("train", army_system.train_units))
  app.add_handler(CommandHandler("army", army_system.view_army))
  app.add_handler(CommandHandler("trainstatus", army_system.training_status))
  app.add_handler(CommandHandler("claimtrain", army_system.claim_training))
 

  # Battle commands
  app.add_handler(CommandHandler("attack", battle_system.attack))
  app.add_handler(CommandHandler("battlestatus", battle_system.battle_status))
  app.add_handler(CommandHandler("spy", battle_system.spy))
 

  # Shop commands
  app.add_handler(CommandHandler("shop", shop_system.shop))
  app.add_handler(CommandHandler("buy", shop_system.buy))
  app.add_handler(
  CommandHandler("unlockblackmarket", shop_system.unlock_blackmarket)
  )
  app.add_handler(CommandHandler("blackmarket", shop_system.blackmarket))
  app.add_handler(CommandHandler("bmbuy", shop_system.bmbuy))
 

  # Unknown fallback
  app.add_handler(
  MessageHandler(
  filters.COMMAND,
  lambda u, c: u.message.reply_text(
  "❓ Unknown—use the menu below.", reply_markup=MENU_MARKUP
  ),
  )
  )
 

  # Start the bot
  app.run_polling()
