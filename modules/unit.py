"""
Unit module for SkyHustle.
Handles unit data, training, and combat.
"""
import logging
import datetime
from utils.sheets_service import (
    get_sheet_data, update_sheet_data, append_sheet_data
)
from utils.constants import UNIT_TYPES
from config import SHEET_NAMES
from modules.player import get_player, update_player

logger = logging.getLogger(__name__)

def get_units():
    """
    Get available unit types.
    
    Returns:
        list: Unit type definitions
    """
    # In a full implementation, this would read from Google Sheets
    # For now, return a hardcoded list of unit types
    return UNIT_TYPES

def get_player_units(player_id):
    """
    Get units owned by a player.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        list: Player's units
    """
    try:
        units_data = get_sheet_data(SHEET_NAMES['units'])
        return [u for u in units_data if str(u.get('player_id')) == str(player_id)]
    except Exception as e:
        logger.error(f"Error getting player units: {e}")
        return []

def train_units(player_id, unit_id, count=1):
    """
    Train new units.
    
    Args:
        player_id: Telegram user ID
        unit_id: Type of unit to train
        count: Number of units to train
        
    Returns:
        dict: Result of the training attempt
    """
    try:
        # Get player data
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Get unit type definition
        unit_types = get_units()
        unit_type = next((u for u in unit_types if u.get('id') == unit_id), None)
        
        if not unit_type:
            return {
                'success': False,
                'message': f"Unknown unit type: {unit_id}"
            }
        
        # Check if player has enough resources
        cost_credits = unit_type.get('cost_credits', 0) * count
        cost_minerals = unit_type.get('cost_minerals', 0) * count
        cost_energy = unit_type.get('cost_energy', 0) * count
        
        player_credits = player.get('credits', 0)
        player_minerals = player.get('minerals', 0)
        player_energy = player.get('energy', 0)
        
        if player_credits < cost_credits:
            return {
                'success': False,
                'message': f"Not enough credits. Need {cost_credits}, have {player_credits}."
            }
        
        if player_minerals < cost_minerals:
            return {
                'success': False,
                'message': f"Not enough minerals. Need {cost_minerals}, have {player_minerals}."
            }
        
        if player_energy < cost_energy:
            return {
                'success': False,
                'message': f"Not enough energy. Need {cost_energy}, have {player_energy}."
            }
        
        # Deduct resources
        update_player(player_id, {
            'credits': player_credits - cost_credits,
            'minerals': player_minerals - cost_minerals,
            'energy': player_energy - cost_energy
        })
        
        # Add units
        now = datetime.datetime.utcnow()
        
        # Calculate training time (could be more complex in a full implementation)
        train_time_seconds = unit_type.get('train_time', 30)  # Default 30 seconds
        completion_time = now + datetime.timedelta(seconds=train_time_seconds)
        
        # In a full implementation, we might add multiple unit records or use a count field
        unit_data = {
            'player_id': str(player_id),
            'unit_id': unit_id,
            'unit_name': unit_type.get('name'),
            'count': count,
            'status': 'training',
            'started_at': now.isoformat(),
            'completes_at': completion_time.isoformat()
        }
        
        append_sheet_data(SHEET_NAMES['units'], [unit_data])
        
        return {
            'success': True,
            'unit_name': unit_type.get('name'),
            'count': count
        }
    except Exception as e:
        logger.error(f"Error training units: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }

def evolve_unit(player_id, unit_id):
    """
    Evolve a unit to a stronger version.
    
    Args:
        player_id: Telegram user ID
        unit_id: ID of unit to evolve
        
    Returns:
        dict: Result of the evolution attempt
    """
    # In a full implementation, this would handle unit evolution mechanics
    return {
        'success': False,
        'message': "Unit evolution not implemented yet"
    }
