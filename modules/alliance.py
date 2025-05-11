"""
Alliance module for the SkyHustle Telegram bot.
Handles alliance creation, management, and war mechanics.
"""
import logging
import asyncio
import random
import string
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from modules.player import get_player, player_exists
from modules.sheets_service import get_sheet, update_sheet_row, append_sheet_row, find_row_by_col_value
from modules.battle import get_player_power

class Alliance:
    """
    Alliance class for SkyHustle.
    Represents a player alliance.
    
    Attributes:
        alliance_id: Unique identifier for this alliance
        name: Name of the alliance
        leader_id: ID of the alliance leader
        join_code: Code for other players to join
        created_at: When the alliance was created
        member_count: Number of members in the alliance
        power_ranking: Combined power of all members
    """
    def __init__(
        self,
        alliance_id: int,
        name: str,
        leader_id: int,
        join_code: str,
        created_at: Optional[datetime] = None,
        member_count: int = 1,
        power_ranking: int = 0,
        row_index: Optional[int] = None
    ):
        self.alliance_id = alliance_id
        self.name = name
        self.leader_id = leader_id
        self.join_code = join_code
        self.created_at = created_at or datetime.now()
        self.member_count = member_count
        self.power_ranking = power_ranking
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert alliance to dictionary for storage."""
        return {
            "alliance_id": self.alliance_id,
            "name": self.name,
            "leader_id": str(self.leader_id),
            "join_code": self.join_code,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "member_count": self.member_count,
            "power_ranking": self.power_ranking
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Alliance':
        """Create an Alliance object from a sheet row."""
        created_at = datetime.now()
        if len(row) > 4 and row[4]:
            try:
                created_at = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logging.warning(f"Invalid created_at format for alliance {row[0]}")
        
        member_count = 1
        if len(row) > 5 and row[5]:
            try:
                member_count = int(row[5])
            except ValueError:
                logging.warning(f"Invalid member_count format for alliance {row[0]}")
        
        power_ranking = 0
        if len(row) > 6 and row[6]:
            try:
                power_ranking = int(row[6])
            except ValueError:
                logging.warning(f"Invalid power_ranking format for alliance {row[0]}")
        
        return cls(
            alliance_id=int(row[0]),
            name=row[1],
            leader_id=int(row[2]),
            join_code=row[3],
            created_at=created_at,
            member_count=member_count,
            power_ranking=power_ranking,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save alliance to the sheet."""
        alliance_data = await self.to_dict()
        alliance_row = list(alliance_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("Alliances", self.row_index, alliance_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("Alliances", alliance_row)

class AllianceMember:
    """
    AllianceMember class for SkyHustle.
    Represents a member of an alliance.
    
    Attributes:
        player_id: ID of the player
        alliance_id: ID of the alliance
        joined_at: When the player joined the alliance
        role: Role of the player in the alliance (leader, officer, member)
    """
    def __init__(
        self,
        player_id: int,
        alliance_id: int,
        joined_at: Optional[datetime] = None,
        role: str = "member",
        row_index: Optional[int] = None
    ):
        self.player_id = player_id
        self.alliance_id = alliance_id
        self.joined_at = joined_at or datetime.now()
        self.role = role
        self.row_index = row_index
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert alliance member to dictionary for storage."""
        return {
            "player_id": str(self.player_id),
            "alliance_id": str(self.alliance_id),
            "joined_at": self.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            "role": self.role
        }
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'AllianceMember':
        """Create an AllianceMember object from a sheet row."""
        joined_at = datetime.now()
        if len(row) > 2 and row[2]:
            try:
                joined_at = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logging.warning(f"Invalid joined_at format for alliance member {row[0]}")
        
        role = "member"
        if len(row) > 3 and row[3]:
            role = row[3]
        
        return cls(
            player_id=int(row[0]),
            alliance_id=int(row[1]),
            joined_at=joined_at,
            role=role,
            row_index=row_index
        )
    
    async def save(self) -> None:
        """Save alliance member to the sheet."""
        member_data = await self.to_dict()
        member_row = list(member_data.values())
        
        if self.row_index is not None:
            # Update existing row
            await update_sheet_row("AllianceMembers", self.row_index, member_row)
        else:
            # Add new row
            self.row_index = await append_sheet_row("AllianceMembers", member_row)

async def get_next_alliance_id() -> int:
    """
    Get the next available alliance ID.
    
    Returns:
        Next available alliance ID
    """
    sheet = await get_sheet("Alliances")
    
    if not sheet["values"] or len(sheet["values"]) <= 1:
        return 1
    
    # Skip header row
    alliance_ids = [int(row[0]) for row in sheet["values"][1:] if row and row[0].isdigit()]
    
    if not alliance_ids:
        return 1
    
    return max(alliance_ids) + 1

async def generate_join_code() -> str:
    """
    Generate a unique join code for an alliance.
    
    Returns:
        Unique join code
    """
    # Generate a 6-character alphanumeric code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Check if code already exists
    sheet = await get_sheet("Alliances")
    
    for row in sheet["values"]:
        if len(row) > 3 and row[3] == code:
            # Code already exists, generate a new one
            return await generate_join_code()
    
    return code

async def get_alliance_by_id(alliance_id: int) -> Optional[Alliance]:
    """
    Get an alliance by ID.
    
    Args:
        alliance_id: The alliance ID
    
    Returns:
        Alliance object or None if not found
    """
    sheet = await get_sheet("Alliances")
    
    # Find alliance row
    row_index, row = await find_row_by_col_value(sheet, str(alliance_id), 0)
    
    if row_index is not None:
        # Alliance exists, return alliance object
        return await Alliance.from_row(row, row_index)
    
    return None

async def get_alliance_by_join_code(join_code: str) -> Optional[Alliance]:
    """
    Get an alliance by join code.
    
    Args:
        join_code: The alliance join code
    
    Returns:
        Alliance object or None if not found
    """
    sheet = await get_sheet("Alliances")
    
    # Find alliance row
    row_index, row = await find_row_by_col_value(sheet, join_code, 3)
    
    if row_index is not None:
        # Alliance exists, return alliance object
        return await Alliance.from_row(row, row_index)
    
    return None

async def get_player_alliance(player_id: int) -> Optional[Alliance]:
    """
    Get the alliance a player belongs to.
    
    Args:
        player_id: The player ID
    
    Returns:
        Alliance object or None if the player is not in an alliance
    """
    # Check if player is in an alliance
    member = await get_alliance_member(player_id)
    
    if member:
        # Get alliance
        return await get_alliance_by_id(member.alliance_id)
    
    return None

async def get_alliance_member(player_id: int) -> Optional[AllianceMember]:
    """
    Get a player's alliance membership.
    
    Args:
        player_id: The player ID
    
    Returns:
        AllianceMember object or None if the player is not in an alliance
    """
    sheet = await get_sheet("AllianceMembers")
    
    # Find member row
    row_index, row = await find_row_by_col_value(sheet, str(player_id), 0)
    
    if row_index is not None:
        # Member exists, return member object
        return await AllianceMember.from_row(row, row_index)
    
    return None

async def get_alliance_members(alliance_id: int) -> List[AllianceMember]:
    """
    Get all members of an alliance.
    
    Args:
        alliance_id: The alliance ID
    
    Returns:
        List of AllianceMember objects
    """
    sheet = await get_sheet("AllianceMembers")
    alliance_id_str = str(alliance_id)
    
    members = []
    for i, row in enumerate(sheet["values"]):
        if len(row) > 1 and row[1] == alliance_id_str:
            member = await AllianceMember.from_row(row, i + 1)  # +1 for header row
            members.append(member)
    
    return members

async def update_alliance_stats(alliance_id: int) -> None:
    """
    Update an alliance's member count and power ranking.
    
    Args:
        alliance_id: The alliance ID
    """
    try:
        # Get alliance
        alliance = await get_alliance_by_id(alliance_id)
        
        if not alliance:
            logging.error(f"Alliance {alliance_id} not found")
            return
        
        # Get alliance members
        members = await get_alliance_members(alliance_id)
        
        # Update member count
        alliance.member_count = len(members)
        
        # Calculate power ranking
        power_ranking = 0
        for member in members:
            player_power = await get_player_power(member.player_id)
            power_ranking += player_power
        
        alliance.power_ranking = power_ranking
        
        # Save alliance
        await alliance.save()
        
    except Exception as e:
        logging.error(f"Error updating alliance stats: {e}", exc_info=True)

async def create_alliance(player_id: int, name: str) -> Dict[str, Any]:
    """
    Create a new alliance.
    
    Args:
        player_id: The player creating the alliance
        name: The name of the alliance
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate player exists
        if not await player_exists(player_id):
            return {
                "success": False,
                "message": "Player does not exist."
            }
        
        # Check if player is already in an alliance
        existing_member = await get_alliance_member(player_id)
        if existing_member:
            return {
                "success": False,
                "message": "You are already in an alliance. Leave your current alliance first."
            }
        
        # Validate alliance name
        if not name or len(name) < 3 or len(name) > 20:
            return {
                "success": False,
                "message": "Alliance name must be between 3 and 20 characters."
            }
        
        # Check if alliance name is already taken
        sheet = await get_sheet("Alliances")
        for row in sheet["values"]:
            if len(row) > 1 and row[1].lower() == name.lower():
                return {
                    "success": False,
                    "message": f"Alliance name '{name}' is already taken."
                }
        
        # Generate alliance ID and join code
        alliance_id = await get_next_alliance_id()
        join_code = await generate_join_code()
        
        # Create alliance
        alliance = Alliance(
            alliance_id=alliance_id,
            name=name,
            leader_id=player_id,
            join_code=join_code,
            created_at=datetime.now(),
            member_count=1,
            power_ranking=await get_player_power(player_id)
        )
        
        # Save alliance
        await alliance.save()
        
        # Add player as a member
        member = AllianceMember(
            player_id=player_id,
            alliance_id=alliance_id,
            joined_at=datetime.now(),
            role="leader"
        )
        
        # Save member
        await member.save()
        
        return {
            "success": True,
            "message": f"Alliance '{name}' created successfully! Join code: {join_code}"
        }
        
    except Exception as e:
        logging.error(f"Error creating alliance: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def join_alliance(player_id: int, join_code: str) -> Dict[str, Any]:
    """
    Join an existing alliance.
    
    Args:
        player_id: The player joining the alliance
        join_code: The alliance join code
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate player exists
        if not await player_exists(player_id):
            return {
                "success": False,
                "message": "Player does not exist."
            }
        
        # Check if player is already in an alliance
        existing_member = await get_alliance_member(player_id)
        if existing_member:
            return {
                "success": False,
                "message": "You are already in an alliance. Leave your current alliance first."
            }
        
        # Find alliance by join code
        alliance = await get_alliance_by_join_code(join_code)
        
        if not alliance:
            return {
                "success": False,
                "message": f"Alliance with join code '{join_code}' not found."
            }
        
        # Add player as a member
        member = AllianceMember(
            player_id=player_id,
            alliance_id=alliance.alliance_id,
            joined_at=datetime.now(),
            role="member"
        )
        
        # Save member
        await member.save()
        
        # Update alliance stats
        await update_alliance_stats(alliance.alliance_id)
        
        return {
            "success": True,
            "message": f"You have joined the alliance '{alliance.name}'!"
        }
        
    except Exception as e:
        logging.error(f"Error joining alliance: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def leave_alliance(player_id: int) -> Dict[str, Any]:
    """
    Leave an alliance.
    
    Args:
        player_id: The player leaving the alliance
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate player exists
        if not await player_exists(player_id):
            return {
                "success": False,
                "message": "Player does not exist."
            }
        
        # Check if player is in an alliance
        member = await get_alliance_member(player_id)
        
        if not member:
            return {
                "success": False,
                "message": "You are not in an alliance."
            }
        
        # Get alliance
        alliance = await get_alliance_by_id(member.alliance_id)
        
        if not alliance:
            # This shouldn't happen, but just in case
            # Delete the member record
            await update_sheet_row("AllianceMembers", member.row_index, ["", "", "", ""])
            
            return {
                "success": True,
                "message": "You have left the alliance."
            }
        
        # Check if player is the leader
        if member.role == "leader":
            # Check if there are other members
            members = await get_alliance_members(alliance.alliance_id)
            
            if len(members) > 1:
                # Find a new leader
                for potential_leader in members:
                    if potential_leader.player_id != player_id:
                        # Promote to leader
                        potential_leader.role = "leader"
                        await potential_leader.save()
                        break
            else:
                # Delete the alliance
                await update_sheet_row("Alliances", alliance.row_index, ["", "", "", "", "", "", ""])
        
        # Remove player from alliance
        await update_sheet_row("AllianceMembers", member.row_index, ["", "", "", ""])
        
        # Update alliance stats
        await update_alliance_stats(alliance.alliance_id)
        
        return {
            "success": True,
            "message": f"You have left the alliance '{alliance.name}'."
        }
        
    except Exception as e:
        logging.error(f"Error leaving alliance: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def invite_to_alliance(player_id: int, target_username: str) -> Dict[str, Any]:
    """
    Invite a player to an alliance.
    
    Args:
        player_id: The player sending the invite
        target_username: The username of the player to invite
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate player exists
        if not await player_exists(player_id):
            return {
                "success": False,
                "message": "Player does not exist."
            }
        
        # Check if player is in an alliance
        member = await get_alliance_member(player_id)
        
        if not member:
            return {
                "success": False,
                "message": "You are not in an alliance."
            }
        
        # Check if player has permission to invite (leader or officer)
        if member.role not in ["leader", "officer"]:
            return {
                "success": False,
                "message": "You don't have permission to invite players. Only leaders and officers can invite."
            }
        
        # Get alliance
        alliance = await get_alliance_by_id(member.alliance_id)
        
        if not alliance:
            return {
                "success": False,
                "message": "Alliance not found."
            }
        
        # Find target player by username
        sheet = await get_sheet("Players")
        target_row_index = None
        target_player_id = None
        
        for i, row in enumerate(sheet["values"]):
            if len(row) > 1 and row[1].lower() == target_username.lower():
                target_row_index = i + 1  # +1 for header row
                target_player_id = int(row[0])
                break
        
        if not target_player_id:
            return {
                "success": False,
                "message": f"Player with username '{target_username}' not found."
            }
        
        # Check if target player is already in an alliance
        target_member = await get_alliance_member(target_player_id)
        
        if target_member:
            return {
                "success": False,
                "message": f"Player '{target_username}' is already in an alliance."
            }
        
        # Return success with join code to send to the target player
        return {
            "success": True,
            "message": f"Invitation to '{target_username}' prepared. They can join using the code: {alliance.join_code}"
        }
        
    except Exception as e:
        logging.error(f"Error inviting to alliance: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }

async def get_alliance_info(player_id: int) -> Optional[Dict[str, Any]]:
    """
    Get information about a player's alliance.
    
    Args:
        player_id: The player ID
    
    Returns:
        Dictionary with alliance information or None if the player is not in an alliance
    """
    try:
        # Check if player is in an alliance
        member = await get_alliance_member(player_id)
        
        if not member:
            return None
        
        # Get alliance
        alliance = await get_alliance_by_id(member.alliance_id)
        
        if not alliance:
            return None
        
        # Get leader name
        leader = await get_player(alliance.leader_id)
        
        # Return alliance info
        return {
            "id": alliance.alliance_id,
            "name": alliance.name,
            "leader_id": alliance.leader_id,
            "leader_name": leader.display_name,
            "join_code": alliance.join_code,
            "created_at": alliance.created_at,
            "member_count": alliance.member_count,
            "power_ranking": alliance.power_ranking,
            "player_role": member.role
        }
        
    except Exception as e:
        logging.error(f"Error getting alliance info: {e}", exc_info=True)
        return None

async def disband_alliance(player_id: int) -> Dict[str, Any]:
    """
    Disband an alliance.
    
    Args:
        player_id: The player disbanding the alliance
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate player exists
        if not await player_exists(player_id):
            return {
                "success": False,
                "message": "Player does not exist."
            }
        
        # Check if player is in an alliance
        member = await get_alliance_member(player_id)
        
        if not member:
            return {
                "success": False,
                "message": "You are not in an alliance."
            }
        
        # Check if player is the leader
        if member.role != "leader":
            return {
                "success": False,
                "message": "Only the alliance leader can disband the alliance."
            }
        
        # Get alliance
        alliance = await get_alliance_by_id(member.alliance_id)
        
        if not alliance:
            return {
                "success": False,
                "message": "Alliance not found."
            }
        
        # Get all members
        members = await get_alliance_members(alliance.alliance_id)
        
        # Remove all members
        for m in members:
            await update_sheet_row("AllianceMembers", m.row_index, ["", "", "", ""])
        
        # Remove alliance
        await update_sheet_row("Alliances", alliance.row_index, ["", "", "", "", "", "", ""])
        
        return {
            "success": True,
            "message": f"Alliance '{alliance.name}' has been disbanded."
        }
        
    except Exception as e:
        logging.error(f"Error disbanding alliance: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }
