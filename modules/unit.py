"""
Unit module for the SkyHustle Telegram bot.
Handles unit training, management, and combat.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from modules.player import get_player, Player
from modules.sheets_service import get_sheet, update_sheet_row, append_sheet_row, find_row_by_col_value
from modules.building import has_building

# Unit definitions (would normally be loaded from sheet but hardcoded for simplicity)
UNITS = {
    "drone": {
        "name": "Reconnaissance Drone",
        "description": "Small aerial unit for scouting",
        "cost": 50,
        "minerals": 20,
        "energy": 10,
        "training_time": 60,  # seconds
        "attack": 5,
        "defense": 10,
        "speed": 8,
        "requirements": ["command_center"]
    },
    "fighter": {
        "name": "Sky Fighter",
        "description": "Light combat aircraft",
        "cost": 150,
        "minerals": 75,
        "energy": 25,
        "training_time": 120,
        "attack": 30,
        "defense": 20,
        "speed": 6,
        "requirements": ["barracks"]
    },
    "bomber": {
        "name": "Heavy Bomber",
        "description": "Slow but powerful bombing aircraft",
        "cost": 250,
        "minerals": 125,
        "energy": 50,
        "training_time": 180,
        "attack": 50,
        "defense": 15,
        "speed": 4,
        "requirements": ["factory"]
    },
    "interceptor": {
        "name": "Interceptor",
        "description": "Fast defensive aircraft",
        "cost": 200,
        "minerals": 100,
        "energy": 40,
        "training_time": 150,
        "attack": 25,
        "defense": 40,
        "speed": 7,
        "requirements": ["barracks", "generator"]
    },
    "gunship": {
        "name": "Assault Gunship",
        "description": "Heavily armed assault aircraft",
        "cost": 350,
        "minerals": 175,
        "energy": 70,
        "training_time": 240,
        "attack": 70,
        "defense": 30,
        "speed": 5,
        "requirements": ["factory", "generator"]
    },
    "titan": {
        "name": "Aerial Titan",
        "description": "Massive aerial fortress",
        "cost": 800,
        "minerals": 400,
        "energy": 150,
        "training_time": 600,
        "attack": 100,
        "defense": 80,
        "speed": 2,
        "requirements": ["factory", "lab"]
    }
}

class Unit:
    """
    Unit class for SkyHustle.
    Represents a player's unit.
    
    Attributes:
        unit_id: The ID of the unit type
        player_id: The player who owns the unit
        quantity: The number of this unit owned
        level: The level/rank of the unit
    """
    def __init__(
        self,
        unit_id: str,
        player_id: int,
        quantity: int = 1,
        level: int = 1,
        row_index: Optional[int] = None
    ):
        self.unit_id = unit_id
        self.player_id = player_id
        self.quantity = quantity
        self.level = level
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert unit to dictionary for storage."""
        return {
            "unit_id": self.unit_id,
            "player_id": str(self.player_id),
            "quantity": self.quantity,
            "level": self.level
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Unit':
        """Create a Unit object from a sheet row."""
        return cls(
            unit_id=row[0],
            player_id=int(row[1]),
            quantity=int(row[2]) if row[2] else 1,
            level=int(row[3]) if len(row) > 3 and row[3] else 1,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save unit to the sheet."""
        unit_data = await self.to_dict()
        unit_row = list(unit_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("Units", self.row_index, unit_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("Units", unit_row)

class TrainingQueue:
    """
    TrainingQueue class for SkyHustle.
    Represents a unit training queue item.
    
    Attributes:
        queue_id: Unique identifier for this queue item
        player_id: The player who queued the training
        unit_id: The unit being trained
        start_time: When training started
        end_time: When training will finish
        quantity: Number of units to train
        completed: Number of units completed
    """
    def __init__(
        self,
        queue_id: int,
        player_id: int,
        unit_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int = 1,
        completed: int = 0,
        row_index: Optional[int] = None
    ):
        self.queue_id = queue_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.start_time = start_time
        self.end_time = end_time
        self.quantity = quantity
        self.completed = completed
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert training queue to dictionary for storage."""
        return {
            "queue_id": self.queue_id,
            "player_id": str(self.player_id),
            "unit_id": self.unit_id,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "quantity": self.quantity,
            "completed": self.completed
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'TrainingQueue':
        """Create a TrainingQueue object from a sheet row."""
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(minutes=5)
        
        try:
            start_time = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        except (ValueError, IndexError):
            logging.warning(f"Invalid time format for training queue {row[0]}")
        
        return cls(
            queue_id=int(row[0]),
            player_id=int(row[1]),
            unit_id=row[2],
            start_time=start_time,
            end_time=end_time,
            quantity=int(row[5]) if len(row) > 5 and row[5] else 1,
            completed=int(row[6]) if len(row) > 6 and row[6] else 0,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save training queue to the sheet."""
        queue_data = await self.to_dict()
        queue_row = list(queue_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("TrainingQueue", self.row_index, queue_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("TrainingQueue", queue_row)

async def get_unit_info(unit_id: str) -> Dict[str, Any]:
    """
    Get information about a unit type.
    
    Args:
        unit_id: The ID of the unit type
    
    Returns:
        Dictionary with unit information
    """
    if unit_id in UNITS:
        return UNITS[unit_id]
    else:
        raise ValueError(f"Unit type {unit_id} not found")

async def get_player_units(player_id: int) -> List[Unit]:
    """
    Get all units owned by a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of Unit objects
    """
    sheet = await get_sheet("Units")
    player_id_str = str(player_id)
    
    units = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == player_id_str:
            unit = await Unit.from_row(row, i + 1)  # +1 for header row
            units.append(unit)
    
    return units

async def get_player_unit(player_id: int, unit_id: str) -> Optional[Unit]:
    """
    Get a specific unit owned by a player.
    
    Args:
        player_id: The player ID
        unit_id: The unit ID
    
    Returns:
        Unit object or None if not found
    """
    units = await get_player_units(player_id)
    for unit in units:
        if unit.unit_id == unit_id:
            return unit
    return None

async def get_next_queue_id() -> int:
    """
    Get the next available training queue ID.
    
    Returns:
        Next available queue ID
    """
    sheet = await get_sheet("TrainingQueue")
    
    if not sheet["values"] or len(sheet["values"]) <= 1:
        return 1
    
    # Skip header row
    queue_ids = [int(row[0]) for row in sheet["values"][1:] if row and row[0].isdigit()]
    
    if not queue_ids:
        return 1
    
    return max(queue_ids) + 1

async def get_training_queue(player_id: int) -> List[TrainingQueue]:
    """
    Get the training queue for a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of TrainingQueue objects
    """
    sheet = await get_sheet("TrainingQueue")
    player_id_str = str(player_id)
    
    queue_items = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == player_id_str:
            queue_item = await TrainingQueue.from_row(row, i + 1)  # +1 for header row
            queue_items.append(queue_item)
    
    # Sort by end time
    queue_items.sort(key=lambda x: x.end_time)
    
    return queue_items

async def train_units(player_id: int, unit_id: str, count: int = 1) -> Dict[str, Any]:
    """
    Queue units for training.
    
    Args:
        player_id: The player who is training
        unit_id: The unit to train
        count: Number of units to train
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Get unit info
        unit_info = await get_unit_info(unit_id)
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        total_cost = unit_info["cost"] * count
        total_minerals = unit_info["minerals"] * count
        total_energy = unit_info["energy"] * count
        
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
        
        # Check unit requirements
        for req_building_id in unit_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                return {
                    "success": False,
                    "message": f"Requires {req_building_id} to train {unit_info['name']}."
                }
        
        # Check queue length
        current_queue = await get_training_queue(player_id)
        if len(current_queue) >= 5:
            return {
                "success": False,
                "message": "Training queue is full (max 5 items)."
            }
        
        # Calculate training times
        now = datetime.now()
        training_time_seconds = unit_info["training_time"]
        
        # If queue exists, add to the end of the queue
        if current_queue:
            last_item = current_queue[-1]
            start_time = last_item.end_time
        else:
            start_time = now
        
        end_time = start_time + timedelta(seconds=training_time_seconds * count)
        
        # Create queue item
        queue_id = await get_next_queue_id()
        queue_item = TrainingQueue(
            queue_id=queue_id,
            player_id=player_id,
            unit_id=unit_id,
            start_time=start_time,
            end_time=end_time,
            quantity=count,
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
            "message": f"Queued {count}x {unit_info['name']} for training."
        }
        
    except Exception as e:
        logging.error(f"Error training units: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def get_available_units(player_id: int) -> List[Dict[str, Any]]:
    """
    Get units available to a player for training.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of available units with their details
    """
    try:
        available_units = []
        
        for unit_id, unit in UNITS.items():
            # Check if unit requirements are met
            requirements_met = True
            for req_building_id in unit["requirements"]:
                if not await has_building(player_id, req_building_id):
                    requirements_met = False
                    break
            
            if requirements_met:
                available_units.append({
                    "id": unit_id,
                    "name": unit["name"],
                    "description": unit["description"],
                    "cost": unit["cost"],
                    "minerals": unit["minerals"],
                    "energy": unit["energy"],
                    "training_time": unit["training_time"],
                    "attack": unit["attack"],
                    "defense": unit["defense"],
                    "speed": unit["speed"]
                })
        
        return available_units
        
    except Exception as e:
        logging.error(f"Error getting available units: {e}", exc_info=True)
        return []

async def complete_training(player_id: int) -> List[Dict[str, Any]]:
    """
    Complete any finished training queue items for a player.
    
    Args:
        player_id: The player ID
    
    Returns:
        List of completed training items
    """
    try:
        # Get player's training queue
        queue_items = await get_training_queue(player_id)
        
        now = datetime.now()
        completed_items = []
        
        for item in queue_items:
            if item.end_time <= now and item.completed < item.quantity:
                # Get the unit being trained
                unit = await get_player_unit(player_id, item.unit_id)
                
                # Get unit info for the message
                unit_info = await get_unit_info(item.unit_id)
                
                # Update or create unit
                if unit:
                    unit.quantity += (item.quantity - item.completed)
                    await unit.save()
                else:
                    unit = Unit(
                        unit_id=item.unit_id,
                        player_id=player_id,
                        quantity=item.quantity - item.completed
                    )
                    await unit.save()
                
                # Mark as completed
                item.completed = item.quantity
                await item.save()
                
                # Add to completed items
                completed_items.append({
                    "unit_id": item.unit_id,
                    "name": unit_info["name"],
                    "quantity": item.quantity
                })
        
        return completed_items
        
    except Exception as e:
        logging.error(f"Error completing training: {e}", exc_info=True)
        return []
