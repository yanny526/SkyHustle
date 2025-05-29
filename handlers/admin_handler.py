"""
Admin Handler Module
Handles admin commands and controls
"""

from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import time
import logging

from modules.admin_manager import AdminManager
from modules.game_logging import log_admin_action
from utils.rate_limiter import rate_limit
from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)

class AdminHandler(BaseHandler):
    """Handler for admin-related commands"""
    
    def __init__(self, admin_manager: AdminManager):
        super().__init__()
        self.admin_manager = admin_manager

    @rate_limit(1)  # 1 second cooldown
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text(
                "❌ You do not have permission to use admin commands.",
                parse_mode='HTML'
            )
            return
            
        # Show admin menu
        keyboard = [
            [InlineKeyboardButton("👥 Manage Admins", callback_data="admin_manage_admins")],
            [InlineKeyboardButton("📊 System Status", callback_data="admin_system_status")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔧 Maintenance Mode", callback_data="admin_maintenance")],
            [InlineKeyboardButton("📝 View Logs", callback_data="admin_logs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 <b>Admin Control Panel</b>\n\n"
            "Select an option to manage the game:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    @rate_limit(1)
    async def handle_add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new admin"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /add_admin &lt;player_id&gt; 👑")
                )
                return
            
            target_id = args[0]
            result = self.admin_manager.add_admin(target_id)
            
            if result['success']:
                message = self.format_message(
                    "Admin Added",
                    [{
                        'title': 'Success!',
                        'content': f"Added {target_id} as admin"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Add Admin',
                        'content': result.get('message', 'Could not add admin.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_add_admin: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    @rate_limit(1)
    async def handle_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove an admin"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /remove_admin &lt;player_id&gt; 👑")
                )
                return
            
            target_id = args[0]
            result = self.admin_manager.remove_admin(target_id)
            
            if result['success']:
                message = self.format_message(
                    "Admin Removed",
                    [{
                        'title': 'Success!',
                        'content': f"Removed {target_id} from admins"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Remove Admin',
                        'content': result.get('message', 'Could not remove admin.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_remove_admin: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    @rate_limit(1)
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast a message to all players"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /broadcast &lt;message&gt; 📢")
                )
                return
            
            message = ' '.join(args)
            result = self.admin_manager.broadcast_message(message)
            
            if result['success']:
                message = self.format_message(
                    "Broadcast Complete",
                    [{
                        'title': 'Success!',
                        'content': f"Broadcast complete\n📤 Sent: {result['sent']}\n❌ Failed: {result['failed']}"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Broadcast',
                        'content': result.get('message', 'Could not broadcast message.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_broadcast: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    @rate_limit(1)
    async def handle_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle maintenance mode"""
        try:
            args = context.args
            if not args:
                await self.send_message(
                    update,
                    self.formatter.bold("Usage: /maintenance &lt;on|off&gt; 🔧")
                )
                return
            
            mode = args[0].lower()
            if mode not in ['on', 'off']:
                await self.send_message(
                    update,
                    self.formatter.bold("Mode must be 'on' or 'off'")
                )
                return
            
            result = self.admin_manager.set_maintenance_mode(mode == 'on')
            
            if result['success']:
                message = self.format_message(
                    "Maintenance Mode",
                    [{
                        'title': 'Success!',
                        'content': f"Maintenance mode turned {mode}"
                    }]
                )
            else:
                message = self.format_message(
                    "Error",
                    [{
                        'title': 'Failed to Set Maintenance Mode',
                        'content': result.get('message', 'Could not set maintenance mode.')
                    }]
                )
            
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_maintenance: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    @rate_limit(1)
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system logs"""
        try:
            logs = self.admin_manager.get_logs()
            
            if not logs:
                await self.send_message(
                    update,
                    self.formatter.bold("No logs found. 📝")
                )
                return
            
            # Format logs
            sections = [{
                'title': 'System Logs 📝',
                'items': [
                    {
                        'type': 'log',
                        'log_type': log['type'],
                        'timestamp': str(log['timestamp']),
                        'details': str(log['details'])
                    }
                    for log in logs
                ]
            }]
            
            # Send formatted message
            message = self.format_message("System Logs", sections)
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_logs: {e}", exc_info=True)
            await self._handle_error(update, e)
    
    @rate_limit(1)
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system status"""
        try:
            status = self.admin_manager.get_status()
            
            if not status:
                await self.send_message(
                    update,
                    self.formatter.bold("Could not fetch system status. 📊")
                )
                return
            
            # Format status
            sections = [{
                'title': 'System Status 📊',
                'items': [
                    {
                        'type': 'setting',
                        'key': setting['key'],
                        'value': str(setting['value'])
                    }
                    for setting in status
                ]
            }]
            
            # Send formatted message
            message = self.format_message("System Status", sections)
            await self.send_message(update, message)
            
        except Exception as e:
            logger.error(f"Error in handle_status: {e}", exc_info=True)
            await self._handle_error(update, e)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle admin callback queries"""
        query = update.callback_query
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await query.answer("Unauthorized")
            return
            
        try:
            if query.data == "admin_manage_admins":
                # Show admin management options
                keyboard = [
                    [{'text': 'Add Admin', 'callback_data': 'admin_add'}],
                    [{'text': 'Remove Admin', 'callback_data': 'admin_remove'}],
                    [{'text': 'View Admins', 'callback_data': 'admin_list'}],
                    [{'text': 'Back', 'callback_data': 'admin_back'}]
                ]
                
                message = self.format_message(
                    "Admin Management",
                    [{
                        'title': 'Admin Management 👥',
                        'content': 'Select an option:'
                    }]
                )
                await self.send_message(update, message, keyboard=keyboard, edit=True)
                
            elif query.data == "admin_system_status":
                # Show system status
                status = self.admin_manager.sheets.get_worksheet('Settings').get_all_records()
                
                sections = [{
                    'title': 'System Status 📊',
                    'items': [
                        {
                            'type': 'setting',
                            'key': setting['key'],
                            'value': str(setting['value'])
                        }
                        for setting in status
                    ]
                }]
                
                keyboard = [[{'text': 'Back', 'callback_data': 'admin_back'}]]
                message = self.format_message("System Status", sections)
                await self.send_message(update, message, keyboard=keyboard, edit=True)
                
            elif query.data == "admin_broadcast":
                message = self.format_message(
                    "Broadcast Message",
                    [{
                        'title': 'Broadcast Message 📢',
                        'content': 'Use /broadcast &lt;message&gt; to send a message to all players.'
                    }]
                )
                await self.send_message(update, message, edit=True)
                
            elif query.data == "admin_maintenance":
                # Show maintenance mode options
                keyboard = [
                    [{'text': 'Enable Maintenance', 'callback_data': 'maintenance_on'}],
                    [{'text': 'Disable Maintenance', 'callback_data': 'maintenance_off'}],
                    [{'text': 'Back', 'callback_data': 'admin_back'}]
                ]
                
                message = self.format_message(
                    "Maintenance Mode",
                    [{
                        'title': 'Maintenance Mode 🔧',
                        'content': 'Select an option:'
                    }]
                )
                await self.send_message(update, message, keyboard=keyboard, edit=True)
                
            elif query.data == "admin_logs":
                # Show recent logs
                logs = self.admin_manager.sheets.get_worksheet('Logs').get_all_records()
                logs = sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:10]
                
                if not logs:
                    message = self.format_message(
                        "Recent Logs",
                        [{
                            'title': 'Recent Logs 📝',
                            'content': 'No recent logs found.'
                        }]
                    )
                else:
                    sections = [{
                        'title': 'Recent Logs 📝',
                        'items': [
                            {
                                'type': 'log',
                                'log_type': log['type'],
                                'timestamp': str(log['timestamp']),
                                'details': str(log['details'])
                            }
                            for log in logs
                        ]
                    }]
                    message = self.format_message("Recent Logs", sections)
                
                keyboard = [[{'text': 'Back', 'callback_data': 'admin_back'}]]
                await self.send_message(update, message, keyboard=keyboard, edit=True)
                
            elif query.data == "admin_back":
                # Return to main admin menu
                keyboard = [
                    [{'text': '👥 Manage Admins', 'callback_data': 'admin_manage_admins'}],
                    [{'text': '📊 System Status', 'callback_data': 'admin_system_status'}],
                    [{'text': '📢 Broadcast Message', 'callback_data': 'admin_broadcast'}],
                    [{'text': '🔧 Maintenance Mode', 'callback_data': 'admin_maintenance'}],
                    [{'text': '📝 View Logs', 'callback_data': 'admin_logs'}]
                ]
                
                message = self.format_message(
                    "Admin Control Panel",
                    [{
                        'title': 'Admin Control Panel 🔧',
                        'content': 'Select an option to manage the game:'
                    }]
                )
                await self.send_message(update, message, keyboard=keyboard, edit=True)
                
        except Exception as e:
            logger.error(f"Error in handle_callback: {e}", exc_info=True)
            await self._handle_error(update, e)

    @rate_limit(1)
    async def handle_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ban command (stub)"""
        await update.message.reply_text("[BAN] Command coming soon.")

    @rate_limit(1)
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unban command (stub)"""
        await update.message.reply_text("[UNBAN] Command coming soon.")

    @rate_limit(1)
    async def handle_grant(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /grant command (stub)"""
        await update.message.reply_text("[GRANT] Command coming soon.")

    @rate_limit(1)
    async def handle_reset_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reset_player command (stub)"""
        await update.message.reply_text("[RESET PLAYER] Command coming soon.")

    @rate_limit(1)
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (stub)"""
        await update.message.reply_text("[STATS] Command coming soon.")

    @rate_limit(1)
    async def handle_search_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /search_player command (stub)"""
        await update.message.reply_text("[SEARCH PLAYER] Command coming soon.")

    @rate_limit(1)
    async def handle_admin_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin_help command (stub)"""
        await update.message.reply_text("[ADMIN HELP] Command coming soon.") 