"""
Player module for SkyHustle.
Handles player data, resources, and profile management.
"""
import logging
import datetime
from utils.sheets_service import (
    get_sheet_data, update_sheet_data, append_sheet_data
)
from utils.constants import PLAYER_STARTING_RESOURCES
from config import SHEET_NAMES, DAILY_REWARD

logger = logging.getLogger(__name__)

def get_player(player_id):
    """
    Get player data from Google Sheets.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        dict: Player data or None if not found
    """
    try:
        players = get_sheet_data(SHEET_NAMES['players'])
        for player in players:
            if str(player.get('player_id')) == str(player_id):
                return player
        return None
    except Exception as e:
        logger.error(f"Error getting player data: {e}")
        return None

def create_player(player_id, name):
    """
    Create a new player in Google Sheets.
    
    Args:
        player_id: Telegram user ID
        name: Initial display name
        
    Returns:
        dict: New player data or None if failed
    """
    try:
        # Check if player already exists
        existing_player = get_player(player_id)
        if existing_player:
            return existing_player
        
        # Create new player data
        player_data = {
            'player_id': str(player_id),
            'display_name': name,
            'credits': PLAYER_STARTING_RESOURCES['credits'],
            'minerals': PLAYER_STARTING_RESOURCES['minerals'],
            'energy': PLAYER_STARTING_RESOURCES['energy'],
            'skybucks': PLAYER_STARTING_RESOURCES['skybucks'],
            'experience': 0,
            'tutorial_completed': False,
            'last_login': datetime.datetime.utcnow().isoformat(),
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Add player to sheet
        append_sheet_data(SHEET_NAMES['players'], [player_data])
        
        return player_data
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return None

def update_player(player_id, updates):
    """
    Update player data in Google Sheets.
    
    Args:
        player_id: Telegram user ID
        updates: Dictionary of fields to update
        
    Returns:
        bool: Success or failure
    """
    try:
        player = get_player(player_id)
        if not player:
            return False
        
        # Update player data
        for key, value in updates.items():
            player[key] = value
        
        # Update last login time
        player['last_login'] = datetime.datetime.utcnow().isoformat()
        
        # Update sheet
        return update_sheet_data(SHEET_NAMES['players'], player, 'player_id', str(player_id))
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False

def get_random_players(exclude_id, count=5):
    """
    Get random players for PvP targeting.
    
    Args:
        exclude_id: Player ID to exclude (usually the requesting player)
        count: Number of players to return
        
    Returns:
        list: List of player data dictionaries
    """
    try:
        players = get_sheet_data(SHEET_NAMES['players'])
        # Filter out the requesting player
        filtered_players = [p for p in players if str(p.get('player_id')) != str(exclude_id)]
        
        # In a full implementation, this would use some algorithm to find appropriate targets
        # based on player level, power, etc.
        
        # For now, just return up to 'count' random players
        import random
        if len(filtered_players) <= count:
            return filtered_players
        return random.sample(filtered_players, count)
    except Exception as e:
        logger.error(f"Error getting random players: {e}")
        return []

def claim_daily_reward(player_id):
    """
    Claim daily reward for a player.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        dict: Result of the claim attempt
    """
    try:
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Check if player has already claimed today
        last_claim = player.get('last_daily_claim')
        now = datetime.datetime.utcnow()
        
        if last_claim:
            last_claim_date = datetime.datetime.fromisoformat(last_claim)
            if last_claim_date.date() == now.date():
                return {
                    'success': False,
                    'message': "You've already claimed your daily reward today. Come back tomorrow!"
                }
        
        # Check for streak
        streak = 1
        if last_claim:
            last_claim_date = datetime.datetime.fromisoformat(last_claim)
            yesterday = (now - datetime.timedelta(days=1)).date()
            
            if last_claim_date.date() == yesterday:
                streak = player.get('daily_streak', 0) + 1
            else:
                streak = 1
        
        # Calculate rewards (could scale with streak in a full implementation)
        rewards = {
            'credits': DAILY_REWARD['credits'],
            'minerals': DAILY_REWARD['minerals'],
            'energy': DAILY_REWARD['energy']
        }
        
        # Apply rewards to player
        update_data = {
            'credits': player.get('credits', 0) + rewards['credits'],
            'minerals': player.get('minerals', 0) + rewards['minerals'],
            'energy': player.get('energy', 0) + rewards['energy'],
            'last_daily_claim': now.isoformat(),
            'daily_streak': streak
        }
        
        success = update_player(player_id, update_data)
        
        if success:
            return {
                'success': True,
                'rewards': rewards,
                'streak': streak
            }
        else:
            return {
                'success': False,
                'message': "Failed to apply rewards. Please try again later."
            }
    except Exception as e:
        logger.error(f"Error claiming daily reward: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }
