"""
Premium Currency Command Handlers for SkyHustle 2
Implements /buy command and payment integration for HustleCoins
"""

from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from modules.premium_manager import PremiumManager
import logging

logger = logging.getLogger(__name__)

class PremiumHandler(BaseHandler):
    """Handler for premium-related commands"""
    
    def __init__(self, premium_manager: PremiumManager):
        super().__init__()
        self.premium_manager = premium_manager
    
    async def handle_premium_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium shop with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            premium_packs = self.premium_manager.get_premium_packs()
            
            if not premium_packs:
                await self.send_message(
                    update,
                    self.formatter.bold("No premium packs available. 💎"),
                    keyboard=[[{'text': '🔙 Back', 'callback_data': 'status'}]]
                )
                return
            
            # Format premium packs
            sections = [{
                'title': 'Premium Packs 💎',
                'items': [
                    {
                        'type': 'item',
                        'name': pack['name'],
                        'description': f"{pack['amount']} HustleCoins for SkyHustle 2.",
                        'emoji': '💎',
                        'price': pack['price'],
                        'effects': pack.get('effects', [])
                    }
                    for pack in premium_packs
                ]
            }]
            
            # Create keyboard
            keyboard = [
                [{'text': '💎 Buy Pack', 'callback_data': 'buy_premium_pack'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            
            # Send formatted message
            message = self.format_message("Premium Shop", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_premium_shop: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_buy_premium_pack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Buy a premium pack"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /buy_premium_pack &lt;pack_id&gt; 💎")
                )
                return
            
            pack_id = args[0]
            pack = self.premium_manager.get_premium_pack(pack_id)
            
            if not pack:
                await self.send_message(
                    update,
                    self.formatter.bold("Pack not found. 💎")
                )
                return
            
            # Create payment keyboard
            keyboard = [[
                InlineKeyboardButton(
                    text=f"Pay {pack['price']} {pack['currency']}",
                    callback_data=f"pay_premium_{pack_id}"
                )
            ]]
            
            # Send payment message
            message = self.format_message(
                "Premium Pack",
                [{
                    'title': pack['name'],
                    'content': f"{pack['amount']} HustleCoins for SkyHustle 2.",
                    'items': [{
                        'type': 'item',
                        'name': 'Price',
                        'description': f"{pack['price']} {pack['currency']}",
                        'emoji': '💰'
                    }]
                }]
            )
            
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_buy_premium_pack: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_premium_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle premium payment callback"""
        try:
            query = update.callback_query
            pack_id = query.data.split('_')[-1]
            
            # Update message to show processing
            await query.edit_message_text(
                self.formatter.bold("Processing payment for HustleCoins..."),
                parse_mode='HTML'
            )
            
            # Process payment
            result = self.premium_manager.process_payment(str(update.effective_user.id), pack_id)
            
            if result['success']:
                message = self.format_message(
                    "Payment Successful",
                    [{
                        'title': 'Success!',
                        'content': f"You received {result['amount']} HustleCoins! Enjoy your premium purchases."
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Payment Failed',
                        'content': "Payment received, but pack not found. Please contact support."
                    }]
                )
            
            await query.edit_message_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in handle_premium_payment: {e}", exc_info=True)
            await self._handle_error(update, e) 