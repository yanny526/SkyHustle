"""
Buildings module for SkyHustle
Handles building construction and management
"""
import logging
from datetime import datetime, timedelta

from constants import BUILDINGS, MAX_QUEUE_LENGTH
from modules.player import get_player, update_player
from modules.sheets_service import get_sheet, update_sheet, append_sheet
from utils.logger import get_logger

logger = get_logger(__name__)

# In-memory cache for buildings data
buildings_cache = {}
last_cache_update = {}

async def get_player_buildings(player_id):
    """Get all buildings for a player"""
    # Check cache first
    cache_key = f"buildings_{player_id}"
    cache_valid_time = 300  # 5 minutes
    
    # If cache is valid, return cached data
    if cache_key in buildings_cache and cache_key in last_cache_update:
        time_since_update = (datetime.now() - last_cache_update[cache_key]).total_seconds()
        if time_since_update < cache_valid_time:
            return buildings_cache[cache_key]
    
    # Get data from sheet
    sheet = await get_sheet("Buildings")
    
    player_buildings = []
    for row in sheet:
        if row.get("player_id") == player_id:
            building_data = {
                "building_id": row.get("building_id"),
                "player_id": row.get("player_id"),
                "building_type": row.get("building_type"),
                "level": int(row.get("level", 1)),
                "quantity": int(row.get("quantity", 0)),
                "build_started": row.get("build_started"),
                "build_completed": row.get("build_completed")
            }
            player_buildings.append(building_data)
    
    # Update cache
    buildings_cache[cache_key] = player_buildings
    last_cache_update[cache_key] = datetime.now()
    
    return player_buildings

async def get_available_buildings(player_id):
    """Get list of buildings available for construction"""
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
    
    # Determine which buildings are available based on prerequisites
    available_buildings = []
    
    for building_id, building_data in BUILDINGS.items():
        # Check prerequisites
        prerequisites_met = True
        
        for req_building, req_level in building_data["prerequisites"].items():
            if req_building not in existing_buildings or existing_buildings[req_building] < req_level:
                prerequisites_met = False
                break
        
        if prerequisites_met:
            available_buildings.append(building_id)
    
    return available_buildings

async def check_building_prerequisites(player_id, building_id):
    """Check if prerequisites are met for a building"""
    if building_id not in BUILDINGS:
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
    prerequisites = BUILDINGS[building_id]["prerequisites"]
    for req_building, req_level in prerequisites.items():
        if req_building not in existing_buildings or existing_buildings[req_building] < req_level:
            return False
    
    return True

async def add_building_to_queue(player_id, building_id, quantity=1, skip_validation=False):
    """Add a building to the construction queue"""
    # Validate building exists
    if building_id not in BUILDINGS:
        return {"success": False, "message": "Invalid building type"}
    
    # Get player data
    player = await get_player(player_id)
    if not player:
        return {"success": False, "message": "Player not found"}
    
    # Check prerequisites if not skipping validation
    if not skip_validation and not await check_building_prerequisites(player_id, building_id):
        return {"success": False, "message": "Building prerequisites not met"}
    
    # Get player's current buildings
    player_buildings = await get_player_buildings(player_id)
    
    # Check if building queue is full
    queue_count = 0
    for building in player_buildings:
        if building.get("build_completed") and datetime.fromisoformat(building["build_completed"]) > datetime.now():
            queue_count += 1
    
    if queue_count >= MAX_QUEUE_LENGTH:
        return {"success": False, "message": f"Build queue is full. Maximum queue length is {MAX_QUEUE_LENGTH}"}
    
    # Calculate cost based on existing buildings of same type
    building_info = BUILDINGS[building_id]
    base_cost = building_info["base_cost"]
    existing_count = 0
    
    for building in player_buildings:
        if building.get("building_type") == building_id:
            existing_count += int(building.get("quantity", 0))
    
    # Calculate total cost with multiplier
    total_cost = {}
    cost_multiplier = building_info["cost_multiplier"]
    
    for resource, amount in base_cost.items():
        # Apply multiplier based on existing buildings
        scaled_amount = amount * (cost_multiplier ** existing_count)
        # Multiply by quantity
        total_cost[resource] = int(scaled_amount * quantity)
    
    # Check if player has enough resources
    for resource, amount in total_cost.items():
        if player.get(resource, 0) < amount:
            return {"success": False, "message": f"Not enough {resource}. Need {amount}, have {player.get(resource, 0)}"}
    
    # Deduct resources
    resource_updates = {}
    for resource, amount in total_cost.items():
        resource_updates[resource] = player.get(resource, 0) - amount
    
    await update_player(player_id, resource_updates)
    
    # Calculate build time
    base_time = building_info["build_time"]
    # Increase time based on quantity
    total_time = base_time * quantity
    
    # Generate unique building ID
    import uuid
    building_unique_id = str(uuid.uuid4())
    
    # Calculate start and completion times
    now = datetime.now()
    build_completed = now + timedelta(seconds=total_time)
    
    # Add to queue
    new_building = {
        "building_id": building_unique_id,
        "player_id": player_id,
        "building_type": building_id,
        "level": 1,  # New buildings start at level 1
        "quantity": quantity,
        "build_started": now.isoformat(),
        "build_completed": build_completed.isoformat()
    }
    
    await append_sheet("Buildings", [new_building])
    
    # Update cache
    cache_key = f"buildings_{player_id}"
    if cache_key in buildings_cache:
        buildings_cache[cache_key].append(new_building)
        last_cache_update[cache_key] = datetime.now()
    
    return {
        "success": True,
        "message": f"Building {quantity}x {building_info['name']} started",
        "build_time": total_time,
        "cost": total_cost
    }

async def upgrade_building(player_id, building_id):
    """Upgrade an existing building"""
    # Get player's buildings
    player_buildings = await get_player_buildings(player_id)
    
    # Find the building to upgrade
    target_building = None
    for building in player_buildings:
        if building.get("building_id") == building_id:
            target_building = building
            break
    
    if not target_building:
        return {"success": False, "message": "Building not found"}
    
    # Check if building is in construction queue
    if target_building.get("build_completed") and datetime.fromisoformat(target_building["build_completed"]) > datetime.now():
        return {"success": False, "message": "Building is still under construction"}
    
    # Get building info
    building_type = target_building.get("building_type")
    if building_type not in BUILDINGS:
        return {"success": False, "message": "Invalid building type"}
    
    building_info = BUILDINGS[building_type]
    current_level = int(target_building.get("level", 1))
    
    # Calculate upgrade cost
    base_cost = building_info["base_cost"]
    cost_multiplier = building_info["cost_multiplier"]
    
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
    base_time = building_info["build_time"]
    # Increase time based on level
    upgrade_time = base_time * (1 + (current_level * 0.25))
    
    # Calculate start and completion times
    now = datetime.now()
    build_completed = now + timedelta(seconds=upgrade_time)
    
    # Update building data for upgrade
    updated_building = {
        "level": current_level + 1,
        "build_started": now.isoformat(),
        "build_completed": build_completed.isoformat()
    }
    
    await update_sheet("Buildings", {"building_id": building_id}, updated_building)
    
    # Update cache
    cache_key = f"buildings_{player_id}"
    if cache_key in buildings_cache:
        for i, building in enumerate(buildings_cache[cache_key]):
            if building.get("building_id") == building_id:
                buildings_cache[cache_key][i].update(updated_building)
                break
        last_cache_update[cache_key] = datetime.now()
    
    return {
        "success": True,
        "message": f"Upgrading {building_info['name']} to level {current_level + 1}",
        "upgrade_time": upgrade_time,
        "cost": upgrade_cost
    }

async def process_building_queue():
    """Process the building queue and complete finished buildings"""
    # Get all buildings
    buildings_sheet = await get_sheet("Buildings")
    
    now = datetime.now()
    completed_buildings = []
    
    for building in buildings_sheet:
        # Check if building is in queue and completed
        if building.get("build_completed") and datetime.fromisoformat(building["build_completed"]) <= now:
            completed_buildings.append(building)
    
    # Update completed buildings
    for building in completed_buildings:
        await update_sheet("Buildings", {"building_id": building["building_id"]}, {
            "build_started": None,
            "build_completed": None
        })
        
        # Clear cache for this player
        player_id = building.get("player_id")
        if player_id:
            cache_key = f"buildings_{player_id}"
            if cache_key in buildings_cache:
                del buildings_cache[cache_key]
    
    return completed_buildings

async def get_building_production(player_id, building_type=None):
    """Get production rates from buildings"""
    player_buildings = await get_player_buildings(player_id)
    
    production = {
        "credits": 0,
        "minerals": 0,
        "energy": 0
    }
    
    for building in player_buildings:
        # Skip buildings in construction queue
        if building.get("build_completed") and datetime.fromisoformat(building["build_completed"]) > datetime.now():
            continue
        
        b_type = building.get("building_type")
        quantity = int(building.get("quantity", 0))
        level = int(building.get("level", 1))
        
        # Filter by building type if specified
        if building_type and b_type != building_type:
            continue
        
        if b_type not in BUILDINGS:
            continue
        
        building_info = BUILDINGS[b_type]
        provides = building_info.get("provides", {})
        
        # Add production based on building type
        if "credits_per_hour" in provides:
            production["credits"] += quantity * provides["credits_per_hour"] * (1 + (level - 1) * 0.1)
        if "minerals_per_hour" in provides:
            production["minerals"] += quantity * provides["minerals_per_hour"] * (1 + (level - 1) * 0.1)
        if "energy_per_hour" in provides:
            production["energy"] += quantity * provides["energy_per_hour"] * (1 + (level - 1) * 0.1)
    
    # Round to integers
    for resource in production:
        production[resource] = int(production[resource])
    
    return production
