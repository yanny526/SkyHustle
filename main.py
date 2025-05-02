"""
main.py:

This file contains the main application logic for the SkyHustle Telegram bot.
It handles user interactions, commands, and game mechanics.
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import BOT_TOKEN  # Import the bot token from config.py
from sheets_api import (
    read_sheet,
    write_to_sheet,
    append_to_sheet,
    create_sheet,
)  # Import the Google Sheets API functions
from game_logic import (
    initialize_player,
    get_player_resources,
    update_player_resources,
    get_resource_production,
    calculate_attack_damage,
    apply_attack_results,
    get_player_defense,
    calculate_travel_time,
    send_resources,
    get_shop_items,
    buy_shop_item,
    create_npc,
    get_npc_data,
    update_npc_data,
    npc_attack,
    distribute_spoils
)  # Import game logic functions
from utils import (
    validate_user_input,
    format_number,
    extract_number,
    is_valid_coordinates,
    sheet_exists
)  # Import utility functions
from constants import (
    START_COMMAND_DESCRIPTION,
    RESOURCES_COMMAND_DESCRIPTION,
    ATTACK_COMMAND_DESCRIPTION,
    DEFENSE_COMMAND_DESCRIPTION,
    SHOP_COMMAND_DESCRIPTION,
    HELP_COMMAND_DESCRIPTION,
    RESOURCE_NAMES,
    BUILDING_NAMES,
    UNIT_TYPES,
    NPC_STARTING_ROW,
    NPC_SHEET_NAME,
    PLAYER_SHEET_NAME
) # Import constants

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all DEBUG logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def send_message_with_retry(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, retries=3) -> None:
    """Sends a message to the user with retry logic."""
    for attempt in range(retries):
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return  # If successful, exit the function
        except Exception as e:
            logger.warning(f"Failed to send message (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:  # Don't wait after the last attempt
                # You might want to add a delay here, e.g., time.sleep(2)
                pass
    logger.error(f"Failed to send message after {retries} attempts.")
    # Consider raising an exception here if the message is critical

def extract_coordinates(text: str) -> tuple[int, int] or None:
    """
    Extracts coordinates from a text string.  Handles both comma-separated
    and space-separated formats.  Also handles negative numbers.

    Args:
        text: The text string to extract coordinates from.

    Returns:
        A tuple of (x, y) coordinates, or None if no valid coordinates are found.
    """
    import re

    # Use a regular expression to find two integers, possibly separated by comma or space
    match = re.search(r"(-?\d+)[, ]+(-?\d+)", text)
    if match:
        try:
            x = int(match.group(1))
            y = int(match.group(2))
            return x, y
        except ValueError:
            return None
    else:
        return None

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and initializes the player in the sheet."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    if not username:
        username = "Unknown"  # Handle users without usernames
    # Initialize the player in the Google Sheet
    if initialize_player(user_id, username):
        await send_message_with_retry(update, context,
            f"🚀 Welcome to SkyHustle, Commander {username}! Your empire awaits. Use /help to see available commands. ❓"
        )
    else:
        await send_message_with_retry(update, context,
            "👋 Welcome back, Commander! Your resources have been restored.  восстановились."
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with command descriptions."""
    help_text = (
        f"{START_COMMAND_DESCRIPTION} 🚀\n"
        f"{RESOURCES_COMMAND_DESCRIPTION} 💰\n"
        f"{ATTACK_COMMAND_DESCRIPTION} ⚔️\n"
        f"{DEFENSE_COMMAND_DESCRIPTION} 🛡️\n"
        f"{SHOP_COMMAND_DESCRIPTION} 🛒\n"
        f"{HELP_COMMAND_DESCRIPTION} ❓\n"
        "\n"
        "For more detailed information on a specific command, use /help <command>.\n"
        "Example: /help attack ⚔️"
    )
    await send_message_with_retry(update, context, help_text)

async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with the player's current resources and production."""
    user_id = update.effective_user.id
    resources = get_player_resources(user_id)
    if resources:
        production = get_resource_production(user_id)
        resource_text = "\n".join(
            f"{name}: {format_number(amount)} (+{format_number(production[name])}/hour) 💰"
            for name, amount in resources.items()
        )
        await send_message_with_retry(update, context, f"Your resources:\n{resource_text}")
    else:
        await send_message_with_retry(update, context, "You do not have any resources. Use /start to begin. 🚀")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the attack command.  Allows a player to attack another player
    or an NPC.  The target is specified by coordinates.
    """
    user_id = update.effective_user.id
    if not context.args:
        await send_message_with_retry(
            update, context, "Please specify the coordinates of the target to attack (e.g., /attack 1,5). 🎯"
        )
        return

    target_coordinates = extract_coordinates(context.args[0])
    if not target_coordinates:
        await send_message_with_retry(
            update, context, "Invalid coordinates. Please use the format x,y (e.g., 1,5 or 1 5). ❌"
        )
        return

    target_x, target_y = target_coordinates

    # Check if the target is a valid player or NPC
    target_player_id = None  # Initialize to None, will be set if it's a player
    target_is_npc = False

    # First, check if it's a player.
    all_player_data = read_sheet(PLAYER_SHEET_NAME, f"A2:B1000")  # Get Player IDs and Coordinates
    if all_player_data:
        for row in all_player_data:
            if len(row) >= 2:
                try:
                    player_id = int(row[0])
                    player_x, player_y = extract_coordinates(row[1])  # Use the helper function
                    if player_x == target_x and player_y == target_y:
                        target_player_id = player_id
                        break  # Found the player, exit the loop
                except ValueError:
                    logger.warning(f"Invalid player ID or coordinates in sheet: {row}")
                    continue  # Skip to the next row

    if target_player_id:
        if target_player_id == user_id:
            await send_message_with_retry(update, context, "You cannot attack yourself! 🤦")
            return
    else:
        # If not a player, check if it's an NPC.
        npc_data = get_npc_data(target_x, target_y)  #Simplified NPC check
        if npc_data:
            target_is_npc = True
        else:
            await send_message_with_retry(update, context, "Target coordinates do not correspond to a player or a NPC. 🤷")
            return

    # Get attacker and defender information.
    attacker_resources = get_player_resources(user_id)
    attacker_damage = calculate_attack_damage(user_id)
    attacker_name = update.effective_user.username if update.effective_user.username else f"Player {user_id}" #Gets Attacker Name
    if target_is_npc:
        defender_defense = get_npc_defense(target_x, target_y) #Gets NPC defense
        defender_name = f"NPC at {target_x},{target_y} 👾"
    else:
        defender_resources = get_player_resources(target_player_id)
        defender_defense = get_player_defense(target_player_id)
        defender_name = context.bot.get_chat(target_player_id).username if context.bot.get_chat(target_player_id).username else f"Player {target_player_id} ⚔️" #Gets Defender Name

    # Calculate travel time (simplified for now).
    travel_time = calculate_travel_time(0, 0, target_x, target_y)  # Example calculation
    await send_message_with_retry(
        update, context, f"Attack initiated! Your fleet will arrive at {defender_name} in {travel_time} seconds. 🚀"
    )

    # Apply attack results (simplified for now).
    if target_is_npc:
        spoils = apply_attack_results(attacker_resources, attacker_damage, defender_defense, target_is_npc)
        update_npc_data(target_x, target_y, spoils) # Update NPC Sheet
        distribute_spoils(user_id, spoils)
        await send_message_with_retry(update, context, f"You attacked {defender_name} and won! You gained {spoils} resources. 🏆")
    else:
        attack_result = apply_attack_results(attacker_resources, attacker_damage, defender_defense, target_is_npc) # returns a dictionary
        if attack_result["result"] == "attacker":
            #Attacker Wins
            await send_message_with_retry(update, context, f"You attacked {defender_name} and won! You gained {attack_result['spoils']} resources. 🏆")
            send_resources(user_id, target_player_id, attack_result['spoils'])
        elif attack_result["result"] == "defender":
            #Defender Wins
             await send_message_with_retry(update, context, f"You attacked {defender_name} and lost! 😢")
        else:
            #Tie
            await send_message_with_retry(update, context, f"You attacked {defender_name} and tied! 🤝")

async def defense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the player's defense rating."""
    user_id = update.effective_user.id
    defense = get_player_defense(user_id)  # Simplified defense retrieval
    await send_message_with_retry(
        update, context, f"Your total defense rating is: {format_number(defense)} 🛡️"
    )

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the items available in the shop or handles buying."""
    if not context.args:
        # Display shop items
        shop_items = get_shop_items()
        shop_text = "Available Shop Items:\n" + "\n".join(
            f"{name}: {item['description']} (Cost: {', '.join(f'{r} {c}' for r, c in item['cost'].items())}) 🛒"
            for name, item in shop_items.items()
        )
        await send_message_with_retry(update, context, shop_text)
    else:
        # Handle buying
        item_name = context.args[0].lower()
        quantity = 1  # Default quantity
        if len(context.args) > 1:
            try:
                quantity = int(context.args[1])
            except ValueError:
                await send_message_with_retry(update, context, "Invalid quantity. Please enter a number. 🔢")
                return
        user_id = update.effective_user.id
        result = buy_shop_item(user_id, item_name, quantity)
        if result:
            await send_message_with_retry(update, context, f"Successfully purchased {quantity} {item_name}(s). ✅")
        else:
            await send_message_with_retry(update, context, f"Failed to purchase {item_name}. Check your resources or item name. ❌")

# --- NPC Management ---
async def handle_npc_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles NPC commands (creation and attack)."""
    if not update.effective_user.id == int(os.environ.get("ADMIN_USER_ID")):  # Restrict to admin
        await send_message_with_retry(update, context, "You are not authorized to use this command. 🚫")
        return

    command = context.args[0].lower() if context.args else ""

    if command == "create":
        if len(context.args) < 5:
            await send_message_with_retry(
                update, context, "Usage: /npc create <x> <y> <level> <type>. Type is one of: base, trader, raider. 🛠️"
            )
            return
        try:
            x = int(context.args[1])
            y = int(context.args[2])
            level = int(context.args[3])
            npc_type = context.args[4].lower()
        except ValueError:
            await send_message_with_retry(update, context, "Invalid coordinates or level. Please enter numbers. 🔢")
            return

        if not is_valid_coordinates(x, y):
            await send_message_with_retry(update, context, "Invalid coordinates. X and Y must be between 1 and 100. ❌")
            return

        if npc_type not in ["base", "trader", "raider"]:
            await send_message_with_retry(update, context, "Invalid NPC type. Must be base, trader, or raider. ❓")
            return

        if level < 1 or level > 10:
            await send_message_with_retry(update, context, "Invalid level. Level must be between 1 and 10. 🔢")
            return

        if create_npc(x, y, level, npc_type):
            await send_message_with_retry(
                update, context, f"NPC {npc_type} (Level {level}) created at coordinates {x},{y}. ✅"
            )
        else:
            await send_message_with_retry(
                update, context, f"Failed to create NPC. There may already be an NPC or player at those coordinates. ❌"
            )

    elif command == "attack":
        if len(context.args) < 3:
            await send_message_with_retry(
                update, context, "Usage: /npc attack <x> <y>. Attacks the NPC at the specified coordinates. ⚔️"
            )
            return
        try:
            x = int(context.args[1])
            y = int(context.args[2])
        except ValueError:
            await send_message_with_retry(update, context, "Invalid coordinates. Please enter numbers. 🔢")
            return
        npc_data = get_npc_data(x,y)
        if npc_data:
            spoils = npc_attack(x, y)
            await send_message_with_retry(update, context, f"You attacked the NPC at {x},{y} and gained {spoils} resources. 🏆")
        else:
            await send_message_with_retry(update, context, "No NPC found at the specified coordinates. 🤷")

    else:
        await send_message_with_retry(
            update, context, "Invalid NPC command. Use /npc create or /npc attack. ❓"
        )

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles general messages. Currently, echoes the message."""
    # For now, we'll just echo the message back to the user
    # but you can add more sophisticated logic here, e.g.,
    # checking for specific keywords, or integrating with a dialog manager.
    await send_message_with_retry(update, context, f"You said: {update.message.text} 💬")

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the developer."""
    # Log the error
    logger.error(f"Exception while handling an update: {context.error} ⚠️")

    # Optionally, send a message to the developer (replace with your Telegram ID)
    dev_telegram_id = int(os.environ.get("DEVELOPER_TELEGRAM_ID"))
    if dev_telegram_id:
        error_message = f"An error occurred: {context.error}\nUpdate: {update} 🚨"
        await context.bot.send_message(chat_id=dev_telegram_id, text=error_message)

def main() -> None:
    """Main function that starts the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- Command Handlers ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("resources", resources))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("defense", defense))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("npc", handle_npc_commands)) #NPC Commands

    # --- Message Handler ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # --- Error Handler ---
    app.add_error_handler(error_handler)

    # --- Start the Bot ---
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
