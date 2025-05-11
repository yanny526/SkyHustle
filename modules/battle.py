"""
Battle module for the SkyHustle Telegram bot.
Handles PvP and PvE combat mechanics.
"""
import logging
from ast import literal_eval
import asyncio
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from modules.player import get_player, player_exists
from modules.unit import get_player_units, get_unit_info
from modules.building import get_player_buildings, get_building_info
from modules.research import get_player_research, get_research_info
from modules.sheets_service import get_sheet, update_sheet_row, append_sheet_row, find_row_by_col_value

class Battle:
    """
    Battle class for SkyHustle.
    Represents a battle between players or against NPCs.
    
    Attributes:
        battle_id: Unique identifier for this battle
        attacker_id: ID of the attacking player
        defender_id: ID of the defending player (or NPC ID)
        attacker_units: Units used by the attacker
        defender_units: Units used by the defender
        result: Outcome of the battle (win/loss/draw)
        resources_gained: Resources gained by the attacker
        timestamp: When the battle occurred
    """
    def __init__(
        self,
        battle_id: int,
        attacker_id: int,
        defender_id: int,
        attacker_units: Dict[str, int],
        defender_units: Dict[str, int],
        result: str,
        resources_gained: Dict[str, int],
        timestamp: Optional[datetime] = None,
        row_index: Optional[int] = None
    ):
        self.battle_id = battle_id
        self.attacker_id = attacker_id
        self.defender_id = defender_id
        self.attacker_units = attacker_units
        self.defender_units = defender_units
        self.result = result
        self.resources_gained = resources_gained
        self.timestamp = timestamp or datetime.now()
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert battle to dictionary for storage."""
        return {
            "battle_id": self.battle_id,
            "attacker_id": str(self.attacker_id),
            "defender_id": str(self.defender_id),
            "attacker_units": str(self.attacker_units),
            "defender_units": str(self.defender_units),
            "result": self.result,
            "resources_gained": str(self.resources_gained),
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Battle':
        """Create a Battle object from a sheet row."""
        try:
            attacker_units = literal_eval(row[2])
            defender_units = literal_eval(row[3])
            resources_gained = literal_eval(row[5])
        except (SyntaxError, ValueError) as e:
            logging.error(f"Error parsing battle data: {e}")
            attacker_units = {}
            defender_units = {}
            resources_gained = {}
        
        timestamp = datetime.now()
        if len(row) > 6 and row[6]:
            try:
                timestamp = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logging.warning(f"Invalid timestamp format for battle {row[0]}")
        
        return cls(
            battle_id=int(row[0]),
            attacker_id=int(row[1]),
            defender_id=int(row[2]),
            attacker_units=attacker_units,
            defender_units=defender_units,
            result=row[4],
            resources_gained=resources_gained,
            timestamp=timestamp,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save battle to the sheet."""
        battle_data = await self.to_dict()
        battle_row = list(battle_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("Battles", self.row_index, battle_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("Battles", battle_row)

async def get_next_battle_id() -> int:
    """
    Get the next available battle ID.
    
    Returns:
        Next available battle ID
    """
    sheet = await get_sheet("Battles")
    
    if not sheet["values"] or len(sheet["values"]) <= 1:
        return 1
    
    # Skip header row
    battle_ids = [int(row[0]) for row in sheet["values"][1:] if row and row[0].isdigit()]
    
    if not battle_ids:
        return 1
    
    return max(battle_ids) + 1

async def get_player_power(player_id: int) -> int:
    """
    Calculate a player's military power based on units, buildings, and research.
    
    Args:
        player_id: The player ID
    
    Returns:
        The player's military power as an integer
    """
    # Get player's units
    units = await get_player_units(player_id)
    unit_power = 0
    
    for unit in units:
        unit_info = await get_unit_info(unit.unit_id)
        # Calculate power from attack and defense values
        unit_power += (unit_info["attack"] + unit_info["defense"]) * unit.quantity * unit.level
    
    # Get player's defensive buildings
    buildings = await get_player_buildings(player_id)
    building_power = 0
    
    for building in buildings:
        building_info = await get_building_info(building.building_id)
        # Add building defense value if it has one
        if "defense" in building_info.get("provides", {}):
            building_power += building_info["provides"]["defense"] * building.level
    
    # Get player's research that affects combat
    research = await get_player_research(player_id)
    research_modifier = 1.0
    
    for tech in research:
        tech_info = await get_research_info(tech.tech_id)
        # Add combat-related research bonuses
        if "unit_attack" in tech_info.get("effects", {}):
            research_modifier *= tech_info["effects"]["unit_attack"]
        if "defense_bonus" in tech_info.get("effects", {}):
            research_modifier *= tech_info["effects"]["defense_bonus"]
    
    # Calculate total power with research modifier
    total_power = int((unit_power + building_power) * research_modifier)
    
    return max(1, total_power)  # Ensure power is at least 1

async def scan_for_targets(player_id: int, count: int = 5) -> List[Dict[str, Any]]:
    """
    Find potential targets for a player to attack.
    
    Args:
        player_id: The player ID
        count: Number of targets to find
    
    Returns:
        List of target players with their details
    """
    try:
        # Get all players
        sheet = await get_sheet("Players")
        
        if not sheet["values"] or len(sheet["values"]) <= 1:
            return []
        
        # Get attacker's power
        attacker_power = await get_player_power(player_id)
        
        # Find players with similar power (±30%)
        targets = []
        power_min = attacker_power * 0.7
        power_max = attacker_power * 1.3
        
        # Skip header row
        for i, row in enumerate(sheet["values"][1:], 2):
            if not row or len(row) < 2:
                continue
            
            target_id = int(row[0])
            
            # Skip the player themselves
            if target_id == player_id:
                continue
            
            # Check if player exists and calculate their power
            if await player_exists(target_id):
                target_power = await get_player_power(target_id)
                
                # Check if power is within range
                if power_min <= target_power <= power_max:
                    # Get player name
                    target_player = await get_player(target_id)
                    
                    targets.append({
                        "id": target_id,
                        "name": target_player.display_name,
                        "power": target_power
                    })
                    
                    # Stop if we have enough targets
                    if len(targets) >= count:
                        break
        
        # If not enough targets, add some random players
        if len(targets) < count:
            for i, row in enumerate(sheet["values"][1:], 2):
                if not row or len(row) < 2:
                    continue
                
                target_id = int(row[0])
                
                # Skip the player themselves and already added targets
                if target_id == player_id or any(t["id"] == target_id for t in targets):
                    continue
                
                # Check if player exists
                if await player_exists(target_id):
                    # Get player name and power
                    target_player = await get_player(target_id)
                    target_power = await get_player_power(target_id)
                    
                    targets.append({
                        "id": target_id,
                        "name": target_player.display_name,
                        "power": target_power
                    })
                    
                    # Stop if we have enough targets
                    if len(targets) >= count:
                        break
        
        # Sort targets by power (closest to player's power first)
        targets.sort(key=lambda x: abs(x["power"] - attacker_power))
        
        return targets
        
    except Exception as e:
        logging.error(f"Error scanning for targets: {e}", exc_info=True)
        return []

async def simulate_battle(attacker_id: int, defender_id: int) -> Tuple[str, Dict[str, int], Dict[str, Any]]:
    """
    Simulate a battle between two players.
    
    Args:
        attacker_id: The attacking player's ID
        defender_id: The defending player's ID
    
    Returns:
        Tuple of (result, resources_gained, battle_details)
    """
    # Get attacker and defender units
    attacker_units = await get_player_units(attacker_id)
    defender_units = await get_player_units(defender_id)
    
    # Calculate attack power
    attacker_power = await get_player_power(attacker_id)
    defender_power = await get_player_power(defender_id)
    
    # Battle logic - simplified for now
    # Add some randomness to the outcome
    attack_roll = random.uniform(0.8, 1.2)
    defense_roll = random.uniform(0.8, 1.2)
    
    attack_score = attacker_power * attack_roll
    defense_score = defender_power * defense_roll
    
    # Determine winner
    if attack_score > defense_score:
        result = "win"
        # Calculate percentage of victory (affects resources gained)
        victory_percentage = min(1.0, (attack_score - defense_score) / defense_score)
        
        # Get defender resources
        defender = await get_player(defender_id)
        
        # Calculate resources gained (10-30% of defender's resources based on victory margin)
        base_percentage = 0.1 + (victory_percentage * 0.2)
        resources_gained = {
            "credits": int(defender.credits * base_percentage),
            "minerals": int(defender.minerals * base_percentage),
            "energy": int(defender.energy * base_percentage)
        }
        
        # Cap resources gained
        resources_gained["credits"] = min(resources_gained["credits"], 1000)
        resources_gained["minerals"] = min(resources_gained["minerals"], 500)
        resources_gained["energy"] = min(resources_gained["energy"], 250)
        
        # Ensure minimum rewards
        resources_gained["credits"] = max(resources_gained["credits"], 50)
        resources_gained["minerals"] = max(resources_gained["minerals"], 25)
        resources_gained["energy"] = max(resources_gained["energy"], 10)
        
    elif attack_score < defense_score:
        result = "loss"
        resources_gained = {"credits": 0, "minerals": 0, "energy": 0}
    else:
        result = "draw"
        resources_gained = {"credits": 0, "minerals": 0, "energy": 0}
    
    # Create battle details
    battle_details = {
        "attacker": {
            "power": attacker_power,
            "roll": attack_roll,
            "score": attack_score
        },
        "defender": {
            "power": defender_power,
            "roll": defense_roll,
            "score": defense_score
        },
        "result": result,
        "resources_gained": resources_gained
    }
    
    # Convert unit objects to simple dictionaries for storage
    attacker_units_dict = {unit.unit_id: unit.quantity for unit in attacker_units}
    defender_units_dict = {unit.unit_id: unit.quantity for unit in defender_units}
    
    return result, resources_gained, battle_details, attacker_units_dict, defender_units_dict

async def attack_player(attacker_id: int, defender_id: int) -> Dict[str, Any]:
    """
    Attack another player.
    
    Args:
        attacker_id: The attacking player's ID
        defender_id: The defending player's ID
    
    Returns:
        Dictionary with battle results
    """
    try:
        # Validate players exist
        if not await player_exists(attacker_id):
            return {
                "success": False,
                "message": "Attacker does not exist."
            }
        
        if not await player_exists(defender_id):
            return {
                "success": False,
                "message": "Target player does not exist."
            }
        
        # Get player names
        attacker = await get_player(attacker_id)
        defender = await get_player(defender_id)
        
        # Simulate battle
        result, resources_gained, battle_details, attacker_units_dict, defender_units_dict = await simulate_battle(attacker_id, defender_id)
        
        # Create battle record
        battle_id = await get_next_battle_id()
        battle = Battle(
            battle_id=battle_id,
            attacker_id=attacker_id,
            defender_id=defender_id,
            attacker_units=attacker_units_dict,
            defender_units=defender_units_dict,
            result=result,
            resources_gained=resources_gained,
            timestamp=datetime.now()
        )
        
        # Save battle
        await battle.save()
        
        # Award resources if attacker won
        if result == "win":
            attacker.credits += resources_gained["credits"]
            attacker.minerals += resources_gained["minerals"]
            attacker.energy += resources_gained["energy"]
            
            # Award experience
            attacker.experience += 50
            
            # Save player
            await attacker.save()
            
            # Deduct resources from defender (but not below 10% of their current resources)
            defender.credits = max(int(defender.credits * 0.9), defender.credits - resources_gained["credits"])
            defender.minerals = max(int(defender.minerals * 0.9), defender.minerals - resources_gained["minerals"])
            defender.energy = max(int(defender.energy * 0.9), defender.energy - resources_gained["energy"])
            
            # Save defender
            await defender.save()
            
            return {
                "success": True,
                "message": f"Victory! You defeated {defender.display_name} and gained {resources_gained['credits']} credits, {resources_gained['minerals']} minerals, and {resources_gained['energy']} energy.",
                "result": result,
                "resources_gained": resources_gained,
                "battle_details": battle_details
            }
        
        elif result == "loss":
            # Award some experience even for a loss
            attacker.experience += 10
            await attacker.save()
            
            return {
                "success": True,
                "message": f"Defeat! {defender.display_name}'s defenses were too strong. You gained 10 experience points.",
                "result": result,
                "resources_gained": resources_gained,
                "battle_details": battle_details
            }
        
        else:  # Draw
            # Award some experience for a draw
            attacker.experience += 20
            await attacker.save()
            
            return {
                "success": True,
                "message": f"Draw! Your forces were evenly matched with {defender.display_name}. You gained 20 experience points.",
                "result": result,
                "resources_gained": resources_gained,
                "battle_details": battle_details
            }
        
    except Exception as e:
        logging.error(f"Error attacking player: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred during battle: {str(e)}"
        }
