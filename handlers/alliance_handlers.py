""",,,,,
Alliance related command handlers for the SkyHustle Telegram bot.
These handlers manage alliances and wars between alliances.
"""
import logging
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from modules.player import get_player
from modules.alliance import (
    create_alliance, join_alliance, leave_alliance, 
    get_alliance, get_alliance_by_player, invite_to_alliance
)
from utils.formatter import format_error, format_success, format_alliance_info

logger = logging.getLogger(__name__)

async def alliance(update: Update, context: CallbackContext):
    """Handler for /alliance command - manages alliance operations."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        await update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    # Check if subcommand was provided
    if not context.args or len(context.args) < 1:
        await show_alliance_status(update, context, player)
        return
    
    subcommand = context.args[0].lower()
    
    if subcommand == "create":
        # Check if name was provided
        if len(context.args) < 2:
            await update.message.reply_text(
                format_error("Please provide an alliance name. Example: /alliance create Sky Warriors")
            )
            return
        
        # Join arguments from index 1 onwards as the alliance name
        alliance_name = " ".join(context.args[1:])
        
        # Create the alliance
        result = create_alliance(user.id, alliance_name)
        
        if result['success']:
            await update.message.reply_text(
                format_success(f"Alliance '{alliance_name}' created successfully! Your join code is: {result['join_code']}")
            )
        else:
            await update.message.reply_text(
                format_error(result['message'])
            )
            
    elif subcommand == "join":
        # Check if join code was provided
        if len(context.args) < 2:
            await update.message.reply_text(
                format_error("Please provide a join code. Example: /alliance join ABC123")
            )
            return
        
        join_code = context.args[1]
        
        # Join the alliance
        result = join_alliance(user.id, join_code)
        
        if result['success']:
            await update.message.reply_text(
                format_success(f"You have joined the alliance '{result['alliance_name']}'!")
            )
        else:
            await update.message.reply_text(
                format_error(result['message'])
            )
            
    elif subcommand == "leave":
        # Leave the alliance
        result = leave_alliance(user.id)
        
        if result['success']:
            await update.message.reply_text(
                format_success("You have left your alliance.")
            )
        else:
            await update.message.reply_text(
                format_error(result['message'])
            )
            
    elif subcommand == "invite":
        # Check if username was provided
        if len(context.args) < 2:
            await update.message.reply_text(
                format_error("Please provide a Telegram username to invite. Example: /alliance invite @username")
            )
            return
        
        username = context.args[1]
        
        # Validate username format
        if not username.startswith("@"):
            await update.message.reply_text(
                format_error("Please provide a valid Telegram username starting with @")
            )
            return
        
        # Remove @ from username
        username = username[1:]
        
        # Send invitation
        # In a full implementation, this would look up the user ID from the username
        # and send them a direct message with an invitation
        await update.message.reply_text(
            format_success(f"Invitation to @{username} will be implemented in future updates.")
        )
            
    elif subcommand == "info":
        # Get alliance info
        alliance_data = get_alliance_by_player(user.id)
        
        if alliance_data:
            alliance_info = format_alliance_info(alliance_data)
            await update.message.reply_text(
                alliance_info,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text(
                format_error("You are not in an alliance.")
            )
            
    elif subcommand == "disband":
        # In a full implementation, this would check if the player is the alliance leader
        # and then disband the alliance
        await update.message.reply_text(
            format_error("Alliance disbanding will be implemented in future updates.")
        )
            
    else:
        await update.message.reply_text(
            format_error(f"Unknown subcommand: {subcommand}. Available subcommands: create, join, leave, invite, info, disband")
        )

async def show_alliance_status(update: Update, context: CallbackContext, player):
    """Shows current alliance status or alliance options."""
    alliance_data = get_alliance_by_player(player['player_id'])
    
    if alliance_data:
        # Player is in an alliance
        alliance_info = format_alliance_info(alliance_data)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "Alliance Info", 
                    callback_data=json.dumps({"cmd": "alliance", "subcmd": "info"})
                ),
                InlineKeyboardButton(
                    "Members", 
                    callback_data=json.dumps({"cmd": "alliance", "subcmd": "members"})
                )
            ],
            [
                InlineKeyboardButton(
                    "Leave Alliance", 
                    callback_data=json.dumps({"cmd": "alliance", "subcmd": "leave"})
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            alliance_info,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        # Player is not in an alliance
        message = (
            "*SkyHustle Alliances*\n\n"
            "You are not currently in an alliance\\.\n"
            "Join forces with other commanders to dominate the skies\\!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "Create Alliance", 
                    callback_data=json.dumps({"cmd": "alliance", "subcmd": "create"})
                ),
                InlineKeyboardButton(
                    "Join Alliance", 
                    callback_data=json.dumps({"cmd": "alliance", "subcmd": "join"})
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def war(update: Update, context: CallbackContext):
    """Handler for /war command - manages alliance wars."""
    user = update.effective_user
    player = get_player(user.id)
    
    if not player:
        await update.message.reply_text(
            format_error("You don't have a profile yet! Use /start to create one.")
        )
        return
    
    # Check if player is in an alliance
    alliance_data = get_alliance_by_player(user.id)
    
    if not alliance_data:
        await update.message.reply_text(
            format_error("You must be in an alliance to use war commands. Join or create an alliance first.")
        )
        return
    
    # Check if subcommand was provided
    if not context.args or len(context.args) < 1:
        await show_war_status(update, context, player, alliance_data)
        return
    
    subcommand = context.args[0].lower()
    
    if subcommand == "create":
        # In a full implementation, this would check if the player is the alliance leader
        # and then create a war with another alliance
        await update.message.reply_text(
            format_error("War creation will be implemented in future updates.")
        )
    elif subcommand == "join":
        await update.message.reply_text(
            format_error("War joining will be implemented in future updates.")
        )
    elif subcommand == "deploy":
        await update.message.reply_text(
            format_error("Unit deployment will be implemented in future updates.")
        )
    elif subcommand == "status":
        await update.message.reply_text(
            format_error("War status will be implemented in future updates.")
        )
    elif subcommand == "results":
        await update.message.reply_text(
            format_error("War results will be implemented in future updates.")
        )
    else:
        await update.message.reply_text(
            format_error(f"Unknown subcommand: {subcommand}. Available subcommands: create, join, deploy, status, results")
        )

async def show_war_status(update: Update, context: CallbackContext, player, alliance_data):
    """Shows current war status or war options."""
    # In a full implementation, this would check if the alliance is in an active war
    # and display war status or war creation options
    
    message = (
        "*Alliance War*\n\n"
        "Your alliance is not currently participating in any wars\\.\n"
        "Start a war to gain resources and prestige\\!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                "Create War", 
                callback_data=json.dumps({"cmd": "war", "subcmd": "create"})
            ),
            InlineKeyboardButton(
                "View Past Wars", 
                callback_data=json.dumps({"cmd": "war", "subcmd": "history"})
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )
