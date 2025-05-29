"""
Shop and Black Market Command Handlers for SkyHustle 2
Implements /shop, /blackmarket, and /bag commands
"""

from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from modules.shop_manager import ShopManager
from modules.black_market_manager import BlackMarketManager
from modules.bag_manager import BagManager
from modules.player_manager import PlayerManager
import logging
import html

logger = logging.getLogger(__name__)

# These should be set in main.py after instantiation
shop_manager: ShopManager = None
black_market_manager: BlackMarketManager = None
bag_manager: BagManager = None
player_manager: PlayerManager = None

class ShopHandler(BaseHandler):
    """Handler for shop-related commands"""
    
    def __init__(self, shop_manager: ShopManager):
        super().__init__()
        self.shop_manager = shop_manager
    
    async def handle_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show shop with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            shop_items = self.shop_manager.get_shop_items()
            
            if not shop_items:
                await self.send_message(
                    update,
                    self.formatter.bold("No items available in the shop. 🏪"),
                    keyboard=[[{'text': '🔙 Back', 'callback_data': 'status'}]]
                )
                return
            
            # Format shop items
            sections = [{
                'title': 'Shop Items 🏪',
                'items': [
                    {
                        'type': 'item',
                        'name': item['name'],
                        'description': item['description'],
                        'emoji': item['emoji'],
                        'price': item['price'],
                        'effects': item.get('effects', [])
                    }
                    for item in shop_items
                ]
            }]
            
            # Create keyboard
            keyboard = [
                [{'text': '🛒 Buy Item', 'callback_data': 'buy_item'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            
            # Send formatted message
            message = self.format_message("Shop", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_shop: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_buy_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Buy an item from the shop"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /buy_item &lt;item_id&gt; 🛒")
                )
                return
            
            item_id = args[0]
            result = self.shop_manager.buy_item(str(update.effective_user.id), item_id)
            
            if result['success']:
                message = self.format_message(
                    "Item Purchased",
                    [{
                        'title': 'Success!',
                        'content': f"Bought {self.formatter.bold(result['item']['name'])}! 🛒"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Buy Item',
                        'content': result.get('message', 'Could not buy item.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_buy_item: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_use_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Use an item from inventory"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /use_item &lt;item_id&gt; 🎯")
                )
                return
            
            item_id = args[0]
            result = self.shop_manager.use_item(str(update.effective_user.id), item_id)
            
            if result['success']:
                message = self.format_message(
                    "Item Used",
                    [{
                        'title': 'Success!',
                        'content': f"Used {self.formatter.bold(result['item']['name'])}! 🎯"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Use Item',
                        'content': result.get('message', 'Could not use item.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_use_item: {e}", exc_info=True)
            await self._handle_error(update, e)

def _get_resource_emoji(resource: str) -> str:
    """Get emoji for resource type"""
    emojis = {
        'gold': '💰',
        'wood': '🪵',
        'stone': '🪨',
        'food': '🍖',
        'hustlecoins': '💎',
        'gems': '💎',
        'energy': '⚡',
        'experience': '✨'
    }
    return emojis.get(resource, '❓')

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show shop with lively UI"""
    try:
        player_id = str(update.effective_user.id)
        items = shop_manager.get_shop_items()
        coins = player_manager.get_hustlecoins(player_id)
        
        # Format shop sections
        sections = [{
            'title': 'SkyHustle Shop 🛒',
            'content': f"💎 <b>Your Balance:</b> {coins} HustleCoins"
        }]
        
        # Group items by category
        categories = {}
        for item in items:
            category = item.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Add items by category
        for category, category_items in categories.items():
            sections.append({
                'title': category,
                'items': [
                    {
                        'type': 'item',
                        'name': item['name'],
                        'description': item['description'],
                        'emoji': item.get('emoji', '📦'),
                        'price': item['price'],
                        'effects': item.get('effects', [])
                    }
                    for item in category_items
                ]
            })
        
        # Create keyboard
        keyboard = []
        for item in items:
            keyboard.append([
                {'text': f"Buy {item['name']}", 'callback_data': f"shop_buy_{item['item_id']}"}
            ])
        keyboard.append([
            {'text': '🔄 Refresh', 'callback_data': 'shop_refresh'},
            {'text': '🔙 Back', 'callback_data': 'status'}
        ])
        
        # Send formatted message
        message = BaseHandler().format_message("Shop", sections)
        await BaseHandler().send_message(update, message, keyboard=keyboard)
        
    except Exception as e:
        logger.error(f"Error in shop: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e)

async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show black market items"""
    try:
        player_id = str(update.effective_user.id)
        items = black_market_manager.get_market_items()
        coins = player_manager.get_hustlecoins(player_id)
        
        # Format black market sections
        sections = [{
            'title': 'Black Market 🖤',
            'content': f"💎 <b>Your Balance:</b> {coins} HustleCoins"
        }]
        
        # Add items
        sections.append({
            'title': 'Available Items',
            'items': [
                {
                    'type': 'item',
                    'name': item['name'],
                    'description': item['description'],
                    'emoji': item.get('emoji', '📦'),
                    'price': item['cost'],
                    'effects': item.get('effects', [])
                }
                for item in items
            ]
        })
        
        # Create keyboard
        keyboard = []
        for item in items:
            keyboard.append([
                {'text': f"Buy {item['name']}", 'callback_data': f"blackmarket_buy_{item['item_id']}"}
            ])
        keyboard.append([
            {'text': '🔙 Back', 'callback_data': 'status'}
        ])
        
        # Send formatted message
        message = BaseHandler().format_message("Black Market", sections)
        await BaseHandler().send_message(update, message, keyboard=keyboard)
        
    except Exception as e:
        logger.error(f"Error in blackmarket: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e)

async def bag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's inventory"""
    try:
        player_id = str(update.effective_user.id)
        items = bag_manager.get_bag(player_id)
        
        # Format bag sections
        sections = [{
            'title': 'Your Bag 🎒',
            'content': "Your inventory items:"
        }]
        
        if not items:
            sections[0]['content'] = "Your bag is empty."
        else:
            sections.append({
                'title': 'Items',
                'items': [
                    {
                        'type': 'item',
                        'name': item['item_id'],
                        'description': f"Quantity: {item['quantity']}",
                        'emoji': item.get('emoji', '📦')
                    }
                    for item in items
                ]
            })
        
        # Create keyboard
        keyboard = []
        for item in items:
            if item['type'] in ['single', 'multi', 'timed']:
                keyboard.append([
                    {'text': f"Use {item['item_id']}", 'callback_data': f"bag_use_{item['item_id']}"}
                ])
        keyboard.append([
            {'text': '🔙 Back', 'callback_data': 'status'}
        ])
        
        # Send formatted message
        message = BaseHandler().format_message("Bag", sections)
        await BaseHandler().send_message(update, message, keyboard=keyboard)
        
    except Exception as e:
        logger.error(f"Error in bag: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e)

# Callback query handlers for purchases and item use
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop-related callbacks"""
    try:
        query = update.callback_query
        player_id = str(query.from_user.id)
        data = query.data
        
        if data.startswith("shop_buy_"):
            item_id = data.split("_")[-1]
            result = shop_manager.purchase_item(player_id, item_id)
            
            if result['success']:
                message = BaseHandler().format_message(
                    "Item Purchased",
                    [{
                        'title': 'Success!',
                        'content': f"Bought {BaseHandler().formatter.bold(result['item']['name'])}! 🛒"
                    }]
                )
            else:
                message = BaseHandler().format_message(
                    "Error",
                    [{
                        'title': 'Failed to Buy Item',
                        'content': result.get('message', 'Could not buy item.')
                    }]
                )
            
            await BaseHandler().send_message(update, message, edit=True)
            
    except Exception as e:
        logger.error(f"Error in shop_callback: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e)

async def blackmarket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle black market-related callbacks"""
    try:
        query = update.callback_query
        player_id = str(query.from_user.id)
        data = query.data
        
        if data.startswith("blackmarket_buy_"):
            item_id = data.split("_")[-1]
            result = black_market_manager.purchase_item(player_id, item_id)
            
            if result['success']:
                message = BaseHandler().format_message(
                    "Item Purchased",
                    [{
                        'title': 'Success!',
                        'content': f"Bought {BaseHandler().formatter.bold(result['item']['name'])}! 🛒"
                    }]
                )
            else:
                message = BaseHandler().format_message(
                    "Error",
                    [{
                        'title': 'Failed to Buy Item',
                        'content': result.get('message', 'Could not buy item.')
                    }]
                )
            
            await BaseHandler().send_message(update, message, edit=True)
            
    except Exception as e:
        logger.error(f"Error in blackmarket_callback: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e)

async def bag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bag-related callbacks"""
    try:
        query = update.callback_query
        player_id = str(query.from_user.id)
        data = query.data
        
        if data.startswith("bag_use_"):
            item_id = data.split("_")[-1]
            result = bag_manager.use_item(player_id, item_id)
            
            if result['success']:
                message = BaseHandler().format_message(
                    "Item Used",
                    [{
                        'title': 'Success!',
                        'content': f"Used {BaseHandler().formatter.bold(result['item']['name'])}! 🎯"
                    }]
                )
            else:
                message = BaseHandler().format_message(
                    "Error",
                    [{
                        'title': 'Failed to Use Item',
                        'content': result.get('message', 'Could not use item.')
                    }]
                )
            
            await BaseHandler().send_message(update, message, edit=True)
            
    except Exception as e:
        logger.error(f"Error in bag_callback: {e}", exc_info=True)
        await BaseHandler()._handle_error(update, e) 