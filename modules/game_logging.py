"""
Game Logging Module
Handles centralized logging of game events, achievements, and admin actions
"""

import uuid
import time
from typing import Dict, Any
from modules.google_sheets_manager import GoogleSheetsManager

class GameLogger:
    def __init__(self):
        self.sheets = GoogleSheetsManager()

    def log_admin_action(self, admin_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log an admin action"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'admin_action',
            'user_id': admin_id,
            'action': action,
            'details': str(details)
        })

    def log_achievement(self, player_id: str, achievement_name: str) -> None:
        """Log an achievement unlock"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'achievement',
            'user_id': player_id,
            'achievement': achievement_name
        })

    def log_daily_reward(self, player_id: str, reward_type: str, amount: int) -> None:
        """Log a daily reward claim"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'daily_reward',
            'user_id': player_id,
            'reward_type': reward_type,
            'amount': amount
        })

    def log_shop_transaction(self, player_id: str, item_id: str, amount: int, cost: Dict[str, int]) -> None:
        """Log a shop transaction"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'shop_transaction',
            'user_id': player_id,
            'item_id': item_id,
            'amount': amount,
            'cost': str(cost)
        })

    def log_black_market_transaction(self, player_id: str, item_id: str, amount: int, cost: int) -> None:
        """Log a black market transaction"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'black_market_transaction',
            'user_id': player_id,
            'item_id': item_id,
            'amount': amount,
            'cost': cost
        })

    def log_alliance_action(self, alliance_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log an alliance action"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'alliance_action',
            'alliance_id': alliance_id,
            'action': action,
            'details': str(details)
        })

    def log_error(self, error_type: str, details: str) -> None:
        """Log a system error"""
        self.sheets.append_row('Logs', {
            'timestamp': time.time(),
            'type': 'error',
            'error_type': error_type,
            'details': details
        })

# Create global logger instance
logger = GameLogger()

# Convenience functions
def log_admin_action(admin_id: str, action: str, details: Dict[str, Any]) -> None:
    logger.log_admin_action(admin_id, action, details)

def log_achievement(player_id: str, achievement_name: str) -> None:
    logger.log_achievement(player_id, achievement_name)

def log_daily_reward(player_id: str, reward_type: str, amount: int) -> None:
    logger.log_daily_reward(player_id, reward_type, amount)

def log_shop_transaction(player_id: str, item_id: str, amount: int, cost: Dict[str, int]) -> None:
    logger.log_shop_transaction(player_id, item_id, amount, cost)

def log_black_market_transaction(player_id: str, item_id: str, amount: int, cost: int) -> None:
    logger.log_black_market_transaction(player_id, item_id, amount, cost)

def log_alliance_action(alliance_id: str, action: str, details: Dict[str, Any]) -> None:
    logger.log_alliance_action(alliance_id, action, details)

def log_error(error_type: str, details: str) -> None:
    logger.log_error(error_type, details)

def log_event(level, event, details=None):
    log_data = {
        'log_id': str(uuid.uuid4()),
        'timestamp': int(time.time()),
        'level': level,
        'event': event,
        'details': str(details) if details else ''
    }
    logger.sheets.log_event(log_data) 