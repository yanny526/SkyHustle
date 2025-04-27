#   core/player.py
#   Defines the Player class and player-related data management functions,
#   using Google Sheets for storage

from typing import Optional, Dict, Any, List
from utils.google_sheets import get_sheet  # Assuming get_sheet() is in utils/google_sheets.py

#   Constants (can be moved to a config file later)
STARTING_CREDITS = 100
STARTING_ORE = 0
STARTING_ENERGY = 50
MAX_ENERGY = 100
PLAYERS_SHEET_NAME = "players"  #   Name of the worksheet for player data


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


#   --- Google Sheets Data Management Functions ---
def find_or_create_player(chat_id: int) -> Player:
    """
    Retrieves a player by chat ID from the Google Sheet.
    Creates a new player if one doesn't exist.
    """

    sheet = get_sheet()
    players_worksheet = sheet.worksheet(PLAYERS_SHEET_NAME)

    #   Assumptions about your sheet structure:
    #   -   Column 1: 'chat_id' (INT)
    #   -   Column 2: 'name' (STR)
    #   -   ... other player attributes

    try:
        #   Find the player by chat_id
        cell = players_worksheet.find(str(chat_id), in_column=1)
        player_data = players_worksheet.row_values(cell.row)
        player_dict = {
            "chat_id": int(player_data[0]),
            "name": player_data[1],
            "credits": int(player_data[2]),  #   Adjust indices based on your sheet
            "ore": int(player_data[3]),
            "energy": int(player_data[4]),
            "max_energy": int(player_data[5]),
            "army": json.loads(player_data[6]),
            "zone": player_data[7],
            "wins": int(player_data[8]),
            "losses": int(player_data[9]),
            "black_market_unlocked": player_data[10].lower() == "true",
            "items": json.loads(player_data[11]),
            "last_daily": player_data[12],
            "daily_streak": int(player_data[13]),
            "missions": json.loads(player_data[14]),
            "last_mission_reset": player_data[15],
            "refinery_level": int(player_data[16]),
            "lab_level": int(player_data[17]),
            "defense_level": int(player_data[18]),
            "research": json.loads(player_data[19]),
        }  #   ... and so on
        return Player.from_dict(player_dict)

    except gspread.exceptions.CellNotFound:
        #   Player not found, create a new one
        new_player = Player(chat_id)
        #   Append the new player data to the sheet
        players_worksheet.append_row(
            [
                new_player.chat_id,
                new_player.name,
                new_player.credits,
                new_player.ore,
                new_player.energy,
                new_player.max_energy,
                json.dumps(new_player.army),
                new_player.zone,
                new_player.wins,
                new_player.losses,
                new_player.black_market_unlocked,
                json.dumps(new_player.items),
                new_player.last_daily,
                new_player.daily_streak,
                json.dumps(new_player.missions),
                new_player.last_mission_reset,
                new_player.refinery_level,
                new_player.lab_level,
                new_player.defense_level,
                json.dumps(new_player.research),
            ]
        )  #   Adjust indices based on your sheet
        return new_player


def find_player_by_name(name: str) -> Optional[Player]:
    """
    Finds a player by their name (case-insensitive) in the Google Sheet.
    Returns None if no player is found.
    """

    sheet = get_sheet()
    players_worksheet = sheet.worksheet(PLAYERS_SHEET_NAME)

    #   Assumptions:
    #   -   Column 2: 'name'
    try:
        cell = players_worksheet.find(name, in_column=2, case_sensitive=False)
        player_data = players_worksheet.row_values(cell.row)
        player_dict = {
            "chat_id": int(player_data[0]),
            "name": player_data[1],
            "credits": int(player_data[2]),  #   Adjust indices based on your sheet
            "ore": int(player_data[3]),
            "energy": int(player_data[4]),
            "max_energy": int(player_data[5]),
            "army": json.loads(player_data[6]),
            "zone": player_data[7],
            "wins": int(player_data[8]),
            "losses": int(player_data[9]),
            "black_market_unlocked": player_data[10].lower() == "true",
            "items": json.loads(player_data[11]),
            "last_daily": player_data[12],
            "daily_streak": int(player_data[13]),
            "missions": json.loads(player_data[14]),
            "last_mission_reset": player_data[15],
            "refinery_level": int(player_data[16]),
            "lab_level": int(player_data[17]),
            "defense_level": int(player_data[18]),
            "research": json.loads(player_data[19]),
        }  #   ... and so on
        return Player.from_dict(player_dict)

    except gspread.exceptions.CellNotFound:
        return None


def save_player(player: Player):
    """
    Saves the player's data to the Google Sheet.
    """

    sheet = get_sheet()
    players_worksheet = sheet.worksheet(PLAYERS_SHEET_NAME)

    #   Assumptions:
    #   -   Column 1: 'chat_id' (INT) - Used to identify the row
    try:
        cell = players_worksheet.find(str(player.chat_id), in_column=1)
        row_index = cell.row
        players_worksheet.update_row(
            [
                player.chat_id,
                player.name,
                player.credits,
                player.ore,
                player.energy,
                player.max_energy,
                json.dumps(player.army),
                player.zone,
                player.wins,
                player.losses,
                player.black_market_unlocked,
                json.dumps(player.items),
                player.last_daily,
                player.daily_streak,
                json.dumps(player.missions),
                player.last_mission_reset,
                player.refinery_level,
                player.lab_level,
                player.defense_level,
                json.dumps(player.research),
            ],
            index=row_index,
        )  #   Adjust indices based on your sheet
    except gspread.exceptions.CellNotFound:
        #   Player not found (this should rarely happen, as we create on find_or_create)
        players_worksheet.append_row(
            [
                player.chat_id,
                player.name,
                player.credits,
                player.ore,
                player.energy,
                player.max_energy,
                json.dumps(player.army),
                player.zone,
                player.wins,
                player.losses,
                player.black_market_unlocked,
                json.dumps(player.items),
                player.last_daily,
                player.daily_streak,
                json.dumps(player.missions),
                player.last_mission_reset,
                player.refinery_level,
                player.lab_level,
                player.defense_level,
                json.dumps(player.research),
            ]
        )  #   Adjust indices based on your sheet


def get_all_players() -> List[Player]:
    """
    Returns a list of all players from the Google Sheet.
    """

    sheet = get_sheet()
    players_worksheet = sheet.worksheet(PLAYERS_SHEET_NAME)

    all_players: List[Player] = []
    player_records = players_worksheet.get_all_records()  #   Get all rows as a list of dicts

    for row in player_records:
        player_dict = {
            "chat_id": int(row["chat_id"]),
            "name": row["name"],
            "credits": int(row["credits"]),  #   Adjust keys based on your sheet
            "ore": int(row["ore"]),
            "energy": int(row["energy"]),
            "max_energy": int(row["max_energy"]),
            "army": json.loads(row["army"]),
            "zone": row["zone"],
            "wins": int(row["wins"]),
            "losses": int(row["losses"]),
            "black_market_unlocked": row["black_market_unlocked"].lower() == "true",
            "items": json.loads(row["items"]),
            "last_daily": row["last_daily"],
            "daily_streak": int(row["daily_streak"]),
            "missions": json.loads(row["missions"]),
            "last_mission_reset": row["last_mission_reset"],
            "refinery_level": int(row["refinery_level"]),
            "lab_level": int(row["lab_level"]),
            "defense_level": int(row["defense_level"]),
            "research": json.loads(row["research"]),
        }  #   ... and so on
        all_players.append(Player.from_dict(player_dict))
    return all_players


def reset_all_players():
    """
    Resets all player data in the Google Sheet (for testing purposes).
    WARNING: Use with caution!
    """

    sheet = get_sheet()
    players_worksheet = sheet.worksheet(PLAYERS_SHEET_NAME)
    players_worksheet.clear()  #   Clears the entire sheet
    #   Add header row back (if needed - adjust based on your sheet)
    players_worksheet.append_row(
        [
            "chat_id",
            "name",
            "credits",
            "ore",
            "energy",
            "max_energy",
            "army",
            "zone",
            "wins",
            "losses",
            "black_market_unlocked",
            "items",
            "last_daily",
            "daily_streak",
            "missions",
            "last_mission_reset",
            "refinery_level",
            "lab_level",
            "defense_level",
            "research",
        ]
    )
