#   core/player.py
#   Defines the Player class and player-related data management functions

from typing import Optional, Dict, Any
import json

#   Constants (can be moved to a config file later)
STARTING_CREDITS = 100
STARTING_ORE = 0
STARTING_ENERGY = 50
MAX_ENERGY = 100


class Player:
    """
    Represents a player in the game.
    """

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.name: str = f"Commander {chat_id}"  #   Default name
        self.credits: int = STARTING_CREDITS
        self.ore: int = STARTING_ORE
        self.energy: int = STARTING_ENERGY
        self.max_energy: int = MAX_ENERGY
        self.army: Dict[str, int] = {"scout": 0, "tank": 0, "drone": 0}
        self.zone: Optional[str] = None  #   Assigned zone (if any)
        self.wins: int = 0
        self.losses: int = 0
        self.black_market_unlocked: bool = False
        self.items: list[str] = []  #   List of item IDs
        self.last_daily: str = ""  #   Date of last daily reward
        self.daily_streak: int = 0
        self.missions: dict[str, bool] = {
            "mine5": False,
            "win1": False,
            "forge5": False,
        }  #   Daily missions
        self.last_mission_reset: str = ""  #   Date of last mission reset
        self.refinery_level: int = 1
        self.lab_level: int = 1
        self.defense_level: int = 1
        self.research: dict[str, int] = {"speed": 0, "armor": 0}

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the Player object to a dictionary for storage.
        """
        return {
            "chat_id": self.chat_id,
            "name": self.name,
            "credits": self.credits,
            "ore": self.ore,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "army": self.army,
            "zone": self.zone,
            "wins": self.wins,
            "losses": self.losses,
            "black_market_unlocked": self.black_market_unlocked,
            "items": self.items,
            "last_daily": self.last_daily,
            "daily_streak": self.daily_streak,
            "missions": self.missions,
            "last_mission_reset": self.last_mission_reset,
            "refinery_level": self.refinery_level,
            "lab_level": self.lab_level,
            "defense_level": self.defense_level,
            "research": self.research,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        """
        Creates a Player object from a dictionary (e.g., loaded from storage).
        """
        player = cls(data["chat_id"])
        player.name = data["name"]
        player.credits = data["credits"]
        player.ore = data["ore"]
        player.energy = data["energy"]
        player.max_energy = data["max_energy"]
        player.army = data["army"]
        player.zone = data["zone"]
        player.wins = data["wins"]
        player.losses = data["losses"]
        player.black_market_unlocked = data["black_market_unlocked"]
        player.items = data["items"]
        player.last_daily = data["last_daily"]
        player.daily_streak = data["daily_streak"]
        player.missions = data["missions"]
        player.last_mission_reset = data["last_mission_reset"]
        player.refinery_level = data["refinery_level"]
        player.lab_level = data["lab_level"]
        player.defense_level = data["defense_level"]
        player.research = data["research"]
        return player


#   --- Player Data Management Functions ---
_players: dict[int, Player] = {}  #   In-memory storage (replace with DB later)


def find_or_create_player(chat_id: int) -> Player:
    """
    Retrieves a player by chat ID. Creates a new player if one doesn't exist.
    """
    if chat_id not in _players:
        _players[chat_id] = Player(chat_id)
    return _players[chat_id]


def find_player_by_name(name: str) -> Optional[Player]:
    """
    Finds a player by their name (case-insensitive).
    Returns None if no player is found.
    """
    for player in _players.values():
        if player.name.lower() == name.lower():
            return player
    return None


def save_player(player: Player):
    """
    Saves the player's data to storage (in-memory for now).
    """
    _players[player.chat_id] = player


def get_all_players() -> list[Player]:
    """
    Returns a list of all players.
    """
    return list(_players.values())


def reset_all_players():
    """
    Resets all player data (for testing purposes).
    """
    _players.clear()
