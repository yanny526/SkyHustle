"""
Research module for SkyHustle.
Handles technology research and unlock mechanics.
"""
import logging
import datetime
from utils.sheets_service import (
    get_sheet_data, update_sheet_data, append_sheet_data
)
from utils.constants import TECH_TREE
from config import SHEET_NAMES
from modules.player import get_player, update_player

logger = logging.getLogger(__name__)

def get_tech_tree():
    """
    Get the technology research tree.
    
    Returns:
        list: Technology definitions
    """
    # In a full implementation, this would read from Google Sheets
    # For now, return a hardcoded technology tree
    return TECH_TREE

def get_player_research(player_id):
    """
    Get technologies researched by a player.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        list: Player's researched technologies
    """
    try:
        research_data = get_sheet_data(SHEET_NAMES['research'])
        return [r for r in research_data if str(r.get('player_id')) == str(player_id)]
    except Exception as e:
        logger.error(f"Error getting player research: {e}")
        return []

def has_tech_prerequisites(player_id, tech_id):
    """
    Check if player has all prerequisites for a technology.
    
    Args:
        player_id: Telegram user ID
        tech_id: Technology ID to check
        
    Returns:
        bool: True if all prerequisites are met, False otherwise
    """
    try:
        tech_tree = get_tech_tree()
        tech = next((t for t in tech_tree if t.get('id') == tech_id), None)
        
        if not tech:
            return False
        
        prerequisites = tech.get('prerequisites', [])
        if not prerequisites:
            return True  # No prerequisites
        
        player_research = get_player_research(player_id)
        researched_ids = [r.get('tech_id') for r in player_research if r.get('status') == 'completed']
        
        # Check if all prerequisites are researched
        return all(prereq in researched_ids for prereq in prerequisites)
    except Exception as e:
        logger.error(f"Error checking tech prerequisites: {e}")
        return False

def research_technology(player_id, tech_id):
    """
    Research a new technology.
    
    Args:
        player_id: Telegram user ID
        tech_id: Technology ID to research
        
    Returns:
        dict: Result of the research attempt
    """
    try:
        player = get_player(player_id)
        if not player:
            return {
                'success': False,
                'message': "Player not found"
            }
        
        # Check if technology exists
        tech_tree = get_tech_tree()
        tech = next((t for t in tech_tree if t.get('id') == tech_id), None)
        
        if not tech:
            return {
                'success': False,
                'message': f"Unknown technology: {tech_id}"
            }
        
        # Check if already researched
        player_research = get_player_research(player_id)
        for research in player_research:
            if research.get('tech_id') == tech_id:
                if research.get('status') == 'completed':
                    return {
                        'success': False,
                        'message': f"You have already researched {tech['name']}."
                    }
                elif research.get('status') == 'in_progress':
                    return {
                        'success': False,
                        'message': f"You are already researching {tech['name']}."
                    }
        
        # Check prerequisites
        if not has_tech_prerequisites(player_id, tech_id):
            return {
                'success': False,
                'message': "You haven't researched the required prerequisites for this technology."
            }
        
        # Check if player has enough resources
        cost_credits = tech.get('cost_credits', 0)
        cost_minerals = tech.get('cost_minerals', 0)
        cost_energy = tech.get('cost_energy', 0)
        
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
        
        # Start research
        now = datetime.datetime.utcnow()
        
        # Calculate research time (could be more complex in a full implementation)
        research_time_seconds = tech.get('research_time', 300)  # Default 5 minutes
        completion_time = now + datetime.timedelta(seconds=research_time_seconds)
        
        research_data = {
            'player_id': str(player_id),
            'tech_id': tech_id,
            'tech_name': tech.get('name'),
            'status': 'in_progress',
            'started_at': now.isoformat(),
            'completes_at': completion_time.isoformat()
        }
        
        append_sheet_data(SHEET_NAMES['research'], [research_data])
        
        return {
            'success': True,
            'tech_name': tech.get('name'),
            'completion_time': completion_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error researching technology: {e}")
        return {
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }
