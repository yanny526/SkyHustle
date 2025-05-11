"""
Validation utilities for the SkyHustle Telegram bot.
Validates command inputs before execution.
"""
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple

from modules.player import get_player, player_exists
from modules.building import has_building, get_building_info, get_build_queue
from modules.unit import get_unit_info, get_training_queue
from modules.research import get_research_info, has_research
from modules.alliance import get_player_alliance, get_alliance_member
from modules.battle import get_player_power

async def validate_build_command(player_id: int, building_id: str, quantity: int) -> Dict[str, Any]:
    """
    Validate the build command.
    
    Args:
        player_id: The player ID
        building_id: The building ID
        quantity: Number of buildings to build
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check if building exists
        try:
            building_info = await get_building_info(building_id)
        except ValueError:
            return {
                "valid": False,
                "message": f"Building '{building_id}' does not exist."
            }
        
        # Check quantity
        if quantity <= 0:
            return {
                "valid": False,
                "message": "Quantity must be greater than 0."
            }
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        total_cost = building_info["cost"] * quantity
        total_minerals = building_info["minerals"] * quantity
        total_energy = building_info["energy"] * quantity
        
        if player.credits < total_cost:
            return {
                "valid": False,
                "message": f"Not enough credits. Need {total_cost}, have {player.credits}."
            }
        
        if player.minerals < total_minerals:
            return {
                "valid": False,
                "message": f"Not enough minerals. Need {total_minerals}, have {player.minerals}."
            }
        
        if player.energy < total_energy:
            return {
                "valid": False,
                "message": f"Not enough energy. Need {total_energy}, have {player.energy}."
            }
        
        # Check building requirements
        for req_building_id in building_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                req_name = await get_building_info(req_building_id)
                return {
                    "valid": False,
                    "message": f"You need to build a {req_name['name']} first."
                }
        
        # Check queue length
        current_queue = await get_build_queue(player_id)
        if len(current_queue) >= 5:
            return {
                "valid": False,
                "message": "Build queue is full (max 5 items)."
            }
        
        return {
            "valid": True,
            "message": "Build command is valid."
        }
    
    except Exception as e:
        logging.error(f"Error validating build command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }

async def validate_train_command(player_id: int, unit_id: str, count: int) -> Dict[str, Any]:
    """
    Validate the train command.
    
    Args:
        player_id: The player ID
        unit_id: The unit ID
        count: Number of units to train
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check if unit exists
        try:
            unit_info = await get_unit_info(unit_id)
        except ValueError:
            return {
                "valid": False,
                "message": f"Unit '{unit_id}' does not exist."
            }
        
        # Check count
        if count <= 0:
            return {
                "valid": False,
                "message": "Count must be greater than 0."
            }
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        total_cost = unit_info["cost"] * count
        total_minerals = unit_info["minerals"] * count
        total_energy = unit_info["energy"] * count
        
        if player.credits < total_cost:
            return {
                "valid": False,
                "message": f"Not enough credits. Need {total_cost}, have {player.credits}."
            }
        
        if player.minerals < total_minerals:
            return {
                "valid": False,
                "message": f"Not enough minerals. Need {total_minerals}, have {player.minerals}."
            }
        
        if player.energy < total_energy:
            return {
                "valid": False,
                "message": f"Not enough energy. Need {total_energy}, have {player.energy}."
            }
        
        # Check unit requirements
        for req_building_id in unit_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                req_name = await get_building_info(req_building_id)
                return {
                    "valid": False,
                    "message": f"You need to build a {req_name['name']} first."
                }
        
        # Check queue length
        current_queue = await get_training_queue(player_id)
        if len(current_queue) >= 5:
            return {
                "valid": False,
                "message": "Training queue is full (max 5 items)."
            }
        
        return {
            "valid": True,
            "message": "Train command is valid."
        }
    
    except Exception as e:
        logging.error(f"Error validating train command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }

async def validate_research_command(player_id: int, tech_id: str) -> Dict[str, Any]:
    """
    Validate the research command.
    
    Args:
        player_id: The player ID
        tech_id: The technology ID
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check if technology exists
        try:
            tech_info = await get_research_info(tech_id)
        except ValueError:
            return {
                "valid": False,
                "message": f"Technology '{tech_id}' does not exist."
            }
        
        # Get player
        player = await get_player(player_id)
        
        # Check if player has enough resources
        if player.credits < tech_info["cost"]:
            return {
                "valid": False,
                "message": f"Not enough credits. Need {tech_info['cost']}, have {player.credits}."
            }
        
        if player.minerals < tech_info["minerals"]:
            return {
                "valid": False,
                "message": f"Not enough minerals. Need {tech_info['minerals']}, have {player.minerals}."
            }
        
        if player.energy < tech_info["energy"]:
            return {
                "valid": False,
                "message": f"Not enough energy. Need {tech_info['energy']}, have {player.energy}."
            }
        
        # Check technology requirements
        for req_building_id in tech_info["requirements"]:
            if not await has_building(player_id, req_building_id):
                req_name = await get_building_info(req_building_id)
                return {
                    "valid": False,
                    "message": f"You need to build a {req_name['name']} first."
                }
        
        # Check if already researched
        if await has_research(player_id, tech_id):
            return {
                "valid": False,
                "message": f"You have already researched {tech_info['name']}."
            }
        
        return {
            "valid": True,
            "message": "Research command is valid."
        }
    
    except Exception as e:
        logging.error(f"Error validating research command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }

async def validate_attack_command(player_id: int, target_id: int) -> Dict[str, Any]:
    """
    Validate the attack command.
    
    Args:
        player_id: The player ID
        target_id: The target player ID
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check if target exists
        if not await player_exists(target_id):
            return {
                "valid": False,
                "message": "Target player does not exist."
            }
        
        # Check if player is attacking themselves
        if player_id == target_id:
            return {
                "valid": False,
                "message": "You cannot attack yourself."
            }
        
        # Get player power
        player_power = await get_player_power(player_id)
        
        # Check if player has any military power
        if player_power <= 0:
            return {
                "valid": False,
                "message": "You need to train units before attacking."
            }
        
        # Get target player info
        target_player = await get_player(target_id)
        
        return {
            "valid": True,
            "message": f"Ready to attack {target_player.display_name}."
        }
    
    except Exception as e:
        logging.error(f"Error validating attack command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }

async def validate_alliance_command(player_id: int, subcmd: str, *args) -> Dict[str, Any]:
    """
    Validate alliance commands.
    
    Args:
        player_id: The player ID
        subcmd: The alliance subcommand
        *args: Additional arguments for the subcommand
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check if player exists
        if not await player_exists(player_id):
            return {
                "valid": False,
                "message": "Player does not exist."
            }
        
        # Get player alliance
        alliance = await get_player_alliance(player_id)
        alliance_member = await get_alliance_member(player_id)
        
        # Validate subcommands
        if subcmd == "create":
            # Check if player is already in an alliance
            if alliance:
                return {
                    "valid": False,
                    "message": "You are already in an alliance. Leave your current alliance first."
                }
            
            # Check alliance name
            if not args or not args[0]:
                return {
                    "valid": False,
                    "message": "You must provide an alliance name."
                }
            
            name = args[0]
            if len(name) < 3 or len(name) > 20:
                return {
                    "valid": False,
                    "message": "Alliance name must be between 3 and 20 characters."
                }
            
            return {
                "valid": True,
                "message": "Create alliance command is valid."
            }
        
        elif subcmd == "join":
            # Check if player is already in an alliance
            if alliance:
                return {
                    "valid": False,
                    "message": "You are already in an alliance. Leave your current alliance first."
                }
            
            # Check join code
            if not args or not args[0]:
                return {
                    "valid": False,
                    "message": "You must provide a join code."
                }
            
            join_code = args[0]
            if len(join_code) != 6:
                return {
                    "valid": False,
                    "message": "Invalid join code format."
                }
            
            return {
                "valid": True,
                "message": "Join alliance command is valid."
            }
        
        elif subcmd == "leave":
            # Check if player is in an alliance
            if not alliance:
                return {
                    "valid": False,
                    "message": "You are not in an alliance."
                }
            
            return {
                "valid": True,
                "message": "Leave alliance command is valid."
            }
        
        elif subcmd == "invite":
            # Check if player is in an alliance
            if not alliance:
                return {
                    "valid": False,
                    "message": "You are not in an alliance."
                }
            
            # Check if player has permission
            if alliance_member.role not in ["leader", "officer"]:
                return {
                    "valid": False,
                    "message": "You don't have permission to invite players."
                }
            
            # Check target username
            if not args or not args[0]:
                return {
                    "valid": False,
                    "message": "You must provide a target username."
                }
            
            return {
                "valid": True,
                "message": "Invite command is valid."
            }
        
        elif subcmd == "disband":
            # Check if player is in an alliance
            if not alliance:
                return {
                    "valid": False,
                    "message": "You are not in an alliance."
                }
            
            # Check if player is the leader
            if alliance_member.role != "leader":
                return {
                    "valid": False,
                    "message": "Only the alliance leader can disband the alliance."
                }
            
            return {
                "valid": True,
                "message": "Disband alliance command is valid."
            }
        
        else:
            return {
                "valid": False,
                "message": f"Unknown alliance subcommand: {subcmd}"
            }
    
    except Exception as e:
        logging.error(f"Error validating alliance command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }

async def validate_setname_command(player_id: int, name: str) -> Dict[str, Any]:
    """
    Validate the setname command.
    
    Args:
        player_id: The player ID
        name: The new display name
    
    Returns:
        Dictionary with validation result and message
    """
    try:
        # Check name length
        if len(name) < 3 or len(name) > 32:
            return {
                "valid": False,
                "message": "Display name must be between 3 and 32 characters."
            }
        
        # Check name format (alphanumeric and spaces only)
        if not re.match(r'^[a-zA-Z0-9 ]+$', name):
            return {
                "valid": False,
                "message": "Display name can only contain letters, numbers, and spaces."
            }
        
        # Check if name is unique
        player = await get_player(player_id)
        
        # If the player already has this name, it's valid
        if player.display_name == name:
            return {
                "valid": True,
                "message": "Display name is valid."
            }
        
        # Check if another player has this name
        from modules.sheets_service import get_sheet
        sheet = await get_sheet("Players")
        
        for row in sheet["values"]:
            if len(row) > 1 and row[1].lower() == name.lower() and int(row[0]) != player_id:
                return {
                    "valid": False,
                    "message": f"Display name '{name}' is already taken."
                }
        
        return {
            "valid": True,
            "message": "Display name is valid."
        }
    
    except Exception as e:
        logging.error(f"Error validating setname command: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"An error occurred: {str(e)}"
        }
