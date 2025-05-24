"""
Premium Currency Command Handlers for SkyHustle 2
Implements /buy command and payment integration for HustleCoins
"""

from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.player_manager import PlayerManager

# Should be set in main.py after instantiation
player_manager: PlayerManager = None

PREMIUM_PACKS = [
    {'pack_id': 'pack_10', 'amount': 10, 'price': 2000, 'label': '10 HustleCoins (R20)'},
    {'pack_id': 'pack_50', 'amount': 50, 'price': 9000, 'label': '50 HustleCoins (R90)'},
    {'pack_id': 'pack_120', 'amount': 120, 'price': 20000, 'label': '120 HustleCoins (R200)'}
]

def _escape_markdown(text: str) -> str:
    special_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    message = "💎 *Buy HustleCoins*\n\nSelect a pack to purchase premium currency.\n\n"
    keyboard = []
    for pack in PREMIUM_PACKS:
        message += f"{pack['label']}\n"
        keyboard.append([
            InlineKeyboardButton(
                f"Buy {pack['amount']} HustleCoins",
                callback_data=f"buy_pack_{pack['pack_id']}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    player_id = str(query.from_user.id)
    data = query.data
    if data.startswith("buy_pack_"):
        pack_id = data.split("_")[-1]
        pack = next((p for p in PREMIUM_PACKS if p['pack_id'] == pack_id), None)
        if not pack:
            await query.answer()
            await query.edit_message_text(_escape_markdown("Pack not found."), parse_mode='MarkdownV2')
            return
        # Send invoice
        title = f"Buy {pack['amount']} HustleCoins"
        description = _escape_markdown(f"{pack['amount']} HustleCoins for SkyHustle 2.")
        payload = f"hustlecoins_{pack_id}_{player_id}"
        provider_token = 'YOUR_PROVIDER_TOKEN'  # Replace with your Telegram payment provider token
        currency = 'ZAR'  # South African Rand
        prices = [LabeledPrice(pack['label'], pack['price'])]
        await query.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices
        )
        await query.answer()
        await query.edit_message_text(_escape_markdown("Processing payment for HustleCoins..."), parse_mode='MarkdownV2')

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    # Parse pack_id and amount
    if payload.startswith("hustlecoins_"):
        parts = payload.split("_")
        pack_id = parts[1]
        pack = next((p for p in PREMIUM_PACKS if p['pack_id'] == pack_id), None)
        if pack:
            player_manager.add_hustlecoins(player_id, pack['amount'])
            await update.message.reply_text(_escape_markdown(f"✅ You received {pack['amount']} HustleCoins! Enjoy your premium purchases."), parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(_escape_markdown("Payment received, but pack not found. Please contact support."), parse_mode='MarkdownV2') 