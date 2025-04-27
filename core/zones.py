#   core/zones.py
#   Defines functions for managing zone ownership

from core.player import Player
from typing import Optional, List

#   Constants (can be moved to a config file later)
#   ZONE_BONUSES = {
#       "zone1": {"ore_bonus": 0.1, "credit_bonus": 0.05},  #   Example bonuses
#       "zone2": {"army_bonus": 0.1},
#       "zone3": {"research_bonus": 0.05},
#   }


def find_zone_owner(zone_name: str, players: List[Player]) -> Optional[Player]:
    """
    Finds the player who owns a given zone.

    Args:
        zone_name: The name of the zone.
        players: A list of all players.

    Returns:
        The Player object of the zone's owner, or None if the zone is unclaimed.
    """
    for player in players:
        if player.zone == zone_name:
            return player
    return None


def claim_zone(player: Player, zone_name: str):
    """
    Assigns a zone to a player.

    Args:
        player: The player claiming the zone.
        zone_name: The name of the zone being claimed.
    """
    player.zone = zone_name


def abandon_zone(player: Player):
    """
    Removes a player's ownership of their current zone.

    Args:
        player: The player abandoning the zone.
    """
    player.zone = None


def apply_zone_bonuses(player: Player):
    """
    Applies any bonuses associated with the player's current zone.

    Args:
        player: The player to apply bonuses to.

    This is a placeholder for more complex zone bonus logic.
    """
    #   Placeholder for zone bonus application
    #   if player.zone:
    #       bonuses = ZONE_BONUSES.get(player.zone)
    #       if bonuses:
    #           #   Apply bonuses to player attributes (e.g., resource generation, army stats)
    #           pass
    pass
