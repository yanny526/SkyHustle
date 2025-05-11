"""
Quick test script for SkyHustle Telegram bot.
This script tests core functionality without taking too much time.
"""
import logging
from modules.player import get_player, create_player
from utils.constants import BUILDING_TYPES, UNIT_TYPES
from utils.sheets_service import get_sheet_data
from config import SHEET_NAMES

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("SkyHustle Quick Test\n")

# Test player module
print("Testing player module...")
player_id = "123456789"  # Test Telegram user ID

# Create a player
player = create_player(player_id, "TestCommander")
if player:
    print(f"✅ Successfully created player: {player['display_name']}")
else:
    print("❌ Failed to create player")

# Retrieve player
player = get_player(player_id)
if player:
    print(f"✅ Successfully retrieved player: {player['display_name']}")
    print(f"   Credits: {player['credits']}, Minerals: {player['minerals']}, Energy: {player['energy']}")
else:
    print("❌ Failed to retrieve player")

# Test game constants
print("\nTesting game constants...")
print(f"✅ {len(BUILDING_TYPES)} building types available")
print(f"✅ {len(UNIT_TYPES)} unit types available")

# Test sheet connection
print("\nTesting Google Sheets connection...")
try:
    players = get_sheet_data(SHEET_NAMES['players'])
    print(f"✅ Connected to Players sheet, found {len(players)} players")
except Exception as e:
    print(f"❌ Error connecting to Players sheet: {e}")

print("\nQuick test completed.")