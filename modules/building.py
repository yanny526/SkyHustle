"""
Building module for SkyHustle.
Handles building data, construction, and upgrades.
"""
import logging
import datetime
from utils.sheets_service import (
    get_sheet_data, update_sheet_data, append_sheet_data
)
from utils.constants import BUILDING_TYPES
from config import SHEET_NAMES, MAX_BUILD_QUEUE_LENGTH
from modules.player import get_player, update_player

logger = logging.getLogger(__name__)

def get_buildings():
    """
    Get available building types.
    
    Returns:
        list: Building type definitions
    """
    # In a full implementation, this would read from Google Sheets
    # For now, return a hardcoded list of building types
    return BUILDING_TYPES

def get_player_buildings(player_id):
    """
    Get buildings owned by a player.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        list: Player's buildings
    """
    try:
        buildings_data = get_sheet_data(SHEET_NAMES['buildings'])
        return [b for b in buildings_data if str(b.get('player_id')) == str(player_id)]
    except Exception as e:
        logger.error(f"Error getting player buildings: {e}")
        return []

def get_building_queue(player_id):
    """
    Get the current building construction queue for a player.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        list: Building queue items
    """
    try:
        buildings_data = get_sheet_data(SHEET_NAMES['buildings'])
        queue = [b for b in buildings_data if str(b.get('player_id')) == str(player_id) and b.get('status') == 'queued']
        # Sort by queue position
        return sorted(queue, key=lambda b: b.get('queue_position', 0))
    except Exception as e:
        logger.error(f"Error getting building queue: {e}")
        return []

def add_building_to_queue(player_id, building_id, quantity=1):
    """
    Add a building to the construction queue.
    
    Args:
        player_id: Telegram user ID
        building_id: Type of building to construct
        quantity: Number of buildings to queue
        
    Returns:
        dict: Result of the queue attempt
    """
    try:
        # Get player data
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Get building type definition
        building_types = get_buildings()
        building_type = next((b for b in building_types if b.get('id') == building_id), None)
        
        if not building_type:
            return {
                'success': False,
                'message': f"Unknown building type: {building_id}"
            }
        
        # Check current queue length
        queue = get_building_queue(player_id)
        if len(queue) >= MAX_BUILD_QUEUE_LENGTH:
            return {
                'success': False,
                'message': f"Build queue full. Maximum {MAX_BUILD_QUEUE_LENGTH} items allowed."
            }
        
        # Check if player has enough resources
        cost_credits = building_type.get('cost_credits', 0) * quantity
        cost_minerals = building_type.get('cost_minerals', 0) * quantity
        cost_energy = building_type.get('cost_energy', 0) * quantity
        
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
        
        # Add building to queue
        now = datetime.datetime.utcnow()
        
        for i in range(quantity):
            # Calculate build time (could be more complex in a full implementation)
            build_time_seconds = building_type.get('build_time', 60)  # Default 60 seconds
            completion_time = now + datetime.timedelta(seconds=build_time_seconds)
            
            building_data = {
                'player_id': str(player_id),
                'building_id': building_id,
                'building_name': building_type.get('name'),
                'level': 1,
                'status': 'queued',
                'queue_position': len(queue) + i + 1,
                'started_at': now.isoformat(),
                'completes_at': completion_time.isoformat()
            }
            
            append_sheet_data(SHEET_NAMES['buildings'], [building_data])
        
        return {
            'success': True,
            'building_name': building_type.get('name')
        }
    except Exception as e:
        logger.error(f"Error adding building to queue: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }
