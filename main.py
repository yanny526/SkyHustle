#   ===============================
#   SkyHustle: Main Entry Point
#   ===============================

import os
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

#   ===============================
#   Configuration - Environment Variables
#   ===============================

#   Ensure you have the BOT_TOKEN environment variable set.
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")


#   ===============================
#   Helper Functions
#   ===============================

def parse_command(text: str) -> tuple[str | None, list[str]]:
    """
    Parses a command from the given text.

    Args:
        text: The text message to parse.

    Returns:
        A tuple containing the command and its arguments.
        Returns (None, []) if no valid command is found.
    """
    if not text.startswith(","):
        return None, []  #   Not a command

    parts = text[1:].split()
    if not parts:
        return None, []  #   Empty command

    command = parts[0].lower()
    args = parts[1:]
    return command, args


#   ===============================
#   Command Handlers (Routing)
#   ===============================

async def handle_start_help_rules(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """Handles the start, help, and rules commands."""
    from handlers import start

    if command == "start":
        await start.start_command(update, context)
    elif command == "help":
        await start.help_command(update, context)
    elif command == "rules":
        await start.rules_command(update, context)

async def handle_player_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles player-related commands (name, status)."""
    from handlers import player

    if command == "name":
        await player.name_command(update, context, args)
    elif command == "status":
        await player.status_command(update, context)

async def handle_resource_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles resource-related commands (daily, mine, missions)."""
    from handlers import resource

    if command == "daily":
        await resource.daily_command(update, context)
    elif command == "mine":
        await resource.mine_command(update, context, args)
    elif command == "missions":
        await resource.missions_command(update, context)

async def handle_army_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles army-related commands (forge, use)."""
    from handlers import army

    if command == "forge":
        await army.forge_command(update, context, args)
    elif command == "use":
        await army.use_command(update, context, args)

async def handle_economy_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles economy-related commands (unlockbm, blackmarket, buy)."""
    from handlers import economy

    if command == "unlockbm":
        await economy.unlockbm_command(update, context)
    elif command == "blackmarket":
        await economy.blackmarket_command(update, context)
    elif command == "buy":
        await economy.buy_command(update, context, args)

async def handle_zone_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles zone-related commands (claim, map)."""
    from handlers import zones

    if command == "claim":
        await zones.claim_command(update, context, args)
    elif command == "map":
        await zones.map_command(update, context)

async def handle_combat_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list[str]):
    """Handles combat-related commands (attack)."""
    from handlers import combat

    if command == "attack":
        await combat.attack_command(update, context, args)

#   ===============================
#   Main Handler - Message Processing
#   ===============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The main message handler. Parses commands and dispatches them to the appropriate functions.
    """

    if not update.message:
        return  #   Ignore non-message updates

    text = update.message.text.strip()
    command, args = parse_command(text)

    try:
        if command:
            #   --- Command Routing Table ---
            command_handlers = {
                "start": handle_start_help_rules,
                "help": handle_start_help_rules,
                "rules": handle_start_help_rules,
                "name": handle_player_commands,
                "status": handle_player_commands,
                "daily": handle_resource_commands,
                "mine": handle_resource_commands,
                "missions": handle_resource_commands,
                "forge": handle_army_commands,
                "use": handle_army_commands,
                "unlockbm": handle_economy_commands,
                "blackmarket": handle_economy_commands,
                "buy": handle_economy_commands,
                "claim": handle_zone_commands,
                "map": handle_zone_commands,
                "attack": handle_combat_commands,
            }

            handler = command_handlers.get(command)
            if handler:
                await handler(update, context, command, args)
            else:
                await update.message.reply_text("❓ Unknown command. Type ,help for available actions.")
        else:
            await update.message.reply_text("💬 I received your message!")  #   Non-command message
    except Exception as e:
        print(f"⚠️ Error handling message: {e}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again.",
            parse_mode=ParseMode.MARKDOWN,
        )


#   ===============================
#   Error Handler
#   ===============================

async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE):
    """Handles errors that occur in the bot."""

    print(f"⚠️ Error: {context.error}")
    if update:
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again.", parse_mode=ParseMode.MARKDOWN
        )


#   ===============================
#   Application Setup
#   ===============================

def main():
    """Sets up and runs the Telegram bot."""

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    #   Message Handler (for commands and non-commands)
    app.add_handler(MessageHandler(filters.TEXT, handle_message))  #   Catch all text

    #   Error Handler
    app.add_error_handler(error_handler)

    #   Start the Bot
    print("🚀 Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
