from typing import Dict, Any, List
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from modules.alliance_manager import AllianceManager
import logging

logger = logging.getLogger(__name__)

class AllianceHandler(BaseHandler):
    """Handler for alliance-related commands"""
    
    def __init__(self, alliance_manager: AllianceManager):
        super().__init__()
        self.alliance_manager = alliance_manager
    
    async def handle_alliance_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show alliance chat with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            alliance = self.alliance_manager.get_player_alliance(player_id)
            
            if not alliance:
                await self.send_message(
                    update,
                    self.formatter.bold("You are not in an alliance. 🤝"),
                    keyboard=[[{'text': '🔙 Back', 'callback_data': 'status'}]]
                )
                return
            
            chat = self.alliance_manager.get_chat_history(alliance['alliance_id'])
            if not chat:
                await self.send_message(
                    update,
                    self.formatter.bold("No messages in alliance chat yet. 💬"),
                    keyboard=[[{'text': '🔙 Back', 'callback_data': 'status'}]]
                )
                return
            
            # Format chat messages
            chat_messages = []
            for msg in chat:
                chat_messages.append(f"{msg['player_id']}: {msg['message']}")
            
            # Create message sections
            sections = [
                {
                    'title': 'Alliance Chat 💬',
                    'content': chat_messages
                }
            ]
            
            # Create keyboard
            keyboard = [
                [{'text': '✏️ Send Message', 'callback_data': 'send_alliance_message'}],
                [{'text': '🔙 Back', 'callback_data': 'status'}]
            ]
            
            # Send formatted message
            message = self.format_message("Alliance Chat", sections)
            await self.send_message(update, message, keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_alliance_chat: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_create_alliance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new alliance with a name and description"""
        try:
            args = context.args
            if len(args) < 2:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /create_alliance &lt;name&gt; &lt;description&gt; 🤝")
                )
                return
            
            name = args[0]
            description = ' '.join(args[1:])
            result = self.alliance_manager.create_alliance(str(update.effective_user.id), name, description)
            
            if result['success']:
                message = self.format_message(
                    "Alliance Created",
                    [{
                        'title': 'Success!',
                        'content': f"Alliance {self.formatter.bold(name)} created! Welcome to the world of alliances! 🤝"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Create Alliance',
                        'content': result.get('message', 'Could not create alliance.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_create_alliance: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    async def handle_join_alliance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Join an alliance with lively UI"""
        try:
            player_id = str(update.effective_user.id)
            if not context.args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /join_alliance &lt;alliance_id&gt; 🤝")
                )
                return
            
            alliance_id = context.args[0]
            result = self.alliance_manager.join_alliance(player_id, alliance_id)
            
            if result.get('success'):
                message = self.format_message(
                    "Alliance Joined",
                    [{
                        'title': 'Success!',
                        'content': f"Joined alliance {alliance_id}! Welcome to your new team! 🤝"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Join Alliance',
                        'content': result.get('message', 'Could not join alliance.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_join_alliance: {e}", exc_info=True)
            await self._handle_error(update, e) 