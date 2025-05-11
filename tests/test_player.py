"""
Tests for the Player module in the SkyHustle Telegram bot.
"""
import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

from modules.player import Player, get_player, create_player, player_exists

# Mock sheet data
mock_sheet = {
    "name": "Players",
    "values": [
        ["player_id", "display_name", "credits", "minerals", "energy", "skybucks", "experience", "tutorial_completed", "tutorial_state", "last_login"],
        ["123456789", "TestPlayer", "1000", "500", "250", "10", "100", "FALSE", "", "2023-01-01 12:00:00"],
    ]
}

# Test Player class initialization
def test_player_init():
    player = Player(
        player_id=123456789,
        display_name="TestCommander",
        credits=1000,
        minerals=500,
        energy=250,
        skybucks=10,
        experience=100,
        tutorial_completed=False,
        tutorial_state="",
        last_login=datetime.now(),
        row_index=2
    )
    
    assert player.player_id == 123456789
    assert player.display_name == "TestCommander"
    assert player.credits == 1000
    assert player.minerals == 500
    assert player.energy == 250
    assert player.skybucks == 10
    assert player.experience == 100
    assert player.tutorial_completed is False
    assert player.tutorial_state == ""
    assert isinstance(player.last_login, datetime)
    assert player.row_index == 2

# Test Player to_dict method
@pytest.mark.asyncio
async def test_player_to_dict():
    test_date = datetime(2023, 1, 1, 12, 0, 0)
    player = Player(
        player_id=123456789,
        display_name="TestCommander",
        credits=1000,
        minerals=500,
        energy=250,
        skybucks=10,
        experience=100,
        tutorial_completed=True,
        tutorial_state="completed",
        last_login=test_date,
        row_index=2
    )
    
    player_dict = await player.to_dict()
    
    assert player_dict["player_id"] == "123456789"
    assert player_dict["display_name"] == "TestCommander"
    assert player_dict["credits"] == 1000
    assert player_dict["minerals"] == 500
    assert player_dict["energy"] == 250
    assert player_dict["skybucks"] == 10
    assert player_dict["experience"] == 100
    assert player_dict["tutorial_completed"] == "TRUE"
    assert player_dict["tutorial_state"] == "completed"
    assert player_dict["last_login"] == "2023-01-01 12:00:00"

# Test Player from_row method
@pytest.mark.asyncio
async def test_player_from_row():
    row = ["123456789", "TestPlayer", "1000", "500", "250", "10", "100", "TRUE", "completed", "2023-01-01 12:00:00"]
    row_index = 2
    
    player = await Player.from_row(row, row_index)
    
    assert player.player_id == 123456789
    assert player.display_name == "TestPlayer"
    assert player.credits == 1000
    assert player.minerals == 500
    assert player.energy == 250
    assert player.skybucks == 10
    assert player.experience == 100
    assert player.tutorial_completed is True
    assert player.tutorial_state == "completed"
    assert player.last_login.year == 2023
    assert player.last_login.month == 1
    assert player.last_login.day == 1
    assert player.row_index == 2

# Test get_player function
@pytest.mark.asyncio
async def test_get_player():
    # Mock get_sheet and find_row_by_col_value
    with patch("modules.player.get_sheet") as mock_get_sheet, \
         patch("modules.player.find_row_by_col_value") as mock_find_row:
        
        mock_get_sheet.return_value = asyncio.Future()
        mock_get_sheet.return_value.set_result(mock_sheet)
        
        mock_find_row.return_value = asyncio.Future()
        mock_find_row.return_value.set_result((2, mock_sheet["values"][1]))
        
        player = await get_player(123456789)
        
        assert player.player_id == 123456789
        assert player.display_name == "TestPlayer"
        assert player.credits == 1000
        assert player.minerals == 500
        assert player.energy == 250
        assert player.skybucks == 10
        assert player.experience == 100
        assert player.tutorial_completed is False

# Test create_player function
@pytest.mark.asyncio
async def test_create_player():
    # Mock the save method
    with patch.object(Player, "save") as mock_save:
        mock_save.return_value = asyncio.Future()
        mock_save.return_value.set_result(None)
        
        player = await create_player(123456789, "NewPlayer")
        
        assert player.player_id == 123456789
        assert player.display_name == "NewPlayer"
        assert player.credits == 500  # Default value
        assert player.minerals == 200  # Default value
        assert player.energy == 100  # Default value
        assert player.skybucks == 0  # Default value
        assert player.experience == 0  # Default value
        assert player.tutorial_completed is False
        assert mock_save.called

# Test player_exists function
@pytest.mark.asyncio
async def test_player_exists():
    # Mock get_sheet and find_row_by_col_value
    with patch("modules.player.get_sheet") as mock_get_sheet, \
         patch("modules.player.find_row_by_col_value") as mock_find_row:
        
        mock_get_sheet.return_value = asyncio.Future()
        mock_get_sheet.return_value.set_result(mock_sheet)
        
        # Test player exists
        mock_find_row.return_value = asyncio.Future()
        mock_find_row.return_value.set_result((2, mock_sheet["values"][1]))
        
        exists = await player_exists(123456789)
        assert exists is True
        
        # Test player doesn't exist
        mock_find_row.return_value = asyncio.Future()
        mock_find_row.return_value.set_result((None, None))
        
        exists = await player_exists(987654321)
        assert exists is False
