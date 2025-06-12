import datetime
from datetime import timezone
from telegram.ext import ContextTypes
from modules.sheets_helper import (
    initialize_sheets,
    list_all_players,
    get_player_data,
    update_player_data
)

# Base production rates per minute
WOOD_PER_MINUTE = 1.0  # Wood Farm level × 1.0
STONE_PER_MINUTE = 0.8  # Stone Mine level × 0.8
FOOD_PER_MINUTE = 0.7  # Food Farm level × 0.7
GOLD_PER_MINUTE = 0.5  # Gold Mine level × 0.5
ENERGY_PER_MINUTE = 0.3  # Power Plant level × 0.3

async def tick_resources(user_id: int) -> None:
    """
    Resource tick job that runs every minute to update player resources.
    Calculates production based on building levels and updates resource balances.
    """
    try:
        # Ensure sheets are initialized
        initialize_sheets()
        
        # Get player data
        data = get_player_data(user_id)
        if not data:
            return
                
        # Get building levels (default to 1)
        wood_farm = data.get("lumber_house_level", 1)
        stone_mine = data.get("mine_level", 1)
        food_farm = data.get("warehouse_level", 1)
        gold_mine = data.get("mine_level", 1)  # Using mine level for gold too
        power_plant = data.get("power_plant_level", 1)
        
        # Calculate per-minute yields
        wood_yield = wood_farm * WOOD_PER_MINUTE
        stone_yield = stone_mine * STONE_PER_MINUTE
        food_yield = food_farm * FOOD_PER_MINUTE
        gold_yield = gold_mine * GOLD_PER_MINUTE
        energy_yield = power_plant * ENERGY_PER_MINUTE
        
        # Get current balances
        wood = data.get("resources_wood", 0)
        stone = data.get("resources_stone", 0)
        food = data.get("resources_food", 0)
        gold = data.get("resources_gold", 0)
        energy = data.get("energy", 0)
        
        # Get capacity limits
        wood_cap = data.get("capacity_wood", 1000)
        stone_cap = data.get("capacity_stone", 1000)
        food_cap = data.get("capacity_food", 1000)
        gold_cap = data.get("capacity_gold", 1000)
        energy_cap = data.get("energy_max", 1000)
        
        # Update resources (capped by capacity)
        new_wood = min(wood + wood_yield, wood_cap)
        new_stone = min(stone + stone_yield, stone_cap)
        new_food = min(food + food_yield, food_cap)
        new_gold = min(gold + gold_yield, gold_cap)
        new_energy = min(energy + energy_yield, energy_cap)
        
        # Update player data
        update_player_data(user_id, "resources_wood", new_wood)
        update_player_data(user_id, "resources_stone", new_stone)
        update_player_data(user_id, "resources_food", new_food)
        update_player_data(user_id, "resources_gold", new_gold)
        update_player_data(user_id, "energy", new_energy)
            
    except Exception as e:
        print(f"Error in resource tick: {e}")

def setup_resources_system(app):
    """Register the resource tick job."""
    app.job_queue.run_repeating(tick_resources, interval=60, first=0) 