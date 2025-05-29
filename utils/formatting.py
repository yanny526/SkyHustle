from typing import Dict, Any, List
import html

class MessageFormatter:
    """Utility class for formatting Telegram messages with HTML"""
    
    @staticmethod
    def bold(text: str) -> str:
        """Wrap text in bold HTML tags"""
        return f"<b>{html.escape(text)}</b>"
    
    @staticmethod
    def italic(text: str) -> str:
        """Wrap text in italic HTML tags"""
        return f"<i>{html.escape(text)}</i>"
    
    @staticmethod
    def code(text: str) -> str:
        """Wrap text in code HTML tags"""
        return f"<code>{html.escape(text)}</code>"
    
    @staticmethod
    def pre(text: str) -> str:
        """Wrap text in pre HTML tags"""
        return f"<pre>{html.escape(text)}</pre>"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        """Create an HTML link"""
        return f'<a href="{url}">{html.escape(text)}</a>'
    
    @staticmethod
    def format_resource(resource: str, amount: int, max_amount: int = None) -> str:
        """Format a resource with emoji and amount"""
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
        emoji = emojis.get(resource, '❓')
        if max_amount:
            return f"{emoji} {amount}/{max_amount}"
        return f"{emoji} {amount}"
    
    @staticmethod
    def format_progress_bar(percentage: float, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 100 * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}] {percentage:.1f}%"
    
    @staticmethod
    def format_list(items: List[str], prefix: str = "└") -> str:
        """Format a list of items with a prefix"""
        return "\n".join(f"{prefix} {item}" for item in items)
    
    @staticmethod
    def format_section(title: str, content: str) -> str:
        """Format a section with title and content"""
        return f"{MessageFormatter.bold(title)}\n{content}\n"
    
    @staticmethod
    def format_rewards(rewards: Dict[str, Any]) -> str:
        """Format rewards with emojis"""
        reward_strs = []
        for k, v in rewards.items():
            if k in ['gold', 'wood', 'stone', 'food', 'hustlecoins', 'gems']:
                reward_strs.append(MessageFormatter.format_resource(k, v))
            elif k == 'xp':
                reward_strs.append(f"✨ {v} XP")
        return " | ".join(reward_strs)
    
    @staticmethod
    def format_stats(stats: Dict[str, Any]) -> str:
        """Format stats with emojis"""
        stat_emojis = {
            'attack': '⚔️',
            'defense': '🛡️',
            'speed': '⚡',
            'health': '❤️',
            'energy': '🔋',
            'luck': '🍀'
        }
        return " | ".join(f"{stat_emojis.get(k, '📊')} {v}" for k, v in stats.items())
    
    @staticmethod
    def format_alliance_info(alliance: Dict[str, Any]) -> str:
        """Format alliance information"""
        sections = [
            f"<b>Name:</b> {html.escape(alliance['name'])}",
            f"<b>Leader:</b> {html.escape(alliance.get('leader', 'Unknown'))}",
            f"<b>Members:</b> {html.escape(', '.join(alliance.get('members', [])))}",
            f"<b>Description:</b> {html.escape(alliance.get('description', ''))}"
        ]
        return "\n".join(sections)
    
    @staticmethod
    def format_notification(notification: Dict[str, Any], read: bool = False) -> str:
        """Format a notification"""
        read_status = "✓" if read else "○"
        return (
            f"└ {read_status} {notification['emoji']} <b>{html.escape(notification['title'])}</b>\n"
            f"  {html.escape(notification['message'])}"
        )
    
    @staticmethod
    def format_building(building: Dict[str, Any], emoji: str) -> str:
        """Format building information"""
        return (
            f"└ {emoji} <b>{html.escape(building['name'])}</b>\n"
            f"  {html.escape(building['description'])}"
        )
    
    @staticmethod
    def format_transaction(seller: str, buyer: str) -> str:
        """Format transaction information"""
        return (
            f"👤 <b>Seller:</b> {html.escape(seller)}\n"
            f"👤 <b>Buyer:</b> {html.escape(buyer)}\n"
        )
    
    @staticmethod
    def format_setting(key: str, value: Any) -> str:
        """Format a setting"""
        return f"<b>{html.escape(key)}</b>: {html.escape(str(value))}"
    
    @staticmethod
    def format_log(log: Dict[str, Any]) -> str:
        """Format a log entry"""
        return (
            f"<b>{html.escape(log['type'])}</b>\n"
            f"Time: {html.escape(str(log['timestamp']))}\n"
            f"Details: {html.escape(str(log['details']))}\n"
        )
    
    @staticmethod
    def format_item(item: Dict[str, Any], effects: List[Dict[str, Any]] = None) -> str:
        """Format item information with effects"""
        message = f"✅ <b>{html.escape(item['name'])}</b>\n{html.escape(item['description'])}\n\n"
        if effects:
            for effect in effects:
                message += f"└ {effect['emoji']} {html.escape(effect['description'])}\n"
        return message 