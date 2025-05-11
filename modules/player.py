"""
Player module for SkyHustle.
Handles player data and operations.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils.sheets import get_sheet, find_row_by_col_value, update_row, append_row
from config import SHEET_NAMES

class Player:
    """Player class representing a game player."""
    
    def __init__(self, player_id: int, display_name: str, 
                 credits: int = 500, minerals: int = 200, energy: int = 100, 
                 skybucks: int = 0, experience: int = 0, level: int = 1,
                 tutorial_completed: bool = False, tutorial_state: str = "",
                 last_login: datetime = None, daily_streak: int = 0, 
                 last_daily: datetime = None, alliance_id: str = "", 
                 row_index: int = None):
        """
        Initialize a Player instance.
        
        Args:
            player_id: Telegram user ID
            display_name: Display name in game
            credits: Current credits
            minerals: Current minerals
            energy: Current energy
            skybucks: Current skybucks (premium currency)
            experience: Current experience points
            level: Current player level
            tutorial_completed: Whether tutorial is completed
            tutorial_state: Current tutorial state
            last_login: Last login timestamp
            daily_streak: Current daily login streak
            last_daily: Last daily claim timestamp
            alliance_id: ID of the player's alliance
            row_index: Row index in the Google Sheet
        """
        self.player_id = player_id
        self.display_name = display_name
        self.credits = credits
        self.minerals = minerals
        self.energy = energy
        self.skybucks = skybucks
        self.experience = experience
        self.level = level
        self.tutorial_completed = tutorial_completed
        self.tutorial_state = tutorial_state
        self.last_login = last_login or datetime.now()
        self.daily_streak = daily_streak
        self.last_daily = last_daily
        self.alliance_id = alliance_id
        self.row_index = row_index
    
    @classmethod
    async def from_row(cls, row: List[str], row_index: int) -> 'Player':
        """
        Create a Player instance from a row of data.
        
        Args:
            row: List of values from a row in the player sheet
            row_index: Index of the row in the sheet
            
        Returns:
            Player instance
        """
        try:
            # Parse row data
            player_id = int(row[0])
            display_name = row[1]
            credits = int(row[2])
            minerals = int(row[3])
            energy = int(row[4])
            skybucks = int(row[5])
            experience = int(row[6])
            level = int(row[7]) if len(row) > 7 and row[7] else 1
            tutorial_completed = row[8].upper() == "TRUE" if len(row) > 8 and row[8] else False
            tutorial_state = row[9] if len(row) > 9 and row[9] else ""
            
            # Parse dates
            last_login = None
            if len(row) > 10 and row[10]:
                try:
                    last_login = datetime.strptime(row[10], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_login = datetime.now()
            else:
                last_login = datetime.now()
            
            daily_streak = int(row[11]) if len(row) > 11 and row[11] else 0
            
            last_daily = None
            if len(row) > 12 and row[12]:
                try:
                    last_daily = datetime.strptime(row[12], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            alliance_id = row[13] if len(row) > 13 and row[13] else ""
            
            return cls(
                player_id=player_id,
                display_name=display_name,
                credits=credits,
                minerals=minerals,
                energy=energy,
                skybucks=skybucks,
                experience=experience,
                level=level,
                tutorial_completed=tutorial_completed,
                tutorial_state=tutorial_state,
                last_login=last_login,
                daily_streak=daily_streak,
                last_daily=last_daily,
                alliance_id=alliance_id,
                row_index=row_index
            )
        
        except Exception as e:
            logging.error(f"Error creating Player from row: {e}", exc_info=True)
            raise
    
    async def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Player instance to a dictionary for storage.
        
        Returns:
            Dictionary representation
        """
        return {
            "player_id": str(self.player_id),
            "display_name": self.display_name,
            "credits": self.credits,
            "minerals": self.minerals,
            "energy": self.energy,
            "skybucks": self.skybucks,
            "experience": self.experience,
            "level": self.level,
            "tutorial_completed": "TRUE" if self.tutorial_completed else "FALSE",
            "tutorial_state": self.tutorial_state,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
            "daily_streak": self.daily_streak,
            "last_daily": self.last_daily.strftime("%Y-%m-%d %H:%M:%S") if self.last_daily else "",
            "alliance_id": self.alliance_id
        }
    
    async def to_row(self) -> List[Any]:
        """
        Convert the Player instance to a row for storage.
        
        Returns:
            List of values for a row
        """
        player_dict = await self.to_dict()
        return [
            player_dict["player_id"],
            player_dict["display_name"],
            player_dict["credits"],
            player_dict["minerals"],
            player_dict["energy"],
            player_dict["skybucks"],
            player_dict["experience"],
            player_dict["level"],
            player_dict["tutorial_completed"],
            player_dict["tutorial_state"],
            player_dict["last_login"],
            player_dict["daily_streak"],
            player_dict["last_daily"],
            player_dict["alliance_id"]
        ]
    
    async def save(self) -> bool:
        """
        Save the Player instance to the database.
        
        Returns:
            Whether the save was successful
        """
        try:
            # Convert to row
            row_data = await self.to_row()
            
            # Update or append
            if self.row_index:
                # Update existing row
                return await update_row(SHEET_NAMES["players"], self.row_index, row_data)
            else:
                # Append new row
                success = await append_row(SHEET_NAMES["players"], row_data)
                if success:
                    # Find the new row index
                    row_index, _ = await find_row_by_col_value(SHEET_NAMES["players"], 0, str(self.player_id))
                    self.row_index = row_index
                return success
        
        except Exception as e:
            logging.error(f"Error saving Player {self.player_id}: {e}", exc_info=True)
            return False
    
    async def update_login(self) -> bool:
        """
        Update the player's last login time.
        
        Returns:
            Whether the update was successful
        """
        self.last_login = datetime.now()
        return await self.save()
    
    async def add_resources(self, credits: int = 0, minerals: int = 0, 
                           energy: int = 0, skybucks: int = 0) -> bool:
        """
        Add resources to the player.
        
        Args:
            credits: Credits to add
            minerals: Minerals to add
            energy: Energy to add
            skybucks: Skybucks to add
            
        Returns:
            Whether the update was successful
        """
        self.credits += credits
        self.minerals += minerals
        self.energy += energy
        self.skybucks += skybucks
        
        return await self.save()
    
    async def can_afford(self, credits: int = 0, minerals: int = 0, 
                        energy: int = 0, skybucks: int = 0) -> bool:
        """
        Check if the player can afford a purchase.
        
        Args:
            credits: Credits required
            minerals: Minerals required
            energy: Energy required
            skybucks: Skybucks required
            
        Returns:
            Whether the player can afford it
        """
        return (self.credits >= credits and 
                self.minerals >= minerals and 
                self.energy >= energy and 
                self.skybucks >= skybucks)
    
    async def spend_resources(self, credits: int = 0, minerals: int = 0, 
                             energy: int = 0, skybucks: int = 0) -> bool:
        """
        Spend resources if the player can afford it.
        
        Args:
            credits: Credits to spend
            minerals: Minerals to spend
            energy: Energy to spend
            skybucks: Skybucks to spend
            
        Returns:
            Whether the purchase was successful
        """
        if not await self.can_afford(credits, minerals, energy, skybucks):
            return False
        
        self.credits -= credits
        self.minerals -= minerals
        self.energy -= energy
        self.skybucks -= skybucks
        
        return await self.save()
    
    async def add_experience(self, amount: int) -> bool:
        """
        Add experience points and handle level-ups.
        
        Args:
            amount: Experience points to add
            
        Returns:
            Whether a level-up occurred
        """
        self.experience += amount
        
        # Check for level-up
        # Simple level formula: level = 1 + floor(sqrt(experience / 100))
        new_level = 1 + int((self.experience / 100) ** 0.5)
        level_up = new_level > self.level
        
        if level_up:
            self.level = new_level
        
        await self.save()
        return level_up
    
    async def claim_daily(self) -> tuple[bool, int, int, int]:
        """
        Claim daily reward.
        
        Returns:
            Tuple of (claimed, credits, minerals, energy)
        """
        from config import DAILY_REWARDS, DAILY_STREAK_BONUS
        
        now = datetime.now()
        
        # Check if already claimed today
        if self.last_daily:
            today = now.date()
            last_claim_date = self.last_daily.date()
            
            if today == last_claim_date:
                return (False, 0, 0, 0)
            
            # Check for streak (consecutive days)
            if (today - last_claim_date).days == 1:
                self.daily_streak += 1
            else:
                self.daily_streak = 1
        else:
            self.daily_streak = 1
        
        # Calculate reward with streak bonus
        streak_multiplier = 1 + (self.daily_streak - 1) * DAILY_STREAK_BONUS
        credits = int(DAILY_REWARDS["credits"] * streak_multiplier)
        minerals = int(DAILY_REWARDS["minerals"] * streak_multiplier)
        energy = int(DAILY_REWARDS["energy"] * streak_multiplier)
        
        # Update player
        self.credits += credits
        self.minerals += minerals
        self.energy += energy
        self.last_daily = now
        
        await self.save()
        
        return (True, credits, minerals, energy)
    
    async def set_display_name(self, name: str) -> bool:
        """
        Set the player's display name.
        
        Args:
            name: New display name
            
        Returns:
            Whether the update was successful
        """
        from config import MAX_NAME_LENGTH
        
        # Sanitize and validate
        name = name.strip()
        if not name or len(name) > MAX_NAME_LENGTH:
            return False
        
        self.display_name = name
        return await self.save()
    
    async def set_tutorial_state(self, tutorial_state: str) -> bool:
        """
        Set the player's tutorial state.
        
        Args:
            tutorial_state: New tutorial state
            
        Returns:
            Whether the update was successful
        """
        self.tutorial_state = tutorial_state
        return await self.save()
    
    async def complete_tutorial(self) -> bool:
        """
        Mark the tutorial as completed.
        
        Returns:
            Whether the update was successful
        """
        self.tutorial_completed = True
        self.tutorial_state = "completed"
        return await self.save()

async def player_exists(player_id: int) -> bool:
    """
    Check if a player exists in the database.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        Whether the player exists
    """
    row_index, _ = await find_row_by_col_value(SHEET_NAMES["players"], 0, str(player_id))
    return row_index is not None

async def get_player(player_id: int) -> Optional[Player]:
    """
    Get a player from the database.
    
    Args:
        player_id: Telegram user ID
        
    Returns:
        Player instance or None if not found
    """
    row_index, row = await find_row_by_col_value(SHEET_NAMES["players"], 0, str(player_id))
    
    if row_index and row:
        return await Player.from_row(row, row_index)
    else:
        return None

async def create_player(player_id: int, display_name: str) -> Player:
    """
    Create a new player and save to the database.
    
    Args:
        player_id: Telegram user ID
        display_name: Display name in game
        
    Returns:
        New Player instance
    """
    # Create player with default values
    player = Player(player_id=player_id, display_name=display_name)
    
    # Save to database
    await player.save()
    
    return player

async def get_top_players(limit: int = 10) -> List[Player]:
    """
    Get the top players by experience.
    
    Args:
        limit: Maximum number of players to return
        
    Returns:
        List of Player instances
    """
    from utils.sheets import get_all_rows
    
    # Get all players
    rows = await get_all_rows(SHEET_NAMES["players"])
    
    # Create Player instances
    players = []
    for i, row in enumerate(rows, start=2):  # Start at row 2 (after header)
        try:
            player = await Player.from_row(row, i)
            players.append(player)
        except Exception as e:
            logging.error(f"Error creating Player from row {i}: {e}", exc_info=True)
    
    # Sort by experience (descending)
    players.sort(key=lambda p: p.experience, reverse=True)
    
    # Return top players
    return players[:limit]