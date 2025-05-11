"""
Units module for SkyHustle
Handles unit training and management
"""
import logging
from datetime import datetime, timedelta

from constants import UNITS, MAX_QUEUE_LENGTH
from modules.player import get_player, update_player
from modules.buildings import get_player_buildings
from modules.sheets_service import get_sheet, update_sheet, append_sheet
from utils.logger import get_logger

logger = get_logger(__name__)

# In-memory cache for units data
units_cache = {}
last_cache_update = {}

async def get_player_units(player_id):
    """Get all units for a player"""
    # Check cache first
    cache_key = f"units_{player_id}"
    cache_valid_time = 300  # 5 minutes
    
    # If cache is valid, return cached data
    if cache_key in units_cache and cache_key in last_cache_update:
        time_since_update = (datetime.now() - last_cache_update[cache_key]).total_seconds()
        if time_since_update < cache_valid_time:
            return units_cache[cache_key]
    
    # Get data from sheet
    sheet = await get_sheet("Units")
    
    player_units = []
    for row in sheet:
        if row.get("player_id") == player_id:
            unit_data = {
                "unit_id": row.get("unit_id"),
                "player_id": row.get("player_id"),
                "unit_type": row.get("unit_type"),
                "level": int(row.get("level", 1)),
                "quantity": int(row.get("quantity", 0)),
                "train_started": row.get("train_started"),
                "train_completed": row.get("train_completed")
            }
            player_units.append(unit_data)
    
    # Update cache
    units_cache[cache_key] = player_units
    last_cache_update[cache_key] = datetime.now()
    
    return player_units

async def get_available_units(player_id):
    """Get list of units available for training"""
    # Get player's current buildings
    player_buildings = await get_player_buildings(player_id)
    
    # Create a dict of existing building types and their levels
    existing_buildings = {}
    for building in player_buildings:
        # Skip buildings in construction queue
        if building.get("build_completed") and datetime.fromisoformat(building["build_completed"]) > datetime.now():
            continue
        
        building_type = building.get("building_type")
        level = building.get("level", 1)
        
        if building_type in existing_buildings:
            existing_buildings[building_type] = max(existing_buildings[building_type], level)
        else:
            existing_buildings[building_type] = level
    
    # Determine which units are available based on prerequisites
    available_units = []
    
    for unit_id, unit_data in UNITS.items():
        # Check prerequisites
        prerequisites_met = True
        
        for req_building, req_level in unit_data["prerequisites"].items():
            if req_building not in existing_buildings or existing_buildings[req_building] < req_level:
                prerequisites_met = False
                break
        
        if prerequisites_met:
            available_units.append(unit_id)
    
    return available_units

async def check_unit_prerequisites(player_id, unit_id):
    """Check if prerequisites are met for a unit"""
    if unit_id not in UNITS:
        return False
    
    # Get player's current buildings
    player_buildings = await get_player_buildings(player_id)
    
    # Create a dict of existing building types and their levels
    existing_buildings = {}
    for building in player_buildings:
        # Skip buildings in construction queue
        if building.get("build_completed") and datetime.fromisoformat(building["build_completed"]) > datetime.now():
            continue
        
        building_type = building.get("building_type")
        level = building.get("level", 1)
        
        if building_type in existing_buildings:
            existing_buildings[building_type] = max(existing_buildings[building_type], level)
        else:
            existing_buildings[building_type] = level
    
    # Check prerequisites
    prerequisites = UNITS[unit_id]["prerequisites"]
    for req_building, req_level in prerequisites.items():
        if req_building not in existing_buildings or existing_buildings[req_building] < req_level:
            return False
    
    return True

async def add_unit_to_queue(player_id, unit_id, quantity=1):
    """Add a unit to the training queue"""
    # Validate unit exists
    if unit_id not in UNITS:
        return {"success": False, "message": "Invalid unit type"}
    
    # Get player data
    player = await get_player(player_id)
    if not player:
        return {"success": False, "message": "Player not found"}
    
    # Check prerequisites
    if not await check_unit_prerequisites(player_id, unit_id):
        return {"success": False, "message": "Unit prerequisites not met"}
    
    # Get player's current units
    player_units = await get_player_units(player_id)
    
    # Check if training queue is full
    queue_count = 0
    for unit in player_units:
        if unit.get("train_completed") and datetime.fromisoformat(unit["train_completed"]) > datetime.now():
            queue_count += 1
    
    if queue_count >= MAX_QUEUE_LENGTH:
        return {"success": False, "message": f"Training queue is full. Maximum queue length is {MAX_QUEUE_LENGTH}"}
    
    # Calculate cost
    unit_info = UNITS[unit_id]
    base_cost = unit_info["base_cost"]
    
    # Calculate total cost
    total_cost = {}
    for resource, amount in base_cost.items():
        total_cost[resource] = int(amount * quantity)
    
    # Check if player has enough resources
    for resource, amount in total_cost.items():
        if player.get(resource, 0) < amount:
            return {"success": False, "message": f"Not enough {resource}. Need {amount}, have {player.get(resource, 0)}"}
    
    # Deduct resources
    resource_updates = {}
    for resource, amount in total_cost.items():
        resource_updates[resource] = player.get(resource, 0) - amount
    
    await update_player(player_id, resource_updates)
    
    # Calculate training time
    base_time = unit_info["train_time"]
    # Total time based on quantity
    total_time = base_time * quantity
    
    # Generate unique unit ID
    import uuid
    unit_unique_id = str(uuid.uuid4())
    
    # Calculate start and completion times
    now = datetime.now()
    train_completed = now + timedelta(seconds=total_time)
    
    # Add to queue
    new_unit = {
        "unit_id": unit_unique_id,
        "player_id": player_id,
        "unit_type": unit_id,
        "level": 1,  # New units start at level 1
        "quantity": quantity,
        "train_started": now.isoformat(),
        "train_completed": train_completed.isoformat()
    }
    
    await append_sheet("Units", [new_unit])
    
    # Update cache
    cache_key = f"units_{player_id}"
    if cache_key in units_cache:
        units_cache[cache_key].append(new_unit)
        last_cache_update[cache_key] = datetime.now()
    
    return {
        "success": True,
        "message": f"Training {quantity}x {unit_info['name']} started",
        "train_time": total_time,
        "cost": total_cost
    }

async def upgrade_unit(player_id, unit_id):
    """Upgrade an existing unit"""
    # Get player's units
    player_units = await get_player_units(player_id)
    
    # Find the unit to upgrade
    target_unit = None
    for unit in player_units:
        if unit.get("unit_id") == unit_id:
            target_unit = unit
            break
    
    if not target_unit:
        return {"success": False, "message": "Unit not found"}
    
    # Check if unit is in training queue
    if target_unit.get("train_completed") and datetime.fromisoformat(target_unit["train_completed"]) > datetime.now():
        return {"success": False, "message": "Unit is still in training"}
    
    # Get unit info
    unit_type = target_unit.get("unit_type")
    if unit_type not in UNITS:
        return {"success": False, "message": "Invalid unit type"}
    
    unit_info = UNITS[unit_type]
    current_level = int(target_unit.get("level", 1))
    
    # Calculate upgrade cost
    base_cost = unit_info["base_cost"]
    cost_multiplier = unit_info["cost_multiplier"]
    
    upgrade_cost = {}
    for resource, amount in base_cost.items():
        # Apply multiplier based on current level
        upgrade_cost[resource] = int(amount * (cost_multiplier ** current_level))
    
    # Check if player has enough resources
    player = await get_player(player_id)
    if not player:
        return {"success": False, "message": "Player not found"}
    
    for resource, amount in upgrade_cost.items():
        if player.get(resource, 0) < amount:
            return {"success": False, "message": f"Not enough {resource}. Need {amount}, have {player.get(resource, 0)}"}
    
    # Deduct resources
    resource_updates = {}
    for resource, amount in upgrade_cost.items():
        resource_updates[resource] = player.get(resource, 0) - amount
    
    await update_player(player_id, resource_updates)
    
    # Calculate upgrade time
    base_time = unit_info["train_time"]
    # Increase time based on level
    upgrade_time = base_time * (1 + (current_level * 0.25))
    
    # Calculate start and completion times
    now = datetime.now()
    train_completed = now + timedelta(seconds=upgrade_time)
    
    # Update unit data for upgrade
    updated_unit = {
        "level": current_level + 1,
        "train_started": now.isoformat(),
        "train_completed": train_completed.isoformat()
    }
    
    await update_sheet("Units", {"unit_id": unit_id}, updated_unit)
    
    # Update cache
    cache_key = f"units_{player_id}"
    if cache_key in units_cache:
        for i, unit in enumerate(units_cache[cache_key]):
            if unit.get("unit_id") == unit_id:
                units_cache[cache_key][i].update(updated_unit)
                break
        last_cache_update[cache_key] = datetime.now()
    
    return {
        "success": True,
        "message": f"Upgrading {unit_info['name']} to level {current_level + 1}",
        "upgrade_time": upgrade_time,
        "cost": upgrade_cost
    }

async def get_unit_power(player_id):
    """Calculate the total military power of a player's units"""
    player_units = await get_player_units(player_id)
    
    total_power = 0
    
    for unit in player_units:
        # Skip units in training queue
        if unit.get("train_completed") and datetime.fromisoformat(unit["train_completed"]) > datetime.now():
            continue
        
        unit_type = unit.get("unit_type")
        quantity = int(unit.get("quantity", 0))
        level = int(unit.get("level", 1))
        
        if unit_type not in UNITS:
            continue
        
        unit_info = UNITS[unit_type]
        stats = unit_info.get("stats", {})
        
        # Calculate unit power based on stats
        unit_power = (
            stats.get("attack", 0) + 
            stats.get("defense", 0) + 
            stats.get("health", 0) / 2
        ) * (1 + (level - 1) * 0.2)  # 20% boost per level
        
        total_power += unit_power * quantity
    
    return int(total_power)

async def process_training_queue():
    """Process the training queue and complete finished units"""
    # Get all units
    units_sheet = await get_sheet("Units")
    
    now = datetime.now()
    completed_units = []
    
    for unit in units_sheet:
        # Check if unit is in queue and completed
        if unit.get("train_completed") and datetime.fromisoformat(unit["train_completed"]) <= now:
            completed_units.append(unit)
    
    # Update completed units
    for unit in completed_units:
        await update_sheet("Units", {"unit_id": unit["unit_id"]}, {
            "train_started": None,
            "train_completed": None
        })
        
        # Clear cache for this player
        player_id = unit.get("player_id")
        if player_id:
            cache_key = f"units_{player_id}"
            if cache_key in units_cache:
                del units_cache[cache_key]
    
    return completed_units
