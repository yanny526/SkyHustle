"""
Research module for the SkyHustle Telegram bot.
Handles research technologies and their effects.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from modules.player import get_player, Player
from modules.sheets_service import get_sheet, update_sheet_row, append_sheet_row, find_row_by_col_value
from modules.building import has_building

# Technology definitions (would normally be loaded from sheet but hardcoded for simplicity)
TECHNOLOGIES = {
    "advanced_materials": {
        "name": "Advanced Materials",
        "description": "Stronger building materials for your structures",
        "cost": 300,
        "minerals": 150,
        "energy": 100,
        "research_time": 300,  # seconds
        "requirements": ["lab"],
        "effects": {"building_health": 1.2}
    },
    "energy_efficiency": {
        "name": "Energy Efficiency",
        "description": "More efficient use of energy",
        "cost": 250,
        "minerals": 100,
        "energy": 50,
        "research_time": 240,
        "requirements": ["lab", "generator"],
        "effects": {"energy_production": 1.25}
    },
    "advanced_propulsion": {
        "name": "Advanced Propulsion",
        "description": "Faster and more maneuverable units",
        "cost": 350,
        "minerals": 175,
        "energy": 125,
        "research_time": 360,
        "requirements": ["lab"],
        "effects": {"unit_speed": 1.2}
    },
    "weapons_research": {
        "name": "Weapons Research",
        "description": "More powerful weapons for your units",
        "cost": 400,
        "minerals": 200,
        "energy": 150,
        "research_time": 420,
        "requirements": ["lab"],
        "effects": {"unit_attack": 1.25}
    },
    "defensive_systems": {
        "name": "Defensive Systems",
        "description": "Improved defenses for your base and units",
        "cost": 375,
        "minerals": 175,
        "energy": 125,
        "research_time": 390,
        "requirements": ["lab", "turret"],
        "effects": {"defense_bonus": 1.3}
    },
    "mineral_processing": {
        "name": "Mineral Processing",
        "description": "More efficient mineral extraction and processing",
        "cost": 300,
        "minerals": 100,
        "energy": 75,
        "research_time": 300,
        "requirements": ["lab", "refinery"],
        "effects": {"mineral_production": 1.25}
    },
    "economy_optimization": {
        "name": "Economy Optimization",
        "description": "Improved credit generation",
        "cost": 275,
        "minerals": 125,
        "energy": 100,
        "research_time": 270,
        "requirements": ["lab", "command_center"],
        "effects": {"credit_production": 1.2}
    },
    "advanced_shield_tech": {
        "name": "Advanced Shield Technology",
        "description": "More powerful protective shields",
        "cost": 450,
        "minerals": 225,
        "energy": 175,
        "research_time": 450,
        "requirements": ["lab", "shield"],
        "effects": {"shield_strength": 1.3}
    }
}

class Research:
    """
    Research class for SkyHustle.
    Represents a player's researched technology.
    
    Attributes:
        tech_id: The ID of the technology
        player_id: The player who researched the technology
        level: The level of the technology
    """
    def __init__(
        self,
        tech_id: str,
        player_id: int,
        level: int = 1,
        completed_at: Optional[datetime] = None,
        row_index: Optional[int] = None
    ):
        self.tech_id = tech_id
        self.player_id = player_id
        self.level = level
        self.completed_at = completed_at or datetime.now()
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert research to dictionary for storage."""
        return {
            "tech_id": self.tech_id,
            "player_id": str(self.player_id),
            "level": self.level,
            "completed_at": self.completed_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Research':
        """Create a Research object from a sheet row."""
        completed_at = datetime.now()
        if len(row) > 3 and row[3]:
            try:
                completed_at = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logging.warning(f"Invalid completed_at format for research {row[0]}")
        
        return cls(
            tech_id=row[0],
            player_id=int(row[1]),
            level=int(row[2]) if row[2] else 1,
            completed_at=completed_at,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save research to the sheet."""
        research_data = await self.to_dict()
        research_row = list(research_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("Research", self.row_index, research_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("Research", research_row)

async def get_research_info(tech_id: str) -> Dict[str, Any]:
    """
    Get information about a technology.
    
    Args:
        tech_id: The ID of the technology
    
    Returns:
        Dictionary with technology information
    """
    if tech_id in TECHNOLOGIES:
        return TECHNOLOGIES[tech_id]
    else:
        raise ValueError(f"Technology {tech_id} not found")

async def get_player_research(player_id: int) -> List[Research]:
    """
    Get all research completed by a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of Research objects
    """
    sheet = await get_sheet("Research")
    player_id_str = str(player_id)
    
    research_list = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == player_id_str:
            research = await Research.from_row(row, i + 1)  # +1 for header row
            research_list.append(research)
    
    return research_list

async def has_research(player_id: int, tech_id: str) -> bool:
    """
    Check if a player has researched a specific technology.
    
    Args:
        player_id: The player ID
        tech_id: The technology ID to check
    
    Returns:
        True if the player has the technology, False otherwise
    """
    player_research = await get_player_research(player_id)
    return any(r.tech_id == tech_id for r in player_research)

async def research_technology(player_id: int, tech_id: str) -> Dict[str, Any]:
    """
    Research a new technology.
    
    Args:
        player_id: The player who is researching
        tech_id: The technology to research
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Get technology info
        tech_info = await get_research_info(tech_id)
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        if player.credits < tech_info["cost"]:
            return {
                "success": False,
                "message": f"Not enough credits. Need {tech_info['cost']}, have {player.credits}."
            }
        
        if player.minerals < tech_info["minerals"]:
            return {
                "success": False,
                "message": f"Not enough minerals. Need {tech_info['minerals']}, have {player.minerals}."
            }
        
        if player.energy < tech_info["energy"]:
            return {
                "success": False,
                "message": f"Not enough energy. Need {tech_info['energy']}, have {player.energy}."
            }
        
        # Check technology requirements
        for req_building_id in tech_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                return {
                    "success": False,
                    "message": f"Requires {req_building_id} to research {tech_info['name']}."
                }
        
        # Check if already researched
        if await has_research(player_id, tech_id):
            return {
                "success": False,
                "message": f"You have already researched {tech_info['name']}."
            }
        
        # Create research
        research = Research(
            tech_id=tech_id,
            player_id=player_id,
            level=1,
            completed_at=datetime.now()
        )
        
        # Save research
        await research.save()
        
        # Deduct resources
        player.credits -= tech_info["cost"]
        player.minerals -= tech_info["minerals"]
        player.energy -= tech_info["energy"]
        
        # Add experience for completing research
        player.experience += tech_info["cost"] // 10
        
        # Save player
        await player.save()
        
        return {
            "success": True,
            "message": f"Successfully researched {tech_info['name']}!"
        }
        
    except Exception as e:
        logging.error(f"Error researching technology: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def get_available_technologies(player_id: int) -> List[Dict[str, Any]]:
    """
    Get technologies available to a player for research.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of available technologies with their details
    """
    try:
        # Get player's research
        player_research = await get_player_research(player_id)
        researched_techs = [r.tech_id for r in player_research]
        
        # Check which technologies are available
        available_techs = []
        for tech_id, tech in TECHNOLOGIES.items():
            # Skip already researched techs
            if tech_id in researched_techs:
                continue
            
            # Check if tech requirements are met
            requirements_met = True
            for req_building_id in tech["requirements"]:
                if not await has_building(player_id, req_building_id):
                    requirements_met = False
                    break
            
            if requirements_met:
                available_techs.append({
                    "id": tech_id,
                    "name": tech["name"],
                    "description": tech["description"],
                    "cost": tech["cost"],
                    "minerals": tech["minerals"],
                    "energy": tech["energy"],
                    "research_time": tech["research_time"]
                })
        
        return available_techs
        
    except Exception as e:
        logging.error(f"Error getting available technologies: {e}", exc_info=True)
        return []
