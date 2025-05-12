"""
Alliance module for SkyHustle.
Handles alliance data, management, and wars.
"""
import logging
import datetime
import random
import string
from utils.sheets_service import (
    get_sheet_data, update_sheet_data, append_sheet_data
)
from config import SHEET_NAMES, MAX_ALLIANCE_SIZE
from modules.player import get_player, update_player

logger = logging.getLogger(__name__)

def get_alliance(alliance_id):
    """
    Get alliance data.
    
    Args:
        alliance_id: Alliance ID
        
    Returns:
        dict: Alliance data or None if not found
    """
    try:
        alliances = get_sheet_data(SHEET_NAMES['alliances'])
        for alliance in alliances:
            if alliance.get('alliance_id') == alliance_id:
                return alliance
        return None
    except Exception as e:
        logger.error(f"Error getting alliance: {e}")
        return None

def get_alliance_by_player(player_id):
    """
    Get alliance data for a player's alliance.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        dict: Alliance data or None if player is not in an alliance
    """
    try:
        player = get_player(player_id)
        if not player or 'alliance_id' not in player or not player['alliance_id']:
            return None
        
        return get_alliance(player['alliance_id'])
    except Exception as e:
        logger.error(f"Error getting alliance by player: {e}")
        return None

def create_alliance(player_id, alliance_name):
    """
    Create a new alliance.
    
    Args:
        player_id: Telegram user ID of the creator
        alliance_name: Name for the new alliance
        
    Returns:
        dict: Result of alliance creation
    """
    try:
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Check if player is already in an alliance
        if 'alliance_id' in player and player['alliance_id']:
            return {
                'success': False,
                'message': "You are already in an alliance. Leave your current alliance first."
            }
        
        # Check alliance name
        if len(alliance_name) < 3 or len(alliance_name) > 32:
            return {
                'success': False,
                'message': "Alliance name must be between 3 and 32 characters."
            }
        
        # Check if alliance name is already taken
        alliances = get_sheet_data(SHEET_NAMES['alliances'])
        for alliance in alliances:
            if alliance.get('alliance_name', '').lower() == alliance_name.lower():
                return {
                    'success': False,
                    'message': "An alliance with this name already exists."
                }
        
        # Generate a unique alliance ID and join code
        alliance_id = 'a_' + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Create alliance record
        now = datetime.datetime.utcnow()
        alliance_data = {
            'alliance_id': alliance_id,
            'alliance_name': alliance_name,
            'leader_id': str(player_id),
            'join_code': join_code,
            'member_count': 1,
            'total_power': player.get('power', 0),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        append_sheet_data(SHEET_NAMES['alliances'], [alliance_data])
        
        # Update player's alliance
        update_player(player_id, {
            'alliance_id': alliance_id,
            'alliance_role': 'leader'
        })
        
        return {
            'success': True,
            'alliance_id': alliance_id,
            'join_code': join_code
        }
    except Exception as e:
        logger.error(f"Error creating alliance: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }

def join_alliance(player_id, join_code):
    """
    Join an existing alliance using a join code.
    
    Args:
        player_id: Telegram user ID
        join_code: Alliance join code
        
    Returns:
        dict: Result of join attempt
    """
    try:
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Check if player is already in an alliance
        if 'alliance_id' in player and player['alliance_id']:
            return {
                'success': False,
                'message': "You are already in an alliance. Leave your current alliance first."
            }
        
        # Find alliance by join code
        alliances = get_sheet_data(SHEET_NAMES['alliances'])
        alliance = None
        for a in alliances:
            if a.get('join_code') == join_code:
                alliance = a
                break
        
        if not alliance:
            return {
                'success': False,
                'message': "Invalid join code. Please check and try again."
            }
        
        # Check if alliance is full
        if alliance.get('member_count', 0) >= MAX_ALLIANCE_SIZE:
            return {
                'success': False,
                'message': f"Alliance is full. Maximum size is {MAX_ALLIANCE_SIZE} members."
            }
        
        # Update alliance member count and power
        alliance['member_count'] = alliance.get('member_count', 0) + 1
        alliance['total_power'] = alliance.get('total_power', 0) + player.get('power', 0)
        alliance['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        update_sheet_data(SHEET_NAMES['alliances'], alliance, 'alliance_id', alliance['alliance_id'])
        
        # Update player's alliance
        update_player(player_id, {
            'alliance_id': alliance['alliance_id'],
            'alliance_role': 'member'
        })
        
        return {
            'success': True,
            'alliance_name': alliance['alliance_name']
        }
    except Exception as e:
        logger.error(f"Error joining alliance: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }

def leave_alliance(player_id):
    """
    Leave current alliance.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        dict: Result of leave attempt
    """
    try:
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Check if player is in an alliance
        if 'alliance_id' not in player or not player['alliance_id']:
            return {
                'success': False,
                'message': "You are not in an alliance."
            }
        
        alliance_id = player['alliance_id']
        alliance = get_alliance(alliance_id)
        
        if not alliance:
            # Alliance doesn't exist, just remove from player
            update_player(player_id, {
                'alliance_id': None,
                'alliance_role': None
            })
            return {
                'success': True
            }
        
        # Check if player is the leader
        if player.get('alliance_role') == 'leader':
            # In a full implementation, this would transfer leadership or disband
            return {
                'success': False,
                'message': "As the leader, you cannot leave the alliance. Transfer leadership or disband the alliance."
            }
        
        # Update alliance member count and power
        alliance['member_count'] = max(0, alliance.get('member_count', 1) - 1)
        alliance['total_power'] = max(0, alliance.get('total_power', 0) - player.get('power', 0))
        alliance['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        update_sheet_data(SHEET_NAMES['alliances'], alliance, 'alliance_id', alliance_id)
        
        # Remove alliance from player
        update_player(player_id, {
            'alliance_id': None,
            'alliance_role': None
        })
        
        return {
            'success': True
        }
    except Exception as e:
        logger.error(f"Error leaving alliance: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }

def invite_to_alliance(player_id, target_username):
    """
    Invite another player to the alliance.
    
    Args:
        player_id: Telegram user ID of the inviter
        target_username: Username of the player to invite
        
    Returns:
        dict: Result of invite attempt
    """
    # In a full implementation, this would send an invitation to the target player
    # For now, return a placeholder response
    return {
        'success': False,
        'message': "Alliance invitations not implemented yet"
    }
