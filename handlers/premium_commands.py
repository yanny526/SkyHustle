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

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command"""
    message = "<b>💰 HustleCoins Store</b>\n\nSelect a pack to purchase:"
    
    keyboard = []
    for pack in PREMIUM_PACKS:
        keyboard.append([
            InlineKeyboardButton(
                pack['label'],
                callback_data=f"buy_{pack['pack_id']}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy callback queries"""
    query = update.callback_query
    player_id = str(query.from_user.id)
    pack_id = query.data.split('_')[1]
    
    # Find selected pack
    pack = next((p for p in PREMIUM_PACKS if p['pack_id'] == pack_id), None)
    if not pack:
        await query.answer("Invalid pack selected!")
        return
    
    # Create invoice
    title = f"Purchase {pack['amount']} HustleCoins"
    description = f"Get {pack['amount']} HustleCoins for your SkyHustle account"
    payload = f"hustlecoins_{pack_id}_{player_id}"
    provider_token = "YOUR_PROVIDER_TOKEN"  # Set this in main.py
    currency = "ZAR"
    prices = [LabeledPrice(f"{pack['amount']} HustleCoins", pack['price'])]
    
    # Send invoice
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices
    )
    
    await query.answer()

async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle successful payment"""
    payment = update.message.successful_payment
    payload = payment.invoice_payload.split('_')
    
    if len(payload) != 3 or payload[0] != 'hustlecoins':
        return
    
    pack_id = payload[1]
    player_id = payload[2]
    
    # Find purchased pack
    pack = next((p for p in PREMIUM_PACKS if p['pack_id'] == pack_id), None)
    if not pack:
        return
    
    # Add coins to player's balance
    player_manager.add_hustlecoins(player_id, pack['amount'])
    
    # Send confirmation message
    message = (
        f"<b>✅ Payment Successful!</b>\n\n"
        f"You have received {pack['amount']} HustleCoins.\n"
        f"Your new balance: {player_manager.get_hustlecoins(player_id)}"
    )
    
    await update.message.reply_text(message, parse_mode='HTML') 