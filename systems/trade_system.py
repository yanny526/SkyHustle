# trade_system.py (Part 1 of X)

import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, CallbackQueryHandler

from utils.google_sheets import (
    load_resources,
    save_resources,
    trade_ws
)
from utils.ui_helpers import render_status_panel

# ── Constants ────────────────────────────────────────────────────────────────

TRADE_RESOURCES = ["metal", "fuel", "crystal"]
MAX_TRADES_PER_PLAYER = 3

# ── Trade UI Entry ───────────────────────────────────────────────────────────

async def trade_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    resources = load_resources(pid)

    msg = "<b>🛒 Trading Hub</b>\nList or exchange resources with others.\n\n"
    msg += "Your resources:\n" + "\n".join(f"• {k.title()}: {v}" for k, v in resources.items() if k in TRADE_RESOURCES)
    msg += "\n\nChoose an action below:"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Create Offer", callback_data="TRADE_CREATE")],
        [InlineKeyboardButton("📥 View Offers", callback_data="TRADE_BROWSE")],
    ])
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
# ── Handle Trade Menu Actions ────────────────────────────────────────────────

async def trade_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "TRADE_CREATE":
        await query.edit_message_text(
            "📤 What do you want to TRADE AWAY?\n(Example: metal 500)",
            parse_mode=ParseMode.HTML,
        )
        context.user_data["trade_state"] = "CREATE_FROM"
    elif action == "TRADE_BROWSE":
        await show_marketplace(update, context)


# ── Collect & Store New Trade Offer ──────────────────────────────────────────

async def trade_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    state = context.user_data.get("trade_state")

    if state == "CREATE_FROM":
        parts = update.message.text.lower().split()
        if len(parts) != 2 or parts[0] not in TRADE_RESOURCES:
            return await update.message.reply_text("⚠️ Invalid input. Try again (e.g., metal 500)")
        context.user_data["offer_from"] = (parts[0], int(parts[1]))
        context.user_data["trade_state"] = "CREATE_TO"
        return await update.message.reply_text("📥 What do you want in return? (e.g., fuel 300)")

    if state == "CREATE_TO":
        parts = update.message.text.lower().split()
        if len(parts) != 2 or parts[0] not in TRADE_RESOURCES:
            return await update.message.reply_text("⚠️ Invalid input. Try again (e.g., fuel 300)")
        offer_to = (parts[0], int(parts[1]))
        offer_from = context.user_data["offer_from"]

        trade_id = f"{pid}-{uuid.uuid4().hex[:8]}"
        trade_ws.append_row([
            trade_id, pid,
            offer_from[0], offer_from[1],
            offer_to[0], offer_to[1],
            "open"
        ])

        context.user_data.clear()
        return await update.message.reply_text("✅ Offer created and added to the marketplace.")
# ── Display Available Offers in Marketplace ────────────────────────────────────

async def show_marketplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    offers = load_open_trades()
    if not offers:
        return await update.callback_query.edit_message_text(
            "🏪 No available trades in the marketplace right now.",
            parse_mode=ParseMode.HTML
        )

    buttons = []
    for offer in offers:
        if offer["player_id"] == pid:
            continue
        label = (
            f"{offer['offer_from_amount']} {offer['offer_from_type'].capitalize()} "
            f"→ {offer['offer_to_amount']} {offer['offer_to_type'].capitalize()}"
        )
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"TRADE_ACCEPT:{offer['trade_id']}")
        ])

    buttons.append([InlineKeyboardButton("« Back", callback_data="TRADE_MENU")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        "🌐 <b>Open Trade Offers</b>\nTap an offer to accept it:",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )


# ── Accept Trade Offer ─────────────────────────────────────────────────────────

async def trade_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    trade_id = query.data.split(":", 1)[1]

    # Find trade
    offers = load_open_trades()
    offer = next((o for o in offers if o["trade_id"] == trade_id), None)
    if not offer:
        return await query.edit_message_text("⚠️ Trade offer no longer exists.")

    if offer["player_id"] == pid:
        return await query.edit_message_text("❌ You can't accept your own trade.")

    # Check buyer resources
    buyer_res = load_resources(pid)
    if buyer_res.get(offer["offer_to_type"], 0) < offer["offer_to_amount"]:
        return await query.edit_message_text("⚠️ You don't have enough resources to complete this trade.")

    # Perform trade: update both accounts
    seller_res = load_resources(offer["player_id"])

    buyer_res[offer["offer_to_type"]] -= offer["offer_to_amount"]
    buyer_res[offer["offer_from_type"]] += offer["offer_from_amount"]

    seller_res[offer["offer_to_type"]] += offer["offer_to_amount"]

    save_resources(pid, buyer_res)
    save_resources(offer["player_id"], seller_res)
    mark_trade_as_closed(trade_id)

    await query.edit_message_text("✅ Trade completed successfully.")
# ── Admin Command: Wipe All Trades (Optional Use) ──────────────────────────────

async def wipe_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != os.getenv("ADMIN_ID"):
        return await update.message.reply_text("⛔ Unauthorized.")
    
    trade_ws = get_worksheet("trades")
    records = trade_ws.get_all_records()
    for i in range(len(records)):
        trade_ws.delete_rows(2)  # Always deletes the second row (after headers)

    await update.message.reply_text("✅ All trade offers wiped.")


# ── Admin Command: Force Add Resource (for testing/debugging) ──────────────────

async def give_resource(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != os.getenv("ADMIN_ID"):
        return await update.message.reply_text("⛔ Unauthorized.")

    if len(context.args) != 3:
        return await update.message.reply_text("Usage: /give <player_id> <resource> <amount>")

    pid, res, amt = context.args
    amt = int(amt)
    resources = load_resources(pid)
    resources[res] = resources.get(res, 0) + amt
    save_resources(pid, resources)

    await update.message.reply_text(f"✅ Gave {amt} {res} to player {pid}.")


# ── Register Trade System Commands ─────────────────────────────────────────────

def register_trade_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("💱 Trade"), show_trade_menu))
    app.add_handler(CallbackQueryHandler(show_trade_menu, pattern="^TRADE_MENU$"))
    app.add_handler(CallbackQueryHandler(start_trade_offer_callback, pattern="^TRADE_OFFER$"))
    app.add_handler(CallbackQueryHandler(show_marketplace, pattern="^TRADE_MARKET$"))
    app.add_handler(CallbackQueryHandler(trade_accept_callback, pattern="^TRADE_ACCEPT:"))

    app.add_handler(CommandHandler("give", give_resource))
    app.add_handler(CommandHandler("wipe_trades", wipe_trades))


