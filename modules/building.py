"""
Building module for the SkyHustle Telegram bot.
Handles building creation, queuing, and management.
"""
import logging
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

from modules.player import get_player, Player
from modules.sheets_service import get_sheet, update_sheet_row, append_sheet_row, find_row_by_col_value

# Building definitions (would normally be loaded from sheet but hardcoded for simplicity)
BUILDINGS = {
    "command_center": {
        "name": "Command Center",
        "description": "Central command facility for your aerial base",
        "cost": 500,
        "minerals": 250,
        "energy": 100,
        "build_time": 300,  # seconds
        "requirements": [],
        "provides": {"credits_per_hour": 50}
    },
    "barracks": {
        "name": "Barracks",
        "description": "Training facility for basic infantry units",
        "cost": 300,
        "minerals": 150,
        "energy": 50,
        "build_time": 180,
        "requirements": ["command_center"],
        "provides": {"max_infantry": 10}
    },
    "factory": {
        "name": "Factory",
        "description": "Production facility for vehicles and mechs",
        "cost": 450,
        "minerals": 200,
        "energy": 75,
        "build_time": 240,
        "requirements": ["barracks"],
        "provides": {"max_vehicles": 8}
    },
    "generator": {
        "name": "Energy Generator",
        "description": "Produces energy for your base",
        "cost": 200,
        "minerals": 100,
        "energy": 0,
        "build_time": 120,
        "requirements": ["command_center"],
        "provides": {"energy_per_hour": 25}
    },
    "lab": {
        "name": "Research Lab",
        "description": "Facility for researching new technologies",
        "cost": 400,
        "minerals": 200,
        "energy": 100,
        "build_time": 300,
        "requirements": ["command_center"],
        "provides": {"research_speed": 1.2}
    },
    "turret": {
        "name": "Defense Turret",
        "description": "Automated defense system for your base",
        "cost": 250,
        "minerals": 150,
        "energy": 50,
        "build_time": 150,
        "requirements": ["command_center"],
        "provides": {"defense": 50}
    },
    "refinery": {
        "name": "Mineral Refinery",
        "description": "Processes and refines minerals",
        "cost": 350,
        "minerals": 50,
        "energy": 75,
        "build_time": 210,
        "requirements": ["command_center"],
        "provides": {"minerals_per_hour": 20}
    },
    "shield": {
        "name": "Shield Generator",
        "description": "Generates a protective shield for your base",
        "cost": 600,
        "minerals": 300,
        "energy": 150,
        "build_time": 360,
        "requirements": ["generator", "turret"],
        "provides": {"shield": 100}
    }
}

class Building:
    """
    Building class for SkyHustle.
    Represents a player's building.
    
    Attributes:
        building_id: The ID of the building
        player_id: The player who owns the building
        level: The level of the building
        position: The position of the building in the base
    """
    def __init__(
        self,
        building_id: str,
        player_id: int,
        level: int = 1,
        position: Optional[Tuple[int, int]] = None,
        row_index: Optional[int] = None
    ):
        self.building_id = building_id
        self.player_id = player_id
        self.level = level
        self.position = position or (0, 0)
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert building to dictionary for storage."""
        return {
            "building_id": self.building_id,
            "player_id": str(self.player_id),
            "level": self.level,
            "position_x": self.position[0],
            "position_y": self.position[1]
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Building':
        """Create a Building object from a sheet row."""
        position = (0, 0)
        if len(row) > 3:
            position = (int(row[3]) if row[3] else 0, int(row[4]) if row[4] else 0)
        
        return cls(
            building_id=row[0],
            player_id=int(row[1]),
            level=int(row[2]) if row[2] else 1,
            position=position,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save building to the sheet."""
        building_data = await self.to_dict()
        building_row = list(building_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("Buildings", self.row_index, building_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("Buildings", building_row)

class BuildQueue:
    """
    BuildQueue class for SkyHustle.
    Represents a building construction queue item.
    
    Attributes:
        queue_id: Unique identifier for this queue item
        player_id: The player who queued the building
        building_id: The building being constructed
        start_time: When construction started
        end_time: When construction will finish
        quantity: Number of buildings to construct
        completed: Number of buildings completed
    """
    def __init__(
        self,
        queue_id: int,
        player_id: int,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int = 1,
        completed: int = 0,
        row_index: Optional[int] = None
    ):
        self.queue_id = queue_id
        self.player_id = player_id
        self.building_id = building_id
        self.start_time = start_time
        self.end_time = end_time
        self.quantity = quantity
        self.completed = completed
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert build queue to dictionary for storage."""
        return {
            "queue_id": self.queue_id,
            "player_id": str(self.player_id),
            "building_id": self.building_id,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "quantity": self.quantity,
            "completed": self.completed
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'BuildQueue':
        """Create a BuildQueue object from a sheet row."""
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(minutes=5)
        
        try:
            start_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        except (ValueError, IndexError):
            logging.warning(f"Invalid time format for build queue {row[0]}")
        
        return cls(
            queue_id=int(row[0]),
            player_id=int(row[1]),
            building_id=row[2],
            start_time=start_time,
            end_time=end_time,
            quantity=int(row[5]) if len(row) > 5 and row[5] else 1,
            completed=int(row[6]) if len(row) > 6 and row[6] else 0,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save build queue to the sheet."""
        queue_data = await self.to_dict()
        queue_row = list(queue_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("BuildQueue", self.row_index, queue_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("BuildQueue", queue_row)

async def get_building_info(building_id: str) -> Dict[str, Any]:
    """
    Get information about a building type.
    
    Args:
        building_id: The ID of the building type
    
    Returns:
        Dictionary with building information
    """
    if building_id in BUILDINGS:
        return BUILDINGS[building_id]
    else:
        raise ValueError(f"Building type {building_id} not found")

async def get_player_buildings(player_id: int) -> List[Building]:
    """
    Get all buildings owned by a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of Building objects
    """
    sheet = await get_sheet("Buildings")
    player_id_str = str(player_id)
    
    buildings = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == player_id_str:
            building = await Building.from_row(row, i + 1)  # +1 for header row
            buildings.append(building)
    
    return buildings

async def has_building(player_id: int, building_id: str) -> bool:
    """
    Check if a player has a specific building.
    
    Args:
        player_id: The player ID
        building_id: The building ID to check
    
    Returns:
        True if the player has the building, False otherwise
    """
    player_buildings = await get_player_buildings(player_id)
    return any(b.building_id == building_id for b in player_buildings)

async def get_next_queue_id() -> int:
    """
    Get the next available build queue ID.
    
    Returns:
        Next available queue ID
    """
    sheet = await get_sheet("BuildQueue")
    
    if not sheet["values"] or len(sheet["values"]) <= 1:
        return 1
    
    # Skip header row
    queue_ids = [int(row[0]) for row in sheet["values"][1:] if row and row[0].isdigit()]
    
    if not queue_ids:
        return 1
    
    return max(queue_ids) + 1

async def get_build_queue(player_id: int) -> List[BuildQueue]:
    """
    Get the build queue for a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of BuildQueue objects
    """
    sheet = await get_sheet("BuildQueue")
    player_id_str = str(player_id)
    
    queue_items = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == player_id_str:
            queue_item = await BuildQueue.from_row(row, i + 1)  # +1 for header row
            queue_items.append(queue_item)
    
    # Sort by end time
    queue_items.sort(key=lambda x: x.end_time)
    
    return queue_items

async def queue_building(player_id: int, building_id: str, quantity: int = 1) -> Dict[str, Any]:
    """
    Queue a building for construction.
    
    Args:
        player_id: The player who is building
        building_id: The building to construct
        quantity: Number of buildings to construct
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Get building info
        building_info = await get_building_info(building_id)
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        total_cost = building_info["cost"] * quantity
        total_minerals = building_info["minerals"] * quantity
        total_energy = building_info["energy"] * quantity
        
        if player.credits < total_cost:
            return {
                "success": False,
                "message": f"Not enough credits. Need {total_cost}, have {player.credits}."
            }
        
        if player.minerals < total_minerals:
            return {
                "success": False,
                "message": f"Not enough minerals. Need {total_minerals}, have {player.minerals}."
            }
        
        if player.energy < total_energy:
            return {
                "success": False,
                "message": f"Not enough energy. Need {total_energy}, have {player.energy}."
            }
        
        # Check building requirements
        for req_building_id in building_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                req_name = BUILDINGS[req_building_id]["name"]
                return {
                    "success": False,
                    "message": f"Requires {req_name} to build {building_info['name']}."
                }
        
        # Check queue length
        current_queue = await get_build_queue(player_id)
        if len(current_queue) >= 5:
            return {
                "success": False,
                "message": "Build queue is full (max 5 items)."
            }
        
        # Calculate build times
        now = datetime.now()
        build_time_seconds = building_info["build_time"]
        
        # If queue exists, add to the end of the queue
        if current_queue:
            last_item = current_queue[-1]
            start_time = last_item.end_time
        else:
            start_time = now
        
        end_time = start_time + timedelta(seconds=build_time_seconds * quantity)
        
        # Create queue item
        queue_id = await get_next_queue_id()
        queue_item = BuildQueue(
            queue_id=queue_id,
            player_id=player_id,
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            quantity=quantity,
            completed=0
        )
        
        # Save queue item
        await queue_item.save()
        
        # Deduct resources
        player.credits -= total_cost
        player.minerals -= total_minerals
        player.energy -= total_energy
        
        # Save player
        await player.save()
        
        return {
            "success": True,
            "message": f"Queued {quantity}x {building_info['name']} for construction."
        }
        
    except Exception as e:
        logging.error(f"Error queueing building: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def get_available_buildings(player_id: int) -> List[Dict[str, Any]]:
    """
    Get buildings available to a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of available buildings with their details
    """
    try:
        # Get player's buildings
        player_buildings = await get_player_buildings(player_id)
        player_building_ids = [b.building_id for b in player_buildings]
        
        # Check which buildings are available
        available_buildings = []
        for building_id, building in BUILDINGS.items():
            # Check if building requirements are met
            requirements_met = True
            for req_building_id in building["requirements"]:
                if req_building_id not in player_building_ids:
                    requirements_met = False
                    break
            
            if requirements_met:
                available_buildings.append({
                    "id": building_id,
                    "name": building["name"],
                    "description": building["description"],
                    "cost": building["cost"],
                    "minerals": building["minerals"],
                    "energy": building["energy"],
                    "build_time": building["build_time"],
                    "already_owned": building_id in player_building_ids
                })
        
        return available_buildings
        
    except Exception as e:
        logging.error(f"Error getting available buildings: {e}", exc_info=True)
        return []
