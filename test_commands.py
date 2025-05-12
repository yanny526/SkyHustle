"""
Simple test script for SkyHustle Telegram bot commands.
This script tests the modules directly without the bot interface.
"""
import logging
import asyncio
from modules.player import get_player, create_player, update_player, claim_daily_reward
from modules.building import get_buildings, get_player_buildings, add_building_to_queue
from modules.alliance import get_alliance, create_alliance, join_alliance
from utils.formatter import format_status_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*50}")
    print(f"Testing: {title}")
    print(f"{'='*50}")

async def test_player_commands():
    """Test player-related commands."""
    print_header("Player Commands")
    
    # Test player creation
    print("\n## Creating new player")
    player_id = "123456789"  # Test Telegram user ID
    player = create_player(player_id, "TestCommander")
    
    if player:
        print(f"Player created: {player['display_name']}")
        print(f"Initial resources: {player['credits']} credits, {player['minerals']} minerals, {player['energy']} energy")
    else:
        print("Failed to create player")
    
    # Test getting player info
    print("\n## Retrieving player info")
    player = get_player(player_id)
    if player:
        status = format_status_message(player)
        print(f"Player status: \n{status}")
    else:
        print("Player not found")
    
    # Test updating player
    print("\n## Updating player name")
    result = update_player(player_id, {"display_name": "UpdatedCommander"})
    print(f"Update result: {result}")
    
    # Test daily reward
    print("\n## Claiming daily reward")
    reward_result = claim_daily_reward(player_id)
    print(f"Daily reward result: {reward_result}")

async def test_building_commands():
    """Test building-related commands."""
    print_header("Building Commands")
    
    # Test getting building types
    print("\n## Available building types")
    buildings = get_buildings()
    for idx, building in enumerate(buildings[:3]):  # Show first 3 for brevity
        print(f"{idx+1}. {building['name']} - {building['description']}")
    
    if len(buildings) > 3:
        print(f"... and {len(buildings) - 3} more building types")
    
    # Test player buildings
    player_id = "123456789"  # Test Telegram user ID
    print("\n## Player buildings")
    player_buildings = get_player_buildings(player_id)
    
    if player_buildings:
        for building in player_buildings:
            print(f"- {building.get('building_name', 'Unknown')} (Level {building.get('level', 1)})")
    else:
        print("No buildings yet")
    
    # Test adding a building
    print("\n## Adding a building to queue")
    first_building = buildings[0]['id'] if buildings else "command_center"
    result = add_building_to_queue(player_id, first_building)
    print(f"Build result: {result}")

async def test_alliance_commands():
    """Test alliance-related commands."""
    print_header("Alliance Commands")
    
    player_id = "123456789"  # Test Telegram user ID
    
    # Test creating alliance
    print("\n## Creating new alliance")
    alliance_result = create_alliance(player_id, "Test Sky Raiders")
    print(f"Alliance creation result: {alliance_result}")
    
    # Get alliance info
    if alliance_result and alliance_result.get('success'):
        alliance_id = alliance_result.get('alliance_id')
        
        print("\n## Alliance info")
        alliance = get_alliance(alliance_id)
        
        if alliance:
            print(f"Alliance: {alliance.get('alliance_name')}")
            print(f"Members: {alliance.get('member_count', 0)}")
            print(f"Join code: {alliance.get('join_code', 'None')}")
        else:
            print("Failed to get alliance info")
        
        # Test joining alliance
        print("\n## Testing alliance join with code")
        join_code = alliance.get('join_code') if alliance else None
        
        if join_code:
            # Create a second player
            second_player_id = "987654321"
            create_player(second_player_id, "JoiningPlayer")
            
            join_result = join_alliance(second_player_id, join_code)
            print(f"Join result: {join_result}")
        else:
            print("No join code available")
    else:
        print("Alliance creation failed, skipping additional tests")

async def run_tests():
    """Run all tests."""
    print("Starting SkyHustle module tests...\n")
    
    await test_player_commands()
    await test_building_commands()
    await test_alliance_commands()
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())