"""
Command handlers for the SkyHustle Telegram bot.
"""
import json
import logging
logging.basicConfig(level=logging.INFO)
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from modules.player import Player, get_player, create_player, player_exists
from modules.building import (
    get_building_info,
    get_available_buildings,
    queue_building,
    get_build_queue,
)
from modules.unit import (
    get_unit_info,
    train_units,
    get_available_units,
    get_training_queue,
)
from modules.research import (
    get_research_info,
    research_technology,
    get_available_technologies,
)
from modules.battle import (
    attack_player,
    scan_for_targets,
)
from modules.alliance import (
    create_alliance,
    join_alliance,
    leave_alliance,
    invite_to_alliance,
    get_alliance_info,
    disband_alliance,
)
from utils.formatting import (
    format_status_message,
    format_building_info,
    format_unit_info,
    format_research_info,
    format_battle_result,
    format_scan_results,
    format_alliance_info,
)
from utils.validation import (
    validate_build_command,
    validate_train_command,
    validate_research_command,
    validate_attack_command,
    validate_alliance_command,
    validate_setname_command,
)
from utils.helpers import (
    create_inline_keyboard,
    encode_callback_data,
    get_command_args,
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command - entry point for new players.
    Shows welcome message and tutorial options.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username or "Commander"
    
    # Check if player exists
    if await player_exists(user_id):
        player = await get_player(user_id)
        await update.message.reply_text(
            f"Welcome back, {player.display_name}! Use /status to see your base or /help for commands."
        )
        return
    
    # New player onboarding
    await update.message.reply_text(
        f"Welcome to SkyHustle, {username}! 🚀\n\n"
        "In this strategy game, you'll build futuristic aerial bases, train armies, "
        "research technologies, and engage in epic battles!\n\n"
        "Would you like to begin the tutorial?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Begin Tutorial", callback_data=encode_callback_data("tutorial", {"action": "start"})),
                InlineKeyboardButton("Skip Tutorial", callback_data=encode_callback_data("tutorial", {"action": "skip"}))
            ]
        ])
    )
    
    # Create a new player
    await create_player(user_id, username)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command - show available commands and brief explanations.
    """
    # Log that we received the help command
    logging.info(f"Received /help command from user: {update.effective_user.id} ({update.effective_user.username})")
    help_text = (
        "*SkyHustle Command Reference*\n\n"
        "📊 *Base Management*\n"
        "/status - Show your base stats and resources\n"
        "/build <structure> \[qty\] - Build structures\n"
        "/train <unit> \[count\] - Train units\n"
        "/research \[tech\_id\] - Research new technologies\n"
        "/defensive - Manage your defensive structures\n\n"
        
        "⚔️ *Combat*\n"
        "/scan - Find potential targets\n"
        "/attack <player\_id> - Attack another player\n"
        "/unit\_evolution - Upgrade your units\n\n"
        
        "🛡️ *Alliance*\n"
        "/alliance <subcmd> - Alliance management\n"
        "/war <subcmd> - Alliance war commands\n\n"
        
        "🏆 *Progression*\n"
        "/daily - Claim daily rewards\n"
        "/achievements - Track your achievements\n"
        "/events - View current game events\n"
        "/leaderboard \[scope\] - View rankings\n\n"
        
        "⚙️ *Settings*\n"
        "/setname <name> - Set your display name\n"
        "/notifications - Manage notifications\n"
        "/tutorial - Restart tutorial\n"
        "/weather - View ambient weather messages\n\n"
        
        "Use /help <command> for detailed info on a specific command."
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /status command - show player's current resources, queues, and stats.
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Get player data
    player = await get_player(user_id)
    build_queue = await get_build_queue(user_id)
    training_queue = await get_training_queue(user_id)
    
    # Format status message
    status_message = await format_status_message(player, build_queue, training_queue)
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("🏗️ Build", callback_data=encode_callback_data("action", {"type": "build"})),
            InlineKeyboardButton("⚔️ Train", callback_data=encode_callback_data("action", {"type": "train"})),
            InlineKeyboardButton("🔬 Research", callback_data=encode_callback_data("action", {"type": "research"}))
        ]
    ]
    
    await update.message.reply_text(
        status_message,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /build command - queue buildings for construction.
    Usage: /build <structure_id> [quantity]
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        # No arguments provided, show available buildings
        available_buildings = await get_available_buildings(user_id)
        
        # Create buttons for available buildings
        keyboard = []
        for i in range(0, len(available_buildings), 2):
            row = []
            for j in range(2):
                if i + j < len(available_buildings):
                    building = available_buildings[i + j]
                    callback_data = encode_callback_data(
                        "build", {"id": building["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{building['name']} ({building['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        await update.message.reply_text(
            "🏗️ *Available Buildings:*\n"
            "Select a building to construct:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Parse building ID and quantity
    building_id = args[0]
    quantity = 1
    if len(args) > 1:
        try:
            quantity = int(args[1])
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid quantity. Please use a positive number."
            )
            return
    
    # Validate build command
    validation_result = await validate_build_command(user_id, building_id, quantity)
    if not validation_result["valid"]:
        await update.message.reply_text(
            f"❌ {validation_result['message']}"
        )
        return
    
    # Queue the building
    result = await queue_building(user_id, building_id, quantity)
    if result["success"]:
        await update.message.reply_text(
            f"✅ {result['message']}"
        )
    else:
        await update.message.reply_text(
            f"❌ {result['message']}"
        )

async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /train command - queue units for training.
    Usage: /train <unit_type> [count]
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        # No arguments provided, show available units
        available_units = await get_available_units(user_id)
        
        # Create buttons for available units
        keyboard = []
        for i in range(0, len(available_units), 2):
            row = []
            for j in range(2):
                if i + j < len(available_units):
                    unit = available_units[i + j]
                    callback_data = encode_callback_data(
                        "train", {"id": unit["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{unit['name']} ({unit['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        await update.message.reply_text(
            "⚔️ *Available Units:*\n"
            "Select a unit to train:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Parse unit ID and count
    unit_id = args[0]
    count = 1
    if len(args) > 1:
        try:
            count = int(args[1])
            if count <= 0:
                raise ValueError("Count must be positive")
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid count. Please use a positive number."
            )
            return
    
    # Validate train command
    validation_result = await validate_train_command(user_id, unit_id, count)
    if not validation_result["valid"]:
        await update.message.reply_text(
            f"❌ {validation_result['message']}"
        )
        return
    
    # Train the units
    result = await train_units(user_id, unit_id, count)
    if result["success"]:
        await update.message.reply_text(
            f"✅ {result['message']}"
        )
    else:
        await update.message.reply_text(
            f"❌ {result['message']}"
        )

async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /research command - research new technologies.
    Usage: /research [tech_id]
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        # No arguments provided, show available technologies
        available_techs = await get_available_technologies(user_id)
        
        # Create buttons for available technologies
        keyboard = []
        for i in range(0, len(available_techs), 2):
            row = []
            for j in range(2):
                if i + j < len(available_techs):
                    tech = available_techs[i + j]
                    callback_data = encode_callback_data(
                        "research", {"id": tech["id"]}
                    )
                    row.append(InlineKeyboardButton(
                        f"{tech['name']} ({tech['cost']} 💰)",
                        callback_data=callback_data
                    ))
            keyboard.append(row)
        
        await update.message.reply_text(
            "🔬 *Available Technologies:*\n"
            "Select a technology to research:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Parse tech ID
    tech_id = args[0]
    
    # Validate research command
    validation_result = await validate_research_command(user_id, tech_id)
    if not validation_result["valid"]:
        await update.message.reply_text(
            f"❌ {validation_result['message']}"
        )
        return
    
    # Research the technology
    result = await research_technology(user_id, tech_id)
    if result["success"]:
        await update.message.reply_text(
            f"✅ {result['message']}"
        )
    else:
        await update.message.reply_text(
            f"❌ {result['message']}"
        )

async def unit_evolution_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /unit_evolution command - upgrade units to more advanced versions.
    """
    await update.message.reply_text(
        "🔄 *Unit Evolution*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to evolve your units into more powerful versions!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def defensive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /defensive command - manage defensive structures.
    """
    await update.message.reply_text(
        "🛡️ *Defense Management*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to configure your defensive structures!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /attack command - attack another player.
    Usage: /attack <player_id>
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        await update.message.reply_text(
            "❌ Missing target player ID. Usage: /attack <player_id>\n"
            "Use /scan to find targets."
        )
        return
    
    # Parse target player ID
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid player ID. Use /scan to find valid targets."
        )
        return
    
    # Validate attack command
    validation_result = await validate_attack_command(user_id, target_id)
    if not validation_result["valid"]:
        await update.message.reply_text(
            f"❌ {validation_result['message']}"
        )
        return
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm Attack",
                callback_data=encode_callback_data("attack_confirm", {"target": target_id})
            ),
            InlineKeyboardButton(
                "Cancel",
                callback_data=encode_callback_data("attack_cancel", {})
            )
        ]
    ]
    
    await update.message.reply_text(
        f"⚠️ Are you sure you want to attack player {target_id}?\n"
        "This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /scan command - find potential targets to attack.
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Scan for targets
    targets = await scan_for_targets(user_id)
    
    if not targets:
        await update.message.reply_text(
            "ℹ️ No suitable targets found at this time. Try again later."
        )
        return
    
    # Format scan results
    scan_message = await format_scan_results(targets)
    
    # Create buttons for targets
    keyboard = []
    for target in targets:
        callback_data = encode_callback_data(
            "attack_target", {"id": target["id"]}
        )
        keyboard.append([InlineKeyboardButton(
            f"Attack {target['name']} (Power: {target['power']})",
            callback_data=callback_data
        )])
    
    await update.message.reply_text(
        scan_message,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def alliance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /alliance command - alliance management.
    Usage: /alliance <subcmd> [args]
    Subcommands: create, join, leave, invite, info, disband
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        # Show alliance menu
        keyboard = [
            [
                InlineKeyboardButton("Create Alliance", callback_data=encode_callback_data("alliance", {"action": "create_prompt"})),
                InlineKeyboardButton("Join Alliance", callback_data=encode_callback_data("alliance", {"action": "join_prompt"}))
            ],
            [
                InlineKeyboardButton("Alliance Info", callback_data=encode_callback_data("alliance", {"action": "info"})),
                InlineKeyboardButton("Leave Alliance", callback_data=encode_callback_data("alliance", {"action": "leave_confirm"}))
            ],
            [
                InlineKeyboardButton("Invite Player", callback_data=encode_callback_data("alliance", {"action": "invite_prompt"})),
                InlineKeyboardButton("Disband Alliance", callback_data=encode_callback_data("alliance", {"action": "disband_confirm"}))
            ]
        ]
        
        await update.message.reply_text(
            "🛡️ *Alliance Management*\n"
            "Select an action:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Handle subcommands
    subcmd = args[0].lower()
    
    if subcmd == "create" and len(args) > 1:
        # Create alliance
        alliance_name = args[1]
        validation_result = await validate_alliance_command(user_id, "create", alliance_name)
        if not validation_result["valid"]:
            await update.message.reply_text(f"❌ {validation_result['message']}")
            return
        
        result = await create_alliance(user_id, alliance_name)
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    elif subcmd == "join" and len(args) > 1:
        # Join alliance
        join_code = args[1]
        validation_result = await validate_alliance_command(user_id, "join", join_code)
        if not validation_result["valid"]:
            await update.message.reply_text(f"❌ {validation_result['message']}")
            return
        
        result = await join_alliance(user_id, join_code)
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    elif subcmd == "leave":
        # Leave alliance
        validation_result = await validate_alliance_command(user_id, "leave")
        if not validation_result["valid"]:
            await update.message.reply_text(f"❌ {validation_result['message']}")
            return
        
        result = await leave_alliance(user_id)
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    elif subcmd == "invite" and len(args) > 1:
        # Invite player
        target_username = args[1].lstrip('@')
        validation_result = await validate_alliance_command(user_id, "invite", target_username)
        if not validation_result["valid"]:
            await update.message.reply_text(f"❌ {validation_result['message']}")
            return
        
        result = await invite_to_alliance(user_id, target_username)
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    elif subcmd == "info":
        # Alliance info
        alliance_info = await get_alliance_info(user_id)
        if alliance_info:
            formatted_info = await format_alliance_info(alliance_info)
            await update.message.reply_text(formatted_info, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("❌ You are not in an alliance.")
    
    elif subcmd == "disband":
        # Disband alliance
        validation_result = await validate_alliance_command(user_id, "disband")
        if not validation_result["valid"]:
            await update.message.reply_text(f"❌ {validation_result['message']}")
            return
        
        result = await disband_alliance(user_id)
        if result["success"]:
            await update.message.reply_text(f"✅ {result['message']}")
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    else:
        # Invalid subcommand
        await update.message.reply_text(
            "❌ Invalid alliance subcommand. Available subcommands:\n"
            "/alliance create <name>\n"
            "/alliance join <code>\n"
            "/alliance leave\n"
            "/alliance invite @username\n"
            "/alliance info\n"
            "/alliance disband"
        )

async def war_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /war command - alliance war management.
    Usage: /war <subcmd> [args]
    Subcommands: create, join, deploy, status, results
    """
    await update.message.reply_text(
        "⚔️ *Alliance War*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to engage in epic alliance vs alliance battles!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /leaderboard command - show player rankings.
    Usage: /leaderboard [scope]
    Scopes: global, faction, alliance
    """
    await update.message.reply_text(
        "🏆 *Leaderboards*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to see player rankings globally and within alliances!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /daily command - claim daily rewards.
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Get player
    player = await get_player(user_id)
    
    # This would normally check if the player has already claimed their daily reward
    # For now, we'll always give the reward
    
    # Update player resources (simple reward for demonstration)
    rewards = {
        "credits": 100,
        "minerals": 50,
        "energy": 25
    }
    
    player.credits += rewards["credits"]
    player.minerals += rewards["minerals"]
    player.energy += rewards["energy"]
    
    # Save player
    await player.save()
    
    await update.message.reply_text(
        "✅ *Daily Reward Claimed!*\n\n"
        f"You received:\n"
        f"💰 {rewards['credits']} Credits\n"
        f"🪨 {rewards['minerals']} Minerals\n"
        f"⚡ {rewards['energy']} Energy\n\n"
        "Come back tomorrow for more rewards!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /achievements command - show and claim achievements.
    """
    await update.message.reply_text(
        "🏅 *Achievements*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to track your progress and claim rewards!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /events command - show active events.
    """
    await update.message.reply_text(
        "🎉 *Game Events*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to participate in special limited-time events!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /notifications command - manage notification settings.
    Usage: /notifications <on/off> [event_types]
    """
    await update.message.reply_text(
        "🔔 *Notifications*\n\n"
        "This feature is coming soon.\n"
        "You'll be able to customize your notification preferences!",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /tutorial command - restart or skip tutorial.
    Usage: /tutorial <start/skip>
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    action = "start"
    if args:
        action = args[0].lower()
    
    if action == "start":
        # Start tutorial
        await update.message.reply_text(
            "🎮 *Tutorial Starting*\n\n"
            "Welcome to SkyHustle! Let me guide you through the basics.\n\n"
            "First, let's check your base status. Type /status to see your resources and base information.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Here we would set the player's tutorial state
        player = await get_player(user_id)
        player.tutorial_state = "status"
        await player.save()
        
    elif action == "skip":
        # Skip tutorial
        await update.message.reply_text(
            "✅ *Tutorial Skipped*\n\n"
            "You've chosen to skip the tutorial. You can always restart it with /tutorial start.\n\n"
            "Use /status to check your base and /help to see available commands.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Mark tutorial as completed
        player = await get_player(user_id)
        player.tutorial_completed = True
        await player.save()
        
    else:
        await update.message.reply_text(
            "❌ Invalid tutorial command. Use /tutorial start or /tutorial skip."
        )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /weather command - show ambient weather messages.
    """
    import random
    
    weather_messages = [
        "☀️ Clear skies above your aerial base. Perfect for reconnaissance missions!",
        "🌤️ Scattered clouds at high altitude. Visibility remains optimal for operations.",
        "⛈️ Electrical storm approaching! Defensive systems receiving 15% power boost.",
        "🌧️ Light rain showers. Resource collectors operating at 105% efficiency.",
        "🌪️ Warning: Turbulence detected in sector 7. Consider relocating sensitive equipment.",
        "🌫️ Dense fog surrounding lower levels. Stealth units gaining 10% evasion bonus.",
        "🌅 Sunrise detected. Solar arrays charging at maximum capacity.",
        "🌙 Nightfall approaching. Stealth operations receiving 8% efficiency bonus."
    ]
    
    weather = random.choice(weather_messages)
    
    await update.message.reply_text(
        f"*Current Weather:*\n{weather}",
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /save command - force save game state to Google Sheets.
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Get player and save
    player = await get_player(user_id)
    await player.save()
    
    await update.message.reply_text(
        "✅ Game state saved successfully!"
    )

async def load_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /load command - force load game state from Google Sheets.
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Force load player data
    player = await get_player(user_id, force_reload=True)
    
    await update.message.reply_text(
        "✅ Game state loaded successfully!"
    )

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /setname command - set player display name.
    Usage: /setname <name>
    """
    user_id = update.effective_user.id
    
    # Validate player exists
    if not await player_exists(user_id):
        await update.message.reply_text(
            "❌ You don't have a base yet. Use /start to create one!"
        )
        return
    
    # Parse arguments
    args = get_command_args(context)
    if not args:
        await update.message.reply_text(
            "❌ Missing name argument. Usage: /setname <name>"
        )
        return
    
    # Parse name
    name = ' '.join(args)
    
    # Validate name
    validation_result = await validate_setname_command(user_id, name)
    if not validation_result["valid"]:
        await update.message.reply_text(
            f"❌ {validation_result['message']}"
        )
        return
    
    # Update player name
    player = await get_player(user_id)
    player.display_name = name
    await player.save()
    
    await update.message.reply_text(
        f"✅ Your display name has been set to: {name}"
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /admin command - admin-only commands.
    Only for development and testing.
    """
    # This would normally check if the user is an admin
    # For now, we'll just return a message
    await update.message.reply_text(
        "🔒 Admin commands are not available in this version."
    )
