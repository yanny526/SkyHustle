"""
Tests for command handlers in the SkyHustle Telegram bot.
"""
import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

from telegram import Update, Chat, Message, User
from telegram.ext import ContextTypes

from handlers.command_handlers import (
    start_command,
    status_command,
    build_command,
    train_command,
    research_command,
    help_command
)

# Mock player data
mock_player_data = {
    "player_id": "123456789",
    "display_name": "TestCommander",
    "credits": 1000,
    "minerals": 500,
    "energy": 250,
    "skybucks": 10,
    "experience": 100,
    "tutorial_completed": "FALSE",
    "tutorial_state": "",
    "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Mock building data
mock_building_data = {
    "command_center": {
        "name": "Command Center",
        "description": "Central command facility for your aerial base",
        "cost": 500,
        "minerals": 250,
        "energy": 100,
        "build_time": 300,
        "requirements": [],
        "provides": {"credits_per_hour": 50}
    }
}

# Create mock update and context for testing
@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat_id = 123456789
    update.message.reply_text = MagicMock()
    
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    
    return context

# Mock player_exists and get_player functions
@pytest.fixture
def mock_player_functions():
    with patch("handlers.command_handlers.player_exists") as mock_exists, \
         patch("handlers.command_handlers.get_player") as mock_get, \
         patch("handlers.command_handlers.create_player") as mock_create:
        
        # Configure mock behavior
        mock_exists.return_value = asyncio.Future()
        mock_exists.return_value.set_result(True)
        
        mock_player = MagicMock()
        for key, value in mock_player_data.items():
            setattr(mock_player, key, value)
        mock_player.save = MagicMock(return_value=asyncio.Future())
        mock_player.save.return_value.set_result(None)
        
        mock_get.return_value = asyncio.Future()
        mock_get.return_value.set_result(mock_player)
        
        mock_create.return_value = asyncio.Future()
        mock_create.return_value.set_result(mock_player)
        
        yield mock_exists, mock_get, mock_create

# Test start_command
@pytest.mark.asyncio
async def test_start_command_new_player(mock_update, mock_context, mock_player_functions):
    mock_exists, mock_get, mock_create = mock_player_functions
    mock_exists.return_value = asyncio.Future()
    mock_exists.return_value.set_result(False)
    
    await start_command(mock_update, mock_context)
    
    # Verify correct calls were made
    assert mock_exists.called
    assert mock_create.called
    assert mock_update.message.reply_text.called
    
    # Check welcome message was sent
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Welcome to SkyHustle" in call_args

# Test start_command with existing player
@pytest.mark.asyncio
async def test_start_command_existing_player(mock_update, mock_context, mock_player_functions):
    mock_exists, mock_get, mock_create = mock_player_functions
    
    await start_command(mock_update, mock_context)
    
    # Verify correct calls were made
    assert mock_exists.called
    assert mock_get.called
    assert not mock_create.called
    assert mock_update.message.reply_text.called
    
    # Check welcome back message was sent
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Welcome back" in call_args

# Test help_command
@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    await help_command(mock_update, mock_context)
    
    # Verify help message was sent
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "SkyHustle Command Reference" in call_args

# Test status_command
@pytest.mark.asyncio
async def test_status_command(mock_update, mock_context, mock_player_functions):
    # Also mock get_build_queue and get_training_queue
    with patch("handlers.command_handlers.get_build_queue") as mock_build_queue, \
         patch("handlers.command_handlers.get_training_queue") as mock_training_queue:
        
        mock_build_queue.return_value = asyncio.Future()
        mock_build_queue.return_value.set_result([])
        
        mock_training_queue.return_value = asyncio.Future()
        mock_training_queue.return_value.set_result([])
        
        await status_command(mock_update, mock_context)
        
        # Verify correct calls were made
        assert mock_update.message.reply_text.called
        
        # Check status info was sent
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Base Status" in call_args
        assert "Credits" in call_args
        assert "Minerals" in call_args
        assert "Energy" in call_args

# Test build_command with no args (should show available buildings)
@pytest.mark.asyncio
async def test_build_command_no_args(mock_update, mock_context, mock_player_functions):
    # Mock get_available_buildings
    with patch("handlers.command_handlers.get_available_buildings") as mock_available:
        mock_available.return_value = asyncio.Future()
        mock_available.return_value.set_result([
            {
                "id": "command_center",
                "name": "Command Center",
                "cost": 500,
                "already_owned": False
            }
        ])
        
        await build_command(mock_update, mock_context)
        
        # Verify available buildings were shown
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available Buildings" in call_args

# Test train_command with no args (should show available units)
@pytest.mark.asyncio
async def test_train_command_no_args(mock_update, mock_context, mock_player_functions):
    # Mock get_available_units
    with patch("handlers.command_handlers.get_available_units") as mock_available:
        mock_available.return_value = asyncio.Future()
        mock_available.return_value.set_result([
            {
                "id": "drone",
                "name": "Reconnaissance Drone",
                "cost": 50
            }
        ])
        
        await train_command(mock_update, mock_context)
        
        # Verify available units were shown
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available Units" in call_args

# Test research_command with no args (should show available technologies)
@pytest.mark.asyncio
async def test_research_command_no_args(mock_update, mock_context, mock_player_functions):
    # Mock get_available_technologies
    with patch("handlers.command_handlers.get_available_technologies") as mock_available:
        mock_available.return_value = asyncio.Future()
        mock_available.return_value.set_result([
            {
                "id": "advanced_materials",
                "name": "Advanced Materials",
                "cost": 300
            }
        ])
        
        await research_command(mock_update, mock_context)
        
        # Verify available technologies were shown
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Available Technologies" in call_args
