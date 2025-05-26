"""
Admin Handler Module
Handles admin commands and controls
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import time

from modules.admin_manager import AdminManager
from modules.game_logging import log_admin_action
from utils.rate_limiter import rate_limit

class AdminHandler:
    def __init__(self):
        self.admin_manager = AdminManager()

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
            "<b>🔧 Admin Control Panel</b>\n\nSelect an option to manage the game:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    @rate_limit(1)
    async def handle_add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /addadmin command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
            return
            
        if not context.args:
            await update.message.reply_text(
                "Usage: /addadmin <user_id>",
                parse_mode='HTML'
            )
            return
            
        target_id = context.args[0]
        result = self.admin_manager.add_admin(target_id, user_id)
        
        if result['success']:
            await update.message.reply_text(f"✅ Added {target_id} as admin", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ {result['message']}", parse_mode='HTML')

    @rate_limit(1)
    async def handle_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /removeadmin command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
            return
            
        if not context.args:
            await update.message.reply_text(
                "Usage: /removeadmin <user_id>",
                parse_mode='HTML'
            )
            return
            
        target_id = context.args[0]
        result = self.admin_manager.remove_admin(target_id, user_id)
        
        if result['success']:
            await update.message.reply_text(f"✅ Removed {target_id} from admins", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ {result['message']}", parse_mode='HTML')

    @rate_limit(1)
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /broadcast command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
            return
            
        if not context.args:
            await update.message.reply_text(
                "Usage: /broadcast <message>",
                parse_mode='HTML'
            )
            return
            
        message = " ".join(context.args)
        
        # Get all players
        players = self.admin_manager.sheets.get_worksheet('Players').get_all_records()
        
        sent = 0
        failed = 0
        
        for player in players:
            try:
                await context.bot.send_message(
                    chat_id=int(player['user_id']),
                    text=f"<b>📢 Broadcast Message</b>\n\n{message}",
                    parse_mode='HTML'
                )
                sent += 1
            except:
                failed += 1
                
        # Log broadcast
        log_admin_action(user_id, 'broadcast', {
            'message': message,
            'sent': sent,
            'failed': failed
        })
        
        await update.message.reply_text(
            f"✅ Broadcast complete\n📤 Sent: {sent}\n❌ Failed: {failed}",
            parse_mode='HTML'
        )

    @rate_limit(1)
    async def handle_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /maintenance command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
            return
            
        if not context.args:
            await update.message.reply_text(
                "Usage: /maintenance <on|off>",
                parse_mode='HTML'
            )
            return
            
        mode = context.args[0].lower()
        
        if mode not in ['on', 'off']:
            await update.message.reply_text("Invalid mode. Use 'on' or 'off'", parse_mode='HTML')
            return
            
        # Update maintenance mode in settings
        settings = self.admin_manager.sheets.get_worksheet('Settings').get_all_records()
        for i, setting in enumerate(settings):
            if setting['key'] == 'maintenance_mode':
                setting['value'] = 'true' if mode == 'on' else 'false'
                self.admin_manager.sheets.update_row('Settings', i + 2, setting)
                break
                
        # Log maintenance mode change
        log_admin_action(user_id, 'maintenance_mode', {'mode': mode})
        
        await update.message.reply_text(
            f"✅ Maintenance mode turned {mode}",
            parse_mode='HTML'
        )

    @rate_limit(1)
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logs command"""
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized", parse_mode='HTML')
            return
            
        # Get recent logs
        logs = self.admin_manager.sheets.get_worksheet('Logs').get_all_records()
        logs = sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        if not logs:
            await update.message.reply_text("No recent logs found", parse_mode='HTML')
            return
            
        # Format logs
        log_text = "<b>📝 Recent Logs</b>\n\n"
        for log in logs:
            log_text += (
                f"<b>{log['type']}</b>\n"
                f"Time: {str(log['timestamp'])}\n"
                f"Details: {str(log['details'])}\n\n"
            )
            
        await update.message.reply_text(log_text, parse_mode='HTML')

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle admin callback queries"""
        query = update.callback_query
        user_id = str(update.effective_user.id)
        
        if not self.admin_manager.is_admin(user_id):
            await query.answer("Unauthorized")
            return
            
        if query.data == "admin_manage_admins":
            # Show admin management options
            keyboard = [
                [InlineKeyboardButton("Add Admin", callback_data="admin_add")],
                [InlineKeyboardButton("Remove Admin", callback_data="admin_remove")],
                [InlineKeyboardButton("View Admins", callback_data="admin_list")],
                [InlineKeyboardButton("Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "<b>👥 Admin Management</b>\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "admin_system_status":
            # Show system status
            status = self.admin_manager.sheets.get_worksheet('Settings').get_all_records()
            status_text = "<b>📊 System Status</b>\n\n"
            
            for setting in status:
                status_text += f"<b>{setting['key']}</b>: {str(setting['value'])}\n"
                
            keyboard = [[InlineKeyboardButton("Back", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "admin_broadcast":
            await query.edit_message_text(
                "<b>📢 Broadcast Message</b>\n\n"
                "Use /broadcast <message> to send a message to all players.",
                parse_mode='HTML'
            )
            
        elif query.data == "admin_maintenance":
            # Show maintenance mode options
            keyboard = [
                [InlineKeyboardButton("Enable Maintenance", callback_data="maintenance_on")],
                [InlineKeyboardButton("Disable Maintenance", callback_data="maintenance_off")],
                [InlineKeyboardButton("Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "<b>🔧 Maintenance Mode</b>\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "admin_logs":
            # Show recent logs
            logs = self.admin_manager.sheets.get_worksheet('Logs').get_all_records()
            logs = sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            if not logs:
                await query.edit_message_text("No recent logs found", parse_mode='HTML')
                return
                
            log_text = "<b>📝 Recent Logs</b>\n\n"
            for log in logs:
                log_text += (
                    f"<b>{log['type']}</b>\n"
                    f"Time: {str(log['timestamp'])}\n"
                    f"Details: {str(log['details'])}\n\n"
                )
                
            keyboard = [[InlineKeyboardButton("Back", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                log_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        elif query.data == "admin_back":
            # Return to main admin menu
            keyboard = [
                [InlineKeyboardButton("👥 Manage Admins", callback_data="admin_manage_admins")],
                [InlineKeyboardButton("📊 System Status", callback_data="admin_system_status")],
                [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
                [InlineKeyboardButton("🔧 Maintenance Mode", callback_data="admin_maintenance")],
                [InlineKeyboardButton("📝 View Logs", callback_data="admin_logs")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "<b>🔧 Admin Control Panel</b>\n\nSelect an option to manage the game:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    @rate_limit(1)
    async def handle_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ban command (stub)"""
        await update.message.reply_text("[BAN] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unban command (stub)"""
        await update.message.reply_text("[UNBAN] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_grant(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /grant command (stub)"""
        await update.message.reply_text("[GRANT] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_reset_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reset_player command (stub)"""
        await update.message.reply_text("[RESET PLAYER] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (stub)"""
        await update.message.reply_text("[STATS] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_search_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /search_player command (stub)"""
        await update.message.reply_text("[SEARCH PLAYER] Command coming soon.", parse_mode='HTML')

    @rate_limit(1)
    async def handle_admin_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin_help command (stub)"""
        await update.message.reply_text("[ADMIN HELP] Command coming soon.", parse_mode='HTML') 