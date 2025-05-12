"""
Test script for SkyHustle Telegram bot commands.
This script simulates sending commands to the bot and shows the expected responses.
"""
import asyncio
import logging
from datetime import datetime
import json

# Create mock telegram classes for testing
class User:
    def __init__(self, id, is_bot, first_name, username=None):
        self.id = id
        self.is_bot = is_bot
        self.first_name = first_name
        self.username = username or first_name.lower()
        
class Chat:
    def __init__(self, id, type):
        self.id = id
        self.type = type

class Message:
    def __init__(self, message_id, date, chat, from_user, text):
        self.message_id = message_id
        self.date = date
        self.chat = chat
        self.from_user = from_user
        self.text = text
        self.reply_text_messages = []
        
    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        """Mock reply_text method that prints the message"""
        self.reply_text_messages.append(text)
        print(f"\nBOT RESPONSE:\n{text}")
        if reply_markup:
            if hasattr(reply_markup, 'inline_keyboard'):
                print("\nINLINE KEYBOARD OPTIONS:")
                for row in reply_markup.inline_keyboard:
                    for button in row:
                        print(f"- {button.text} (callback: {button.callback_data})")
    
    async def reply_markdown_v2(self, text, reply_markup=None):
        """Mock reply_markdown_v2 method that prints the message"""
        await self.reply_text(text, reply_markup=reply_markup, parse_mode="MarkdownV2")

class Update:
    def __init__(self, update_id, message=None, callback_query=None):
        self.update_id = update_id
        self.message = message
        self.callback_query = callback_query
        self.effective_user = message.from_user if message else None

class CallbackQuery:
    def __init__(self, id, from_user, message, data):
        self.id = id
        self.from_user = from_user
        self.message = message
        self.data = data
        
    async def answer(self):
        """Mock answer method"""
        pass
        
    async def edit_message_text(self, text):
        """Mock edit_message_text method that prints the message"""
        print(f"\nBOT EDITED MESSAGE:\n{text}")

class InlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url

class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard

class ContextTypes:
    DEFAULT_TYPE = None

# Import command handlers
from handlers.base_handlers import (
    start, status, help_command, setname, daily, weather, events, 
    achievements, save, load, leaderboard, notifications
)
from handlers.building_handlers import build, defensive
from handlers.alliance_handlers import alliance, war
from handlers.combat_handlers import attack, scan, unit_evolution
from handlers.tutorial_handlers import tutorial

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MockContext:
    """Mock context for testing commands."""
    def __init__(self, args=None):
        self.args = args if args is not None else []
        self.bot_data = {}
        self.chat_data = {}
        self.user_data = {}

async def create_mock_update(user_id=123456789, username="test_user", chat_id=123456789, text="/command"):
    """Create a mock Update object for testing."""
    user = User(id=user_id, is_bot=False, first_name="Test", username=username)
    chat = Chat(id=chat_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=1, message=message)

async def test_command(handler_func, args=None, user_id=123456789, username="test_user"):
    """Test a command handler with mock objects."""
    command_name = handler_func.__name__
    
    # Create mock objects
    text = f"/{command_name}" + (f" {' '.join(args)}" if args else "")
    update = await create_mock_update(user_id=user_id, username=username, text=text)
    context = MockContext(args=args)
    
    print(f"\n{'='*50}")
    print(f"Testing command: {text}")
    print(f"{'='*50}")
    
    # Call the handler function
    try:
        await handler_func(update, context)
        print("Command executed successfully!")
    except Exception as e:
        print(f"Error executing command: {e}")

async def run_tests():
    """Run tests for all commands."""
    print("Starting SkyHustle bot command tests...\n")
    
    # Basic commands
    await test_command(start)
    await test_command(status)
    await test_command(help_command)
    await test_command(setname, args=["Commander Skywalker"])
    await test_command(daily)
    await test_command(weather)
    await test_command(events)
    await test_command(achievements)
    await test_command(save)
    await test_command(load)
    await test_command(leaderboard)
    await test_command(leaderboard, args=["alliance"])
    await test_command(notifications)
    
    # Building commands
    await test_command(build)
    await test_command(build, args=["command_center"])
    await test_command(defensive)
    
    # Alliance commands
    await test_command(alliance)
    await test_command(alliance, args=["create", "Sky Raiders"])
    await test_command(alliance, args=["join", "ABC123"])
    await test_command(war)
    
    # Combat commands
    await test_command(attack)
    await test_command(attack, args=["987654321"])
    await test_command(scan)
    await test_command(unit_evolution)
    
    # Tutorial command
    await test_command(tutorial)
    
    print("\nCommand tests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())