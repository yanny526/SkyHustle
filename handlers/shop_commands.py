"""
Shop and Black Market Command Handlers for SkyHustle 2
Implements /shop, /blackmarket, and /bag commands
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.shop_manager import ShopManager
from modules.black_market_manager import BlackMarketManager
from modules.bag_manager import BagManager
from modules.player_manager import PlayerManager

# These should be set in main.py after instantiation
shop_manager: ShopManager = None
black_market_manager: BlackMarketManager = None
bag_manager: BagManager = None
player_manager: PlayerManager = None

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    items = shop_manager.get_shop_items()
    coins = player_manager.get_hustlecoins(player_id)
    message = f"🛒 *Regular Shop*\n\nYour HustleCoins: {coins}\n\n"
    keyboard = []
    for item in items:
        cost_str = " | ".join(f"{k}: {v}" for k, v in item['cost'].items())
        message += f"*{item['name']}*\n{item['description']}\nCost: {cost_str}\n\n"
        keyboard.append([InlineKeyboardButton(f"Buy {item['name']}", callback_data=f"shop_buy_{item['item_id']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    items = black_market_manager.get_market_items()
    coins = player_manager.get_hustlecoins(player_id)
    message = f"🖤 *Black Market*\n\nYour HustleCoins: {coins}\n\n"
    keyboard = []
    for item in items:
        message += f"*{item['name']}*\n{item['description']}\nCost: {item['cost']} HustleCoins\n\n"
        keyboard.append([InlineKeyboardButton(f"Buy {item['name']}", callback_data=f"blackmarket_buy_{item['item_id']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def bag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    items = bag_manager.get_bag(player_id)
    message = "🎒 *Your Bag*\n\n"
    keyboard = []
    if not items:
        message += "Your bag is empty.\n"
    else:
        for item in items:
            name = item['item_id']
            qty = item['quantity']
            message += f"*{name}* x{qty}\n"
            if item['type'] in ['single', 'multi', 'timed']:
                keyboard.append([InlineKeyboardButton(f"Use {name}", callback_data=f"bag_use_{item['item_id']}")])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# Callback query handlers for purchases and item use
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    player_id = str(query.from_user.id)
    data = query.data
    if data.startswith("shop_buy_"):
        item_id = data.split("_")[-1]
        result = shop_manager.purchase_item(player_id, item_id)
        await query.answer()
        await query.edit_message_text(result['message'])

async def blackmarket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    player_id = str(query.from_user.id)
    data = query.data
    if data.startswith("blackmarket_buy_"):
        item_id = data.split("_")[-1]
        result = black_market_manager.purchase_item(player_id, item_id)
        await query.answer()
        await query.edit_message_text(result['message'])

async def bag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    player_id = str(query.from_user.id)
    data = query.data
    if data.startswith("bag_use_"):
        item_id = data.split("_")[-1]
        if bag_manager.use_item(player_id, item_id):
            await query.answer()
            await query.edit_message_text(f"Used {item_id}!")
        else:
            await query.answer()
            await query.edit_message_text(f"Failed to use {item_id}.") 