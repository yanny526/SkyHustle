"""
Telegram Bot setup and configuration for SkyHustle.
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from handlers.command_handlers import (
    start_command,
    status_command,
    build_command,
    train_command,
    research_command,
    unit_evolution_command,
    defensive_command,
    attack_command,
    scan_command,
    alliance_command,
    war_command,
    leaderboard_command,
    daily_command,
    achievements_command,
    events_command,
    notifications_command,
    tutorial_command,
    weather_command,
    save_command,
    load_command,
    setname_command,
    help_command,
    admin_command,
)
from handlers.callback_handlers import handle_callback_query

async def error_handler(update_or_error: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors occurring in the dispatcher."""
    logging.error(f"Error occurred: {context.error}", exc_info=context.error)
    
    # Try to respond to user if this is an update object
    try:
        if isinstance(update_or_error, Update) and update_or_error.effective_message:
            await update_or_error.effective_message.reply_text(
                "❌ An error occurred processing your request. Please try again later."
            )
    except Exception as e:
        logging.error(f"Error sending error message: {e}", exc_info=True)

async def setup_bot(bot_token: str) -> None:
    """
    Set up and run the Telegram bot with all handlers.
    
    Args:
        bot_token: Telegram Bot API token
    """
    # Create the application
    application = Application.builder().token(bot_token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("build", build_command))
    application.add_handler(CommandHandler("train", train_command))
    application.add_handler(CommandHandler("research", research_command))
    application.add_handler(CommandHandler("unit_evolution", unit_evolution_command))
    application.add_handler(CommandHandler("defensive", defensive_command))
    application.add_handler(CommandHandler("attack", attack_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("alliance", alliance_command))
    application.add_handler(CommandHandler("war", war_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("achievements", achievements_command))
    application.add_handler(CommandHandler("events", events_command))
    application.add_handler(CommandHandler("notifications", notifications_command))
    application.add_handler(CommandHandler("tutorial", tutorial_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("load", load_command))
    application.add_handler(CommandHandler("setname", setname_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # Register callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logging.info("Starting polling...")
    await application.initialize()
    
    # Start polling with updater
    if application.updater:
        # First, let's try to delete any existing webhook
        logging.info("Attempting to delete any existing webhook...")
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logging.info("Successfully deleted webhook (if it existed)")
        except Exception as e:
            logging.error(f"Error deleting webhook: {e}", exc_info=True)
        
        logging.info("Starting Telegram updater with polling...")
        # Print the bot information to verify we're using the correct bot
        try:
            bot_info = await application.bot.get_me()
            logging.info(f"Connected as bot: {bot_info.first_name} (@{bot_info.username}) with ID {bot_info.id}")
            
            # Verify the bot token by making a test request
            logging.info("Testing bot token with getUpdates request...")
            import aiohttp
            import json
            bot_token = application.bot.token
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/bot{bot_token}/getUpdates") as response:
                    text = await response.text()
                    logging.info(f"getUpdates response status: {response.status}")
                    logging.info(f"getUpdates response: {text[:200]}...")  # Log first 200 chars
            
            # Start polling with appropriate parameters for this version
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            logging.info("Polling started successfully. Bot is ready to receive commands.")
            
            # Keep the bot running indefinitely
            try:
                # Keep the bot running until receiving a stop signal
                import asyncio
                logging.info("Bot is now running indefinitely. Waiting for commands...")
                
                # Instead of sleeping for a long time, do shorter sleeps and periodic checks
                count = 0
                while True:
                    await asyncio.sleep(300)  # Sleep for 5 minutes between checks
                    count += 1
                    logging.info(f"Bot is still running... (check #{count})")
                    
                    # Every hour, do a health check
                    if count % 12 == 0:
                        try:
                            bot_info = await application.bot.get_me()
                            logging.info(f"Bot health check: Still connected as {bot_info.username}")
                        except Exception as e:
                            logging.error(f"Bot health check failed: {e}", exc_info=True)
            except (KeyboardInterrupt, SystemExit):
                # If we get a keyboard interrupt or system exit, stop the application
                logging.info("Received shutdown signal. Stopping bot...")
                await application.stop()
        except Exception as e:
            logging.critical(f"Critical error in bot setup: {e}", exc_info=True)
