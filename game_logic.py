"""
game_logic.py:

This file contains the functions that implement the core mechanics of the SkyHustle game.
"""

import random
from utils import format_number
from sheets_api import read_sheet, write_to_sheet, append_to_sheet
from constants import (
    RESOURCE_NAMES,
    BUILDING_NAMES,
    UNIT_TYPES,
    PLAYER_SHEET_NAME,
    NPC_SHEET_NAME,
    NPC_STARTING_ROW
)

# --- Helper Functions ---

def get_player_row(user_id: int) -> int or None:
    """
    Retrieves the row number of a player in the Google Sheet based on their user ID.

    Args:
        user_id: The Telegram user ID of the player.

    Returns:
        The row number of the player in the sheet, or None if not found.
    """
    player_data = read_sheet(PLAYER_SHEET_NAME, "A2:A")  # Read all player IDs
    if player_data:
        for i, row in enumerate(player_data, start=2):  # Start from row 2
            if row and row[0] == str(user_id):
                return i
    return None

def get_npc_row(x: int, y: int) -> int or None:
    """
    Retrieves the row number of an NPC in the Google Sheet based on its coordinates.

    Args:
        x: The x-coordinate of the NPC.
        y: The y-coordinate of the NPC.

    Returns:
        The row number of the NPC in the sheet, or None if not found.
    """
    npc_data = read_sheet(NPC_SHEET_NAME, f"B{NPC_STARTING_ROW}:C")  # Read all NPC coordinates
    if npc_data:
        for i, row in enumerate(npc_data, start=NPC_STARTING_ROW):
            if len(row) >= 2:
                try:
                    npc_x = int(row[0])
                    npc_y = int(row[1])
                    if npc_x == x and npc_y == y:
                        return i
                except ValueError:
                    # Handle non-integer data in the coordinates
                    print(f"Warning: Non-integer coordinates found in NPC data: {row}")
                    continue
    return None

def initialize_player(user_id: int, username: str) -> bool:
    """
    Initializes a new player in the Google Sheet or resets their resources if they exist.

    Args:
        user_id: The Telegram user ID of the player.
        username: The Telegram username of the player.

    Returns:
        True if the player was successfully initialized or reset, False on error.
    """
    player_row = get_player_row(user_id)
    if player_row:
        # Player exists, reset their resources
        initial_resources = [1000] * len(RESOURCE_NAMES)  # Example: 1000 of each resource
        resource_range = f"D{player_row}:{(chr(67 + len(RESOURCE_NAMES)) + str(player_row))}" # Calculate the range dynamically.  D is the 4th column, and ресурси is after id, username, coordinates
        write_to_sheet(PLAYER_SHEET_NAME, resource_range, [initial_resources])
        return False #Return false because player existed
    else:
        # Player does not exist, create a new entry
        new_player_data = [user_id, "1,1", username] + [1000] * len(RESOURCE_NAMES)  # Example starting resources
        append_to_sheet(PLAYER_SHEET_NAME, new_player_data)
        return True # Return true because new player

def get_player_resources(user_id: int) -> dict[str, int] or None:
    """
    Retrieves a player's resources from the Google Sheet.

    Args:
        user_id: The Telegram user ID of the player.

    Returns:
        A dictionary of resources (name: amount), or None if the player is not found.
    """
    player_row = get_player_row(user_id)
    if player_row:
        resource_range = f"D{player_row}:{(chr(67 + len(RESOURCE_NAMES)) + str(player_row))}"
        resources_data = read_sheet(PLAYER_SHEET_NAME, resource_range)
        if resources_data and resources_data[0]:
            return dict(zip(RESOURCE_NAMES, map(int, resources_data[0])))
        else:
            return None
    else:
        return None

def update_player_resources(user_id: int, resources: dict[str, int]) -> bool:
    """
    Updates a player's resources in the Google Sheet.

    Args:
        user_id: The Telegram user ID of the player.
        resources: A dictionary of resources (name: amount) to update.

    Returns:
        True if the resources were successfully updated, False otherwise.
    """
    player_row = get_player_row(user_id)
    if player_row:
        resource_list = [resources.get(name, 0) for name in RESOURCE_NAMES] # Handles if a resource is not in the dict
        resource_range = f"D{player_row}:{(chr(67 + len(RESOURCE_NAMES)) + str(player_row))}"
        write_to_sheet(PLAYER_SHEET_NAME, resource_range, [resource_list])
        return True
    else:
        return False

def get_resource_production(user_id: int) -> dict[str, int] or None:
    """
    Calculates the resource production for a player.  This is a placeholder,
    and the actual calculation would depend on the player's buildings and upgrades.

    Args:
        user_id: The Telegram user ID of the player.

    Returns:
        A dictionary of resource production rates (name: amount), or None if player not found.
    """
    player_row = get_player_row(user_id)
    if player_row:
        production = {}
        for resource in RESOURCE_NAMES:
            # Placeholder:  Replace with actual calculation based on buildings/units
            production[resource] = 10  # Example: 10 per hour for each resource.
        return production
    else:
        return None

def calculate_attack_damage(user_id: int) -> int:
    """
    Calculates the attack damage of a player.  This is a placeholder.

    Args:
        user_id: The Telegram user ID of the player.

    Returns:
        The attack damage of the player.
    """
    # Placeholder:  Replace with actual calculation based on units and upgrades.
    return 100  # Example: 100 attack damage

def get_player_defense(user_id: int) -> int:
    """
    Calculates the defense rating of a player.  This is a placeholder.

    Args:
        user_id: The Telegram user ID of the player.

    Returns:
        The defense rating of the player.
    """
    # Placeholder: Replace with actual calculation based on buildings and units.
    return 50  # Example: 50 defense

def calculate_travel_time(start_x: int, start_y: int, end_x: int, end_y: int) -> int:
    """
    Calculates the travel time between two points.  This is a placeholder.

    Args:
        start_x: The x-coordinate of the starting point.
        start_y: The y-coordinate of the starting point.
        end_x: The x-coordinate of the ending point.
        end_y: The y-coordinate of the ending point.

    Returns:
        The travel time in seconds.
    """
    # Placeholder: Replace with actual calculation based on distance and speed.
    distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
    return int(distance * 10)  # Example: 10 seconds per unit of distance

def apply_attack_results(attacker_resources: dict[str, int], attacker_damage: int, defender_defense: int, target_is_npc: bool) -> dict or str:
    """
    Applies the results of an attack, including resource transfer and unit losses.

    Args:
        attacker_resources: A dictionary of the attacker's resources.
        attacker_damage: The attack damage of the attacker.
        defender_defense: The defense rating of the defender.
        target_is_npc: Boolean indicating if the target is an NPC

    Returns:
        A dictionary containing the result of the attack and any spoils,
        or "npc_attacked" if the target was an NPC.
    """

    # Placeholder:  Replace with actual battle logic.
    result = {}
    if target_is_npc:
        #NPC attacked.
        spoils_amount = random.randint(100, 500)  # Example: Random spoils between 100 and 500
        spoils = {RESOURCE_NAMES[0]: spoils_amount} #Give only the first resource.
        return spoils
    else:
        if attacker_damage > defender_defense:
            # Attacker wins.
            spoils_percentage = 0.2  # Example: 20% of defender's resources
            spoils = {}
            for resource_name in RESOURCE_NAMES:
                defender_resource_amount = defender_resources.get(resource_name, 0)
                spoils_amount = int(defender_resource_amount * spoils_percentage)
                if spoils_amount > 0 :
                    spoils[resource_name] = spoils_amount
                # Deduct spoils from the defender.  This is done in memory; the actual
                # update to the sheet will be handled later.
                attacker_resources[resource_name] += spoils_amount #add resources to attacker
            result["result"] = "attacker"
            result["spoils"] = spoils
            return result
        elif attacker_damage < defender_defense:
            result["result"] = "defender" # Defender wins.
            result["spoils"] = {}
            return result
        else:
            result["result"] = "tie"
            result["spoils"] = {}
            return result # Tie
        # Defender loses resources.

def send_resources(attacker_id:int, defender_id:int, spoils:dict):
    """
    Sends resources from the defender to the attacker

    Args:
        attacker_id: the telegram ID of the attacker
        defender_id: the telegram ID of the defender
        spoils: dictionary of resources
    """
    attacker_row = get_player_row(attacker_id)
    defender_row = get_player_row(defender_id)
    if attacker_row and defender_row:
        attacker_resources = get_player_resources(attacker_id)
        defender_resources = get_player_resources(defender_id)
        for resource_name, amount in spoils.items():
            if amount > 0:
                defender_resources[resource_name] -= amount
                attacker_resources[resource_name] += amount
        #write new resources to the sheet
        update_player_resources(attacker_id, attacker_resources)
        update_player_resources(defender_id, defender_resources)

def get_shop_items() -> dict:
    """
    Returns a dictionary of items available in the shop.  This is a placeholder.

    Returns:
        A dictionary of shop items (item_name: item_data).
    """
    # Placeholder:  Replace with actual data from a config file or Google Sheet.
    return {
        "basic_sword": {
            "description": "A basic sword for attacking",
            "cost": {"gold": 100},
            "type": "unit",
            "attack": 10,
        },
        "basic_shield": {
            "description": "A basic shield for defense",
            "cost": {"gold": 80},
            "type": "unit",
            "defense": 10,
        },
        "stone_mine": {
            "description": "A mine that produces stone",
            "cost": {"gold": 200, "stone": 50},
            "type": "building",
            "production": {"stone": 5},  # Per hour
        },
        "wood_cutter": {
            "description": "A building that produces wood",
            "cost": {"gold": 150, "wood": 50},
            "type": "building",
            "production": {"wood": 5},
        },
    }

def buy_shop_item(user_id: int, item_name: str, quantity: int) -> bool:
    """
    Handles the purchase of an item from the shop.

    Args:
        user_id: The Telegram user ID of the player.
        item_name: The name of the item to buy.
        quantity: The quantity of the item to buy.

    Returns:
        True if the purchase was successful, False otherwise.
    """
    player_resources = get_player_resources(user_id)
    if not player_resources:
        return False  # Player not found.

    shop_items = get_shop_items()
    item = shop_items.get(item_name)
    if not item:
        return False  # Item not found.

    # Check if the player has enough resources.
    for resource, cost in item["cost"].items():
        if player_resources.get(resource, 0) < cost * quantity:
            return False  # Not enough resources.

    # Deduct the resources.
    for resource, cost in item["cost"].items():
        player_resources[resource] -= cost * quantity

    # Update the player's resources in the Google Sheet.
    if not update_player_resources(user_id, player_resources):
        return False  # Failed to update resources.

    # Apply the item's effects (e.g., add to player's units, buildings, etc.).
    # This is a placeholder; the actual implementation will depend on the item type.
    if item["type"] == "unit":
        #  Add units to player.  You'll need to track units in the Google Sheet.
        pass
    elif item["type"] == "building":
        #  Add building to player.  You'll need to track buildings.
        pass
    #  Return True if the purchase was successful.
    return True

# --- NPC Functions ---
def create_npc(x: int, y: int, level: int, npc_type: str) -> bool:
    """
    Creates a new NPC in the Google Sheet.

    Args:
        x: The x-coordinate of the NPC.
        y: The y-coordinate of the NPC.
        level: The level of the NPC.
        npc_type: The type of the NPC (base, trader, raider).

    Returns:
        True if the NPC was created successfully, False otherwise.
    """
    # Check if there is already an NPC or player at the coordinates.
    if get_npc_row(x, y) or get_player_row_by_coordinates(x,y): # Use the helper function
        return False  # Already exists.

    # Determine starting resources and other attributes based on level and type.
    if npc_type == "base":
        resources = [1000 * level] * len(RESOURCE_NAMES)  # Example
        defense = 10 * level
        attack = 0
    elif npc_type == "trader":
        resources = [500 * level] * len(RESOURCE_NAMES)
        defense = 5 * level
        attack = 0
    elif npc_type == "raider":
        resources = [100 * level] * len(RESOURCE_NAMES)
        defense = 5 * level
        attack = 20 * level
    else:
        return False  # Invalid NPC type

    # Append the NPC data to the sheet.
    npc_data = [x, y, level, npc_type, defense, attack] + resources
    append_to_sheet(NPC_SHEET_NAME, npc_data)
    return True

def get_npc_data(x: int, y: int) -> dict or None:
    """
    Retrieves the data for an NPC from the Google Sheet.

    Args:
        x: The x-coordinate of the NPC.
        y: The y-coordinate of the NPC.

    Returns:
        A dictionary containing the NPC's data, or None if not found.
    """
    npc_row = get_npc_row(x, y)
    if npc_row:
        npc_data = read_sheet(NPC_SHEET_NAME, f"A{npc_row}:{(chr(64 + 6 + len(RESOURCE_NAMES)))}{npc_row}")  # Adjust the column range
        if npc_data and npc_data[0]:
            # Construct a dictionary with keys
            npc_dict = {
                "x": int(npc_data[0][0]),
                "y": int(npc_data[0][1]),
                "level": int(npc_data[0][2]),
                "type": npc_data[0][3],
                "defense": int(npc_data[0][4]),
                "attack": int(npc_data[0][5]),
            }
            resource_data = dict(zip(RESOURCE_NAMES, map(int, npc_data[0][6:])))
            npc_dict["resources"] = resource_data
            return npc_dict
        else:
            return None
    else:
        return None

def update_npc_data(x: int, y: int, spoils:dict) -> bool:
    """
    Updates the resources of an NPC in the Google Sheet.

    Args:
        x: The x-coordinate of the NPC.
        y: The y-coordinate of the NPC.
        spoils: the spoils of the attack

    Returns:
        True if the NPC data was updated successfully, False otherwise.
    """
    npc_row = get_npc_row(x, y)
    if npc_row:
        npc_data = get_npc_data(x,y)
        if npc_data:
             new_resources = {}
             for resource_name in RESOURCE_NAMES:
                new_resources[resource_name] = npc_data["resources"][resource_name] - spoils.get(resource_name,0)
             resource_list = [new_resources.get(name, 0) for name in RESOURCE_NAMES]
             resource_range = f"G{npc_row}:{(chr(64 + 6 + len(RESOURCE_NAMES)))}{npc_row}"
             write_to_sheet(NPC_SHEET_NAME, resource_range, [resource_list])
             return True
        else:
            return False
    else:
        return False

def npc_attack(x: int, y: int) -> dict:
    """
    Simulates an NPC attack on a player.  This is a placeholder.

    Args:
        x: The x-coordinate of the NPC.
        y: The y-coordinate of the NPC.

    Returns:
        A dictionary of spoils from the attack.
    """
    # Placeholder:  Replace with actual attack logic.
    npc_data = get_npc_data(x,y)
    if npc_data:
        spoils_amount = random.randint(50, 200) * npc_data["level"]  # Example: Spoils based on NPC level
        spoils = {RESOURCE_NAMES[0]: spoils_amount}  # Give only the first resource
        return spoils
    else:
        return {}

def distribute_spoils(user_id:int, spoils:dict):
    """
    Distributes the spoils of an attack to the player

    Args:
        user_id: the telegram ID of the player
        spoils: the spoils of the attack
    """
    player_resources = get_player_resources(user_id)
    if player_resources:
        for resource_name, amount in spoils.items():
            player_resources[resource_name] += amount
        update_player_resources(user_id, player_resources)

def get_player_row_by_coordinates(x: int, y: int) -> int or None:
    """
    Retrieves the row number of a player in the Google Sheet based on their coordinates.

    Args:
        x: The x-coordinate of the player.
        y: The y-coordinate of the player.

    Returns:
        The row number of the player in the sheet, or None if not found.
    """
    player_data = read_sheet(PLAYER_SHEET_NAME, f"B2:B1000")  # Read all player coordinates
    if player_data:
        for i, row in enumerate(player_data, start=2):
            if len(row) >= 1:
                player_x, player_y = map(int, row[0].split(','))
                if player_x == x and player_y == y:
                    return i
    return None


def get_npc_defense(x: int, y: int) -> int:
    """
    Retrieves the defense value for the NPC at coordinates (x, y).
    """
    npc = get_npc_data(x, y)
    if npc and "defense" in npc:
        return int(npc["defense"])
    return 0
