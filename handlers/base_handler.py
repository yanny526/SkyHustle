from typing import Dict, Any, Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import logging
from utils.formatting import MessageFormatter
import html

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all game handlers"""
    
    def __init__(self):
        self.formatter = MessageFormatter()
    
    async def _handle_error(self, update: Update, error: Exception):
        """Handle errors in command handlers"""
        error_message = "An error occurred. Please try again later."
        
        if isinstance(error, TelegramError):
            error_message = "Telegram API error. Please try again later."
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    self.formatter.bold(error_message),
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}", exc_info=True)
    
    def create_keyboard(self, buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
        """Create an inline keyboard from a list of button configurations"""
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append(InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data']
                ))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(keyboard)
    
    def format_message(self, title: str, sections: List[Dict[str, Any]]) -> str:
        """Format a message with title and sections"""
        message_parts = [self.formatter.bold(title)]
        
        for section in sections:
            if 'title' in section:
                message_parts.append(self.formatter.bold(section['title']))
            
            if 'content' in section:
                if isinstance(section['content'], list):
                    message_parts.append(self.formatter.format_list(section['content']))
                else:
                    message_parts.append(html.escape(section['content']))
            
            if 'items' in section:
                for item in section['items']:
                    if isinstance(item, dict):
                        if item.get('type') == 'alliance':
                            message_parts.append(self.formatter.format_alliance_info(item))
                        elif item.get('type') == 'notification':
                            message_parts.append(self.formatter.format_notification(item))
                        elif item.get('type') == 'building':
                            message_parts.append(self.formatter.format_building(item, item.get('emoji', '🏗️')))
                        elif item.get('type') == 'transaction':
                            message_parts.append(self.formatter.format_transaction(item['seller'], item['buyer']))
                        elif item.get('type') == 'setting':
                            message_parts.append(self.formatter.format_setting(item['key'], item['value']))
                        elif item.get('type') == 'log':
                            message_parts.append(self.formatter.format_log(item))
                        elif item.get('type') == 'item':
                            message_parts.append(self.formatter.format_item(item, item.get('effects')))
                        else:
                            message_parts.append(f"└ {item.get('emoji', '📊')} {self.formatter.bold(item['name'])}")
                            if 'description' in item:
                                message_parts.append(f"  {html.escape(item['description'])}")
                    else:
                        message_parts.append(f"└ {html.escape(str(item))}")
            
            message_parts.append("")  # Add empty line between sections
        
        return "\n".join(message_parts)
    
    async def send_message(
        self,
        update: Update,
        message: str,
        keyboard: Optional[List[List[Dict[str, str]]]] = None,
        edit: bool = False
    ):
        """Send or edit a message with optional keyboard"""
        try:
            if keyboard:
                reply_markup = self.create_keyboard(keyboard)
            else:
                reply_markup = None
            
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            await self._handle_error(update, e) 